import uuid

from peewee import SQL
from peewee import BooleanField
from peewee import CharField
from peewee import CompositeKey
from peewee import DateTimeField
from peewee import ForeignKeyField
from peewee import IntegerField
from peewee import TextField
from peewee import UUIDField
from playhouse.flask_utils import FlaskDB

db = FlaskDB()


class AuditTable(db.Model):
    class Meta:
        db_table = "audit"

    uuid = UUIDField(unique=True)
    name = CharField()
    description = CharField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])
    created_by = CharField(default="")
    updated_by = CharField(default="")


class ScanTable(db.Model):
    class Meta:
        db_table = "scan"

    uuid = UUIDField(unique=True)
    audit_id = ForeignKeyField(AuditTable, backref="scans", on_delete="CASCADE", on_update="CASCADE")
    name = CharField(default="")
    description = CharField(default="")
    target = CharField()
    scheduled_at = DateTimeField(null=True, default=None)
    max_duration = IntegerField(default=0)
    started_at = DateTimeField(null=True, default=None)
    ended_at = DateTimeField(null=True, default=None)
    error_reason = CharField(default="")
    task_uuid = UUIDField(unique=True, null=True, default=None)
    rrule = CharField(default="")
    detection_module = CharField(default="")
    detection_mode = CharField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])
    created_by = CharField(default="")
    updated_by = CharField(default="")


class TaskTable(db.Model):
    class Meta:
        db_table = "task"

    uuid = UUIDField(unique=True, default=uuid.uuid4)
    audit_id = ForeignKeyField(AuditTable, null=True, on_delete="SET NULL", on_update="CASCADE")
    scan_id = ForeignKeyField(ScanTable, null=True, on_delete="SET NULL", on_update="CASCADE")
    scan_uuid = UUIDField(null=True, default=None)
    target = CharField(default="")
    scheduled_at = DateTimeField(default=None)
    max_duration = IntegerField(default=0)
    started_at = DateTimeField(default=None)
    ended_at = DateTimeField(default=None)
    error_reason = CharField(default="")
    detection_module = CharField(default="")
    detection_mode = CharField(default="")
    session = TextField(default="")
    progress = CharField(default="")
    results = TextField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])


class ResultTable(db.Model):
    class Meta:
        db_table = "result"

    scan_id = ForeignKeyField(
        ScanTable, backref="results", null=True, on_delete="CASCADE", on_update="CASCADE"
    )
    host = CharField(null=True)
    port = CharField(null=True)
    name = CharField(null=True)
    description = TextField(null=True)
    severity = CharField(null=True)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])


class IntegrationTable(db.Model):
    class Meta:
        db_table = "integration"
        primary_key = CompositeKey("audit_id", "service")

    audit_id = ForeignKeyField(AuditTable, backref="integrations", on_delete="CASCADE", on_update="CASCADE")
    service = CharField(null=True)
    url = CharField(null=True)
    verbose = BooleanField(default=False)
