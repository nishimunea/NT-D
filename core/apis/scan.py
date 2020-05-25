from http import HTTPStatus

import pytz
from flask import abort
from flask import g
from flask_restx import Namespace
from flask_restx import Resource
from flask_restx import fields

from models import ResultTable
from models import ScanTable
from utils.scan import get_scan_by_uuid
from utils.scan import validate_schedule

from .authorizers import token_required
from .parsers import Parser

api = Namespace("scan")

RRULE_WEEKDAY_LIST = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]

ScanResultGetResponseSchema = api.model(
    "Scan Result Get Response",
    {
        "host": fields.String(required=True),
        "port": fields.String(required=True),
        "name": fields.String(required=True),
        "description": fields.String(required=True),
        "severity": fields.String(required=True),
    },
)

ScanGetResponseSchema = api.model(
    "Scan Get Response",
    {
        "uuid": fields.String(required=True, attribute=lambda scan: scan["uuid"].hex),
        "name": fields.String(required=True),
        "description": fields.String(required=True),
        "target": fields.String(required=True),
        "scheduled_at": fields.DateTime(required=True),
        "max_duration": fields.Integer(required=True),
        "rrule": fields.String(required=True),
        "started_at": fields.DateTime(required=True),
        "ended_at": fields.DateTime(required=True),
        "error_reason": fields.String(required=True),
        "detection_module": fields.String(required=True),
        "detection_mode": fields.String(required=True),
        "created_at": fields.DateTime(required=True),
        "updated_at": fields.DateTime(required=True),
        "created_by": fields.String(required=True),
        "updated_by": fields.String(required=True),
        "results": fields.List(fields.Nested(ScanResultGetResponseSchema), required=True),
    },
)


@api.route("/<string:scan_uuid>/")
@api.doc(security="API Token")
@api.response(200, HTTPStatus.OK.description)
@api.response(401, HTTPStatus.UNAUTHORIZED.description)
@api.response(403, HTTPStatus.FORBIDDEN.description)
@api.response(404, HTTPStatus.NOT_FOUND.description)
class ScanItem(Resource):
    @api.marshal_with(ScanGetResponseSchema)
    @token_required()
    def get(self, scan_uuid):

        """
        Retrieve the specified scan
        """

        scan, scan_query = get_scan_by_uuid(scan_uuid)
        results = ResultTable.select(ResultTable).where(ResultTable.scan_id == scan["id"])
        scan["results"] = results.dicts()
        return scan

    @token_required()
    def delete(self, scan_uuid):

        """
        Delete the specified scan
        """

        ScanTable.delete().where(ScanTable.uuid == scan_uuid).execute()
        return {}


@api.route("/<string:scan_uuid>/schedule/")
@api.doc(security="API Token")
@api.response(200, HTTPStatus.OK.description)
@api.response(400, HTTPStatus.BAD_REQUEST.description)
@api.response(401, HTTPStatus.UNAUTHORIZED.description)
@api.response(403, HTTPStatus.FORBIDDEN.description)
@api.response(404, HTTPStatus.NOT_FOUND.description)
class ScanSchedule(Resource):
    @api.expect(Parser.ScanSchedulePostRequest)
    @api.marshal_with(ScanGetResponseSchema)
    @token_required()
    def post(self, scan_uuid):

        """
        Schedule the specified scan
        """

        scan, _ = get_scan_by_uuid(scan_uuid)
        if scan["scheduled_at"] is not None:
            abort(400, "Scan is already scheduled")
        params = Parser.ScanSchedulePostRequest.parse_args()
        validate_schedule(params["scheduled_at"])

        if len(params["rrule"]) > 0:
            scheduled_at = params["scheduled_at"].replace(tzinfo=pytz.utc)
            weekday = RRULE_WEEKDAY_LIST[scheduled_at.weekday()]
            hour = scheduled_at.time().hour
            params["rrule"] = "RRULE:FREQ=WEEKLY;BYDAY={};BYHOUR={};BYMINUTE=0;BYSECOND=0".format(
                weekday, hour
            )

        params["task_uuid"] = None
        params["started_at"] = None
        params["ended_at"] = None
        params["updated_by"] = g.identity["name"]
        ScanTable.update(params).where(ScanTable.uuid == scan_uuid).execute()

        return get_scan_by_uuid(scan_uuid)[0]

    @api.marshal_with(ScanGetResponseSchema)
    @token_required()
    def delete(self, scan_uuid):

        """
        Cancel the specified scan schedule
        """

        scan, _ = get_scan_by_uuid(scan_uuid)
        if scan["scheduled_at"] is None:
            abort(400, "Scan is not scheduled")

        default_values = {
            "scheduled_at": None,
            "max_duration": 0,
            "rrule": "",
            "started_at": None,
            "ended_at": None,
            "task_uuid": None,
            "updated_by": g.identity["name"],
        }

        ScanTable.update(default_values).where(ScanTable.uuid == scan_uuid).execute()
        return get_scan_by_uuid(scan_uuid)[0]
