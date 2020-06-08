import ipaddress
import json
import logging
import os
import traceback

from flask import Flask
from flask import abort
from flask import request
from flask_cors import CORS
from peewee import MySQLDatabase

from apis import api
from apis.authorizers import jwt
from detectors import dtm
from integrators import im
from models import AuditTable
from models import IntegrationTable
from models import ResultTable
from models import ScanTable
from models import TaskTable
from models import db
from utils import Utils


class FormatterJSON(logging.Formatter):
    def format(self, record):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        log = {
            "severity": record.levelname,
            "message": record.message,
            "module": record.module,
            "filename": record.filename,
            "funcName": record.funcName,
            "levelno": record.levelno,
            "lineno": record.lineno,
            "traceback": {},
        }
        if record.exc_info:
            exception_data = traceback.format_exc().splitlines()
            log["traceback"] = exception_data

        return json.dumps(log, ensure_ascii=False)


formatter = FormatterJSON(
    "[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(levelno)s\t%(message)s\n", "%Y-%m-%dT%H:%M:%S"
)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

if Utils.is_gcp():
    logging.getLogger().handlers[0].setFormatter(formatter)
    config_file_path = os.getenv("CONFIG_ENV_FILE_PATH", "config.env")
    Utils.load_env_from_config_file(config_file_path)
    app.config["DATABASE"] = MySQLDatabase(
        os.environ["DB_NAME"],
        unix_socket=os.path.join("/cloudsql", os.environ["DB_INSTANCE_NAME"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
else:
    app.config["DATABASE"] = MySQLDatabase(
        os.getenv("DB_NAME", "ntd"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "password"),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
    )

app.config["ALLOW_ANONYMOUS_AUDIT_ACCESS"] = os.getenv("ALLOW_ANONYMOUS_AUDIT_ACCESS", "True") == "True"
app.config["ADMIN_NAME"] = os.getenv("ADMIN_NAME", "NT-D ADMIN")
app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "password")
app.config["PERMITTED_SOURCE_IP_RANGES"] = os.getenv("PERMITTED_SOURCE_IP_RANGES", "")
app.config["CORS_PERMITTED_ORIGINS"] = os.getenv("CORS_PERMITTED_ORIGINS", "*")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your-256-bit-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 12 * 3600  # 12 hours
app.config["JWT_IDENTITY_CLAIM"] = "sub"
app.config["MAX_SCAN_COUNT_IN_EACH_AUDIT"] = 50
app.config["SCAN_MAX_PENDING_DURATION_IN_HOUR"] = 4
app.config["SCAN_MAX_RUNNING_DURATION_IN_HOUR"] = 6
app.config["RESTX_MASK_SWAGGER"] = False
app.config["SWAGGER_UI_REQUEST_DURATION"] = True
app.config["SWAGGER_UI_DOC_EXPANSION"] = "list"
app.config["SWAGGER_UI_JSONEDITOR"] = True

api.init_app(app)
db.init_app(app)
jwt.init_app(app)
jwt._set_error_handler_callbacks(api)
CORS(app, origins=app.config["CORS_PERMITTED_ORIGINS"])

with db.database:
    db.database.create_tables([AuditTable, ScanTable, TaskTable, ResultTable, IntegrationTable])

dtm.init()
im.init()


@app.before_request
def check_source_ip():
    if len(app.config["PERMITTED_SOURCE_IP_RANGES"]) == 0:
        return

    permitted_ip_ranges = app.config["PERMITTED_SOURCE_IP_RANGES"].split(",")
    source_ip = ipaddress.ip_address(request.access_route[0])

    for permitted_ip_range in permitted_ip_ranges:
        permitted_ip_network = ipaddress.ip_network(permitted_ip_range)
        if source_ip in permitted_ip_network:
            return

    abort(403, "Not allowed to access from your IP address")


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "private, no-store, no-cache, must-revalidate"
    return response
