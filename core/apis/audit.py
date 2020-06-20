import csv
import os
import secrets
import tempfile
import uuid
from datetime import timedelta
from http import HTTPStatus

from flask import Response
from flask import abort
from flask import current_app as app
from flask import g
from flask_restx import Namespace
from flask_restx import Resource
from flask_restx import fields

from detectors import DetectionTarget
from detectors import dtm
from integrators import im
from models import AuditTable
from models import IntegrationTable
from models import ResultTable
from models import ScanTable
from storages import Storage
from utils.audit import get_audit_by_uuid
from utils.scan import get_safe_url
from utils.scan import get_scan_by_uuid
from utils.scan import validate_host

from .authorizers import token_required
from .parsers import Parser
from .scan import ScanGetResponseSchema

api = Namespace("audit")

AUDIT_EXPORT_SCAN_RESULT_CSV_COLUMNS = ["host", "port", "name", "description"]
AUDIT_EXPORT_RESPONSE_HEADERS = {"Content-Type": "text/csv", "Content-Disposition": "attachment"}

IntegrationGetResponseSchema = api.model(
    "Integration Get Response", {"service": fields.String(required=True)}
)

AuditGetResponseSchema = api.model(
    "Audit Get Response",
    {
        "id": fields.Integer(required=True),
        "uuid": fields.String(required=True, attribute=lambda audit: audit["uuid"].hex),
        "name": fields.String(required=True),
        "description": fields.String(required=True),
        "created_at": fields.DateTime(required=True),
        "updated_at": fields.DateTime(required=True),
        "created_by": fields.String(required=True),
        "updated_by": fields.String(required=True),
        "source_ip_address": fields.String(required=True),
        "scans": fields.List(fields.Nested(ScanGetResponseSchema), required=True),
        "integrations": fields.List(fields.Nested(IntegrationGetResponseSchema), required=True),
    },
)

AuditListGetResponseSchema = api.model(
    "Audit List Get Response",
    {
        "total": fields.Integer(required=True),
        "audits": fields.List(fields.Nested(AuditGetResponseSchema), required=True),
    },
)


@api.route("/")
@api.doc(security="API Token")
@api.response(200, HTTPStatus.OK.description)
@api.response(400, HTTPStatus.BAD_REQUEST.description)
@api.response(401, HTTPStatus.UNAUTHORIZED.description)
@api.response(403, HTTPStatus.FORBIDDEN.description)
class AuditList(Resource):
    @api.expect(Parser.AuditListGetRequest)
    @api.marshal_with(AuditListGetResponseSchema, skip_none=True, as_list=True)
    @token_required(admin=True)
    def get(self):

        """
        Retrieve list of audits
        """

        params = Parser.AuditListGetRequest.parse_args()

        audit_query = AuditTable.select(AuditTable)
        if len(params["q"]) > 0:
            audit_query = audit_query.where(
                (AuditTable.name ** "%{}%".format(params["q"]))
                | (AuditTable.description ** "%{}%".format(params["q"]))
            )

        total = audit_query.count()

        audit_query = audit_query.order_by(AuditTable.updated_at.desc()).paginate(
            params["page"], params["count"]
        )

        return {"total": total, "audits": list(audit_query.dicts())}

    @api.expect(Parser.AuditListPostRequest)
    @api.marshal_with(AuditGetResponseSchema)
    @token_required(admin=True)
    def post(self):

        """
        Create new audit
        """

        params = Parser.AuditListPostRequest.parse_args()

        # Audit UUID must be 'NNNNNNNN-NNNN-NNNN-NNNN-NNNN00000000'.
        # Lower 32 bits of the UUID are used for identifying scans/tasks in the audit.
        params["uuid"] = uuid.UUID(secrets.token_hex(12) + "0" * 8)
        params["created_by"] = g.identity["name"]
        params["updated_by"] = g.identity["name"]

        AuditTable(**params).save()
        return get_audit_by_uuid(params["uuid"])[0]


@api.route("/<string:audit_uuid>/")
@api.doc(security="API Token")
@api.response(200, HTTPStatus.OK.description)
@api.response(400, HTTPStatus.BAD_REQUEST.description)
@api.response(401, HTTPStatus.UNAUTHORIZED.description)
@api.response(403, HTTPStatus.FORBIDDEN.description)
@api.response(404, HTTPStatus.NOT_FOUND.description)
class AuditItem(Resource):
    @api.marshal_with(AuditGetResponseSchema)
    @token_required()
    def get(self, audit_uuid):

        """
        Retrieve the specified audit information
        """

        audit, audit_query = get_audit_by_uuid(audit_uuid)
        audit["source_ip_address"] = os.getenv("NAT_EGRESS_IP", "127.0.0.1")
        audit["scans"] = audit_query[0].scans.dicts()
        audit["integrations"] = audit_query[0].integrations.dicts()
        return audit

    @api.expect(Parser.AuditPatchRequest)
    @api.marshal_with(AuditGetResponseSchema)
    @token_required()
    def patch(self, audit_uuid):

        """
        Update the specified audit information
        """

        params = Parser.AuditPatchRequest.parse_args()
        params["updated_by"] = g.identity["name"]

        AuditTable.update(params).where(AuditTable.uuid == audit_uuid).execute()
        return get_audit_by_uuid(audit_uuid)[0]

    @token_required(admin=True)
    def delete(self, audit_uuid):

        """
        Delete the specified audit information
        """

        AuditTable.delete().where(AuditTable.uuid == audit_uuid).execute()
        Storage().delete(audit_uuid)
        return {}


