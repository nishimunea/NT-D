from datetime import timedelta

import pytz
from flask import current_app as app

from detectors import dtm
from models import TaskTable
from tasks import TaskHandlerBase
from tasks import TaskProgress
from tasks.running import RunningTaskHandler
from utils.scan import validate_target


class PendingTaskHandler(TaskHandlerBase):
    def __init__(self):
        super().__init__(TaskProgress.PENDING.name)

    def add(self, scan):
        app.logger.info("Try to enqueue into {}: scan={}".format(self.progress, scan))
        validate_target(scan["target"])
        detector = dtm.load_detector(scan["detection_module"], None)
        session = detector.create()
        task = {
            "audit_id": scan["audit_id"],
            "scan_id": scan["id"],
            "target": scan["target"],
            "scheduled_at": scan["scheduled_at"],
            "max_duration": scan["max_duration"],
            "detection_module": scan["detection_module"],
            "detection_mode": scan["detection_mode"],
            "session": session,
            "progress": TaskProgress.PENDING.name,
        }
        task = TaskTable(**task)
        task.save()
        app.logger.info("Enqueued into {} successfully: scan={}".format(self.progress, scan["id"]))
        return task

    def process(self, task):
        # Cancel if detector stays pending for a long time
        created_at = task["created_at"].replace(tzinfo=pytz.utc)
        if self.now > (created_at + timedelta(hours=app.config["SCAN_MAX_PENDING_DURATION_IN_HOUR"])):
            raise Exception("Cancelled: detector stayed pending for a long time")

        # Check if detector is ready to scan
        detector = dtm.load_detector(task["detection_module"], task["session"])
        if detector.is_ready():
            # Enqueue the task to running queue
            RunningTaskHandler().add(task)
