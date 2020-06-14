from flask import current_app as app

from detectors import dtm
from integrators import NotificationType
from integrators import im
from models import ResultTable
from models import ScanTable
from models import TaskTable
from models import db
from tasks import TaskHandlerBase
from tasks import TaskProgress


class StoppedTaskHandler(TaskHandlerBase):
    def __init__(self):
        super().__init__(TaskProgress.STOPPED.name)

    def add(self, task):
        app.logger.info("Try to enqueue into {}: task={}".format(self.progress, task))

        task["progress"] = TaskProgress.STOPPED.name
        task["ended_at"] = self.now

        # Update task progress
        TaskTable.update(task).where(TaskTable.uuid == task["uuid"]).execute()

        app.logger.info("Enqueued into {} successfully: task={}".format(self.progress, task["uuid"]))
        return

    def process(self, task):
        detector = dtm.load_detector(task["detection_module"], task["session"])
        results = detector.get_results()

        # Change keys for conforming to result table schema
        for result in results:
            result["scan_id"] = task["scan_id"]

        # Delete and insert scan results for keeping only the latest scan result
        with db.database.atomic():
            ResultTable.delete().where(ResultTable.scan_id == task["scan_id"]).execute()
            ResultTable.insert_many(results).execute()
            ScanTable.update({"ended_at": self.now}).where(ScanTable.task_uuid == task["uuid"]).execute()

        task["results"] = results
        im.send(NotificationType.RESULT, task)

        # Destroy the task without error
        self.finish(task)
