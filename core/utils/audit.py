from flask import abort

from models import AuditTable


def get_audit_by_uuid(audit_uuid):
    try:
        query = AuditTable.select().where(AuditTable.uuid == audit_uuid)
        return query.dicts()[0], query
    except:
        abort(404)
