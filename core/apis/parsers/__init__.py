from flask_restx import inputs
from flask_restx import reqparse

AUDIT_LIST_MAX_COUNT = 100
AUDIT_LIST_DEFAULT_COUNT = 20

SCAN_MAX_DURATION_IN_HOUR = 48


class Parser:

    # Session

    SessionPostRequest = reqparse.RequestParser()
    SessionPostRequest.add_argument("password", type=str, required=True, location="json")

    # Audit

    AuditListGetRequest = reqparse.RequestParser()
    AuditListGetRequest.add_argument("q", type=str, default="", location="args")
    AuditListGetRequest.add_argument("page", type=inputs.natural, default=0, location="args")
    AuditListGetRequest.add_argument(
        "count",
        type=inputs.int_range(1, AUDIT_LIST_MAX_COUNT),
        default=AUDIT_LIST_DEFAULT_COUNT,
        location="args",
    )

    AuditListPostRequest = reqparse.RequestParser()
    AuditListPostRequest.add_argument("name", type=inputs.regex("^.{1,128}$"), required=True, location="json")
    AuditListPostRequest.add_argument(
        "description", type=inputs.regex("^.{,128}$"), default="", location="json"
    )

    AuditPatchRequest = AuditListPostRequest

    AuditExportGetRequest = reqparse.RequestParser()
    AuditExportGetRequest.add_argument(
        "tz_offset", type=inputs.int_range(-1440, 1440), default=0, location="args"
    )

    # Scan

    ScanPostRequest = reqparse.RequestParser()
    ScanPostRequest.add_argument("name", type=inputs.regex("^.{1,128}$"), required=True, location="json")
    ScanPostRequest.add_argument("description", type=inputs.regex("^.{,128}$"), default="", location="json")
    ScanPostRequest.add_argument("target", type=inputs.regex("^.{1,128}$"), required=True, location="json")
    ScanPostRequest.add_argument(
        "detection_module", type=inputs.regex("^.{1,128}$"), required=True, location="json"
    )
    ScanPostRequest.add_argument(
        "detection_mode", type=inputs.regex("^.{1,128}$"), required=True, location="json"
    )

    ScanSchedulePostRequest = reqparse.RequestParser()
    ScanSchedulePostRequest.add_argument(
        "scheduled_at", type=inputs.datetime_from_iso8601, required=True, location="json"
    )
    ScanSchedulePostRequest.add_argument(
        "max_duration", type=inputs.int_range(1, SCAN_MAX_DURATION_IN_HOUR), required=True, location="json"
    )

    ScanSchedulePostRequest.add_argument(
        "rrule", type=inputs.regex("^RRULE:.{,128}$"), default="", location="json"
    )

    # Integration
    IntegrationPatchRequest = reqparse.RequestParser()
    IntegrationPatchRequest.add_argument(
        "url", type=inputs.URL(schemes=["https"], check=False), required=True, location="json"
    )
    IntegrationPatchRequest.add_argument("verbose", type=inputs.boolean, default=False, location="json")