@api.route("/<string:audit_uuid>/export/")
@api.doc(security="API Token")
@api.expect(Parser.AuditExportGetRequest)
@api.response(200, HTTPStatus.OK.description, headers=AUDIT_EXPORT_RESPONSE_HEADERS)
@api.response(401, HTTPStatus.UNAUTHORIZED.description)
@api.response(403, HTTPStatus.FORBIDDEN.description)
@api.response(404, HTTPStatus.NOT_FOUND.description)
class AuditExport(Resource):
    @token_required()
    def get(self, audit_uuid):

        """
        Export the specified audit information
        """

        params = Parser.AuditExportGetRequest.parse_args()

        audit, audit_query = get_audit_by_uuid(audit_uuid)
        output = audit["name"] + "\n" + audit["description"] + "\n\n"

        scoped_scan_ids = []
        for scan in audit_query[0].scans.dicts():
            # Todo: この比較がスキャン完了を示す processed の代わりになるか確認
            if scan["ended_at"] is not None:
                scoped_scan_ids.append(scan["id"])

        results = (
            ResultTable.select(ResultTable, ScanTable)
            .join(ScanTable)
            .where(ResultTable.scan_id.in_(scoped_scan_ids))
            .order_by(ResultTable.scan_id)
        )

        with tempfile.TemporaryFile("r+") as f:
            writer = csv.DictWriter(f, AUDIT_EXPORT_SCAN_RESULT_CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for result in results.dicts():
                result["started_at"] = result["started_at"] + timedelta(minutes=params["tz_offset"])
                result["ended_at"] = result["ended_at"] + timedelta(minutes=params["tz_offset"])
                writer.writerow(result)
            f.flush()
            f.seek(0)
            output += f.read()

        return Response(response=output, status=200, headers=AUDIT_EXPORT_RESPONSE_HEADERS)


@api.route("/<string:audit_uuid>/scan/")
@api.doc(security="API Token")
@api.response(200, HTTPStatus.OK.description)
@api.response(400, HTTPStatus.BAD_REQUEST.description)
@api.response(401, HTTPStatus.UNAUTHORIZED.description)
@api.response(403, HTTPStatus.FORBIDDEN.description)
@api.response(404, HTTPStatus.NOT_FOUND.description)
class AuditScan(Resource):
    @api.expect(Parser.ScanPostRequest)
    @api.marshal_with(ScanGetResponseSchema)
    @token_required()
    def post(self, audit_uuid):

        """
        Create new scan into the specified audit
        """

        params = Parser.ScanPostRequest.parse_args()

        try:
            detector = dtm.load_detector(params["detection_module"], None)
            if detector.TARGET_TYPE == DetectionTarget.HOST.name:
                validate_host(params["target"])
            elif detector.TARGET_TYPE == DetectionTarget.URL.name:
                params["target"] = get_safe_url(params["target"])
        except Exception as e:
            abort(400, str(e))

        # Scan UUID consists of upper 96 bits audit UUID (=A) and lower 32 bits random number (=B),
        # i.e., 'AAAAAAAA-AAAA-AAAA-AAAA-AAAABBBBBBBB'.
        params["uuid"] = uuid.UUID(audit_uuid[0:24] + secrets.token_hex(4))
        params["created_by"] = g.identity["name"]
        params["updated_by"] = g.identity["name"]

        audit, _ = get_audit_by_uuid(audit_uuid)
        params["audit_id"] = audit["id"]

        current_scan_count = ScanTable.select().where(ScanTable.audit_id == params["audit_id"]).count()
        if current_scan_count >= app.config["MAX_SCAN_COUNT_IN_EACH_AUDIT"]:
            abort(400, "Max scan count exceeded")

        ScanTable(**params).save()

        return get_scan_by_uuid(params["uuid"])[0]


@api.route("/<string:audit_uuid>/integration/<string:service>/")
@api.doc(security="API Token")
@api.response(200, HTTPStatus.OK.description)
@api.response(400, HTTPStatus.BAD_REQUEST.description)
@api.response(401, HTTPStatus.UNAUTHORIZED.description)
@api.response(403, HTTPStatus.FORBIDDEN.description)
@api.response(404, HTTPStatus.NOT_FOUND.description)
class AuditIntegration(Resource):
    @api.expect(Parser.IntegrationPatchRequest)
    @api.marshal_with(ScanGetResponseSchema)
    @token_required()
    def patch(self, audit_uuid, service):

        """
        Set service integration
        """

        integrators = im.get_info()
        supported_services = []
        for integrator in integrators:
            supported_services.append(integrator["module"])

        if service not in supported_services:
            abort(400, "Not supported")

        params = Parser.IntegrationPatchRequest.parse_args()

        try:
            params["url"] = get_safe_url(params["url"])
        except Exception as e:
            abort(400, str(e))

        audit, _ = get_audit_by_uuid(audit_uuid)
        params["audit_id"] = audit["id"]
        params["service"] = service

        IntegrationTable.insert(params).on_conflict_replace().execute()

        return get_audit_by_uuid(audit_uuid)[0]

    @token_required()
    def delete(self, audit_uuid, service):

        """
        Delete the specified service integration
        """

        audit, _ = get_audit_by_uuid(audit_uuid)

        IntegrationTable.delete().where(
            (IntegrationTable.audit_id == audit["id"]) & (IntegrationTable.service == service)
        ).execute()
        return {}
