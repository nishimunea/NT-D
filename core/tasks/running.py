from datetime import timedelta

import pytz
from flask import current_app as app

from detectors import dtm
from models import ScanTable
from models import TaskTable
from models import db
from tasks import TaskHandlerBase
from tasks import TaskProgress
from tasks.stopped import StoppedTaskHandler


class RunningTaskHandler(TaskHandlerBase):
    def __init__(self):
        super().__init__(TaskProgress.RUNNING.name)

    def add(self, task):
        app.logger.info("Try to enqueue into {}: task={}".format(self.progress, task))
        detector = dtm.load_detector(task["detection_module"], task["session"])
        session = detector.run(task["target"], task["detection_mode"])

        task["session"] = session
        task["progress"] = TaskProgress.RUNNING.name
        task["started_at"] = self.now

        with db.database.atomic():
            # Update task progress
            TaskTable.update(task).where(TaskTable.uuid == task["uuid"]).execute()
            # Reflect started time to corresponding scan entry
            ScanTable.update({"started_at": self.now}).where(ScanTable.task_uuid == task["uuid"]).execute()

        # TODO: Notify to integrators here
        app.logger.info("Enqueued into {} successfully: task={}".format(self.progress, task["uuid"]))
        return

    def process(self, task):
        # Cancel if detector stays running for a long time
        started_at = task["started_at"].replace(tzinfo=pytz.utc)
        if self.now > (started_at + timedelta(hours=app.config["SCAN_MAX_RUNNING_DURATION_IN_HOUR"])):
            raise Exception("Cancelled: detector was running for a long time")

        # Check if detector is still running
        detector = dtm.load_detector(task["detection_module"], task["session"])
        if not detector.is_running():
            # Enqueue the task to stopped queue
            StoppedTaskHandler().add(task)
