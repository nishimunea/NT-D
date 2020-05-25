from datetime import datetime
from datetime import timedelta

import pytz
from dateutil.rrule import rrulestr
from flask import current_app as app
from peewee import fn

from models import ScanTable
from models import db
from tasks.pending import PendingTaskHandler


class TaskScheduler:
    def __init__(self):
        self.now = datetime.now(tz=pytz.utc)

    def set_next_periodic_scan_schedule(self):
        scan_query = ScanTable().select().where((ScanTable.scheduled_at.is_null() & (ScanTable.rrule != "")))
        for scan in scan_query.dicts():
            app.logger.info("Try to schedule next: scan={}".format(scan))
            try:
                next_schedule = rrulestr(scan["rrule"])[0].replace(tzinfo=pytz.utc)
                ScanTable.update({"scheduled_at": next_schedule}).where(ScanTable.id == scan["id"]).execute()
                app.logger.info("Scheduled next successfully: scan={}".format(scan["id"]))
            except Exception as error:
                app.logger.error("ERROR: scan={}, error={}".format(scan["id"], error))

    def set_next_scan(self):
        # Get scan entries that scheduled time has elapsed but still not be in any tasks
        scan_query = (
            ScanTable().select().where((ScanTable.scheduled_at < fn.now()) & (ScanTable.task_uuid.is_null()))
        )

        for scan in scan_query.dicts():
            try:
                app.logger.info("Try to set: scan={}".format(scan))
                # Cancel scan if scan period has already elapsed
                scheduled_at = scan["scheduled_at"].replace(tzinfo=pytz.utc)
                if self.now > (scheduled_at + timedelta(hours=scan["max_duration"])):
                    raise Exception("Cancelled: scheduled period has elapsed")

                with db.database.atomic():
                    # Enqueue the task to pending queue
                    task = PendingTaskHandler().add(scan)
                    # ToDo: Consider race condition between scan reschedule API and this thread context
                    ScanTable.update({"task_uuid": task.uuid}).where(ScanTable.id == scan["id"]).execute()

                app.logger.info("Set scan successfully: scan={}".format(scan["id"]))

            except Exception as error:
                app.logger.warn("ERROR: scan={}, error={}".format(scan["id"], error))
                self.reset_scan_schedule(scan, error)

    def poll(self):
        self.set_next_periodic_scan_schedule()
        self.set_next_scan()

    def reset_scan_schedule(self, scan, error_reason=""):
        ScanTable.update({"scheduled_at": None, "error_reason": error_reason, "task_uuid": None}).where(
            ScanTable.id == scan["id"]
        ).execute()
