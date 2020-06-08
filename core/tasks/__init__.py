from datetime import datetime
from datetime import timedelta
from enum import Enum
from enum import unique

import pytz
from flask import current_app as app
from peewee import JOIN

from detectors import dtm
from integrators import NotificationType
from integrators import im
from models import ScanTable
from models import TaskTable
from models import db


@unique
class TaskProgress(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class TaskHandlerBase:
    def __init__(self, progress):
        self.now = datetime.now(tz=pytz.utc)
        self.progress = progress

    def add(self, task):
        return

    def poll(self):
        # Get all task entries that progress matches the task queue name, e.g., PENDING.
        task_query = (
            TaskTable.select(TaskTable, ScanTable.uuid.alias("scan_exists"))
            .join(ScanTable, JOIN.LEFT_OUTER, on=(TaskTable.uuid == ScanTable.task_uuid))
            .where(TaskTable.progress == self.progress)
            .order_by(TaskTable.updated_at.asc())
        )
        for task in task_query.dicts():
            try:
                # Task UUID changes if the task is cancelled/rescheduled by user.
                # Here we cancel a task that is no longer connected to any scan entries.
                if task.pop("scan_exists") is None:
                    raise Exception("Cancelled: scan has been cancelled/rescheduled by user")

                # Cancel the task if that scan period has already elapsed
                scheduled_at = task["scheduled_at"].replace(tzinfo=pytz.utc)
                if self.now > (scheduled_at + timedelta(hours=task["max_duration"])):
                    raise Exception("Cancelled: scheduled period has elapsed")

                # Call task process function prepared by each handler
                app.logger.info("Do process: task={}".format(task["uuid"]))
                self.process(task)
            except Exception as error:
                app.logger.warn("ERROR: task={}, error={}".format(task["uuid"], error))
                self.finish(task, error)

    def finish(self, task, error_reason=""):
        app.logger.info("Try to delete: task={}, error_reason={}".format(task, error_reason))
        if task["session"] is not None:
            detector = dtm.load_detector(task["detection_module"], task["session"])
            detector.delete()
        with db.database.atomic():
            TaskTable.delete().where(TaskTable.uuid == task["uuid"]).execute()
            # Here we use task uuid for finding corresponding scan entry
            # because task uuid of scan entry is changed by user's re-schedule
            ScanTable.update({"scheduled_at": None, "task_uuid": None, "error_reason": error_reason}).where(
                ScanTable.task_uuid == task["uuid"]
            ).execute()

        if error_reason != "":
            im.send(NotificationType.ERROR, task)

        app.logger.info("Deleted successfully: task={}, error_reason={}".format(task["uuid"], error_reason))

    def process(self, task):
        pass
