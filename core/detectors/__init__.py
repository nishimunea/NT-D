import importlib
import json
import logging
import os
import sys
import uuid
from abc import ABCMeta
from abc import abstractmethod
from ast import literal_eval
from enum import Enum
from enum import unique

import requests
from flask import current_app as app
from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.stream import stream

from utils import Utils

kslogger = logging.getLogger("kubernetes")
console_h = logging.StreamHandler()
kslogger.addHandler(console_h)
kslogger.setLevel(logging.DEBUG)


class DetectorManager:
    def __init__(self):
        self.detectors = {}
        self.info = []

    def init(self):
        current_path = os.path.dirname(__file__)
        sys.path.insert(0, current_path)

        for f in os.listdir(current_path):
            fname, ext = os.path.splitext(f)
            if ext == ".py" and fname != "__init__":
                module = importlib.import_module(fname)
                self.detectors[fname] = module.Detector
        sys.path.pop(0)

        for dt in self.detectors:

            self.info.append(
                {
                    "module": dt,
                    "name": self.detectors[dt].NAME,
                    "version": self.detectors[dt].VERSION,
                    "supported_mode": self.detectors[dt].SUPPORTED_MODE,
                    "target_type": self.detectors[dt].TARGET_TYPE,
                    "stage": self.detectors[dt].STAGE,
                    "description": self.detectors[dt].DESCRIPTION,
                }
            )

    def get_info(self):
        return self.info

    def load_detector(self, module, session):
        try:
            return self.detectors[module](session)
        except Exception as error:
            raise Exception("Detector `{}` could not be loaded, error={}".format(module, error))


@unique
class DetectionMode(Enum):
    SAFE = "Safe"
    UNSAFE = "Unsafe"


@unique
class DetectionTarget(Enum):
    HOST = "Host"
    URL = "URL"


@unique
class ReleaseStage(Enum):
    ALPHA = "Alpha"
    BETA = "Beta"
    STABLE = "Stable"
    DEPRECATED = "Deprecated"


@unique
class Severity(Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"


class LocalKubernetesConfiguration:
    def set_config(self):
        config.load_kube_config()
        configuration = Configuration()
        configuration.assert_hostname = False
        Configuration.set_default(configuration)


class GKEConfiguration:

    METADATA_TOKEN_ENDPOINT = (
        "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
    )

    def get_access_token(self):
        headers = {"Metadata-Flavor": "Google"}
        resp = requests.get(GKEConfiguration.METADATA_TOKEN_ENDPOINT, headers=headers)
        return json.loads(resp.text)["access_token"]

    def set_config(self):
        configuration = Configuration()
        configuration.api_key["authorization"] = self.get_access_token()
        configuration.api_key_prefix["authorization"] = "Bearer"
        configuration.host = os.environ.get("GKE_MASTER_SERVER")
        configuration.verify_ssl = False
        configuration.assert_hostname = False
        Configuration.set_default(configuration)


class DetectorBase(metaclass=ABCMeta):

    NAME = "__name__"
    VERSION = "__version__"
    SUPPORTED_MODE = []
    TARGET_TYPE = "__target_type"
    STAGE = ReleaseStage.DEPRECATED.value
    DESCRIPTION = "__description__"

    POD_NAME_PREFIX = "__pod_name_prefix__"
    POD_NAMESPACE = "__pod_namespace__"
    POD_RESOURCE_REQUEST = {}
    POD_RESOURCE_LIMIT = {}

    CONTAINER_IMAGE = "__container_image__"

    CMD_RUN_SCAN = "echo run > out.txt"
    CMD_CHECK_SCAN_STATUS = "ps x | wc -c"
    CMD_GET_SCAN_RESULTS = "cat out.txt"

    @abstractmethod
    def __init__(self, session):
        try:
            self.session = literal_eval(session)
        except Exception:
            self.session = session

        if Utils.is_gcp():
            GKEConfiguration().set_config()
        else:
            LocalKubernetesConfiguration().set_config()
        self.core_api = core_v1_api.CoreV1Api()

    @abstractmethod
    def create(self):
        app.logger.info("Try to create detector: session={}".format(self.session))

        pod_name = self.POD_NAME_PREFIX + "-" + uuid.uuid4().hex
        resp = None
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": pod_name},
            "spec": {
                "restartPolicy": "Never",
                "containers": [
                    {
                        "image": self.CONTAINER_IMAGE,
                        "image_pull_policy": "IfNotPresent",
                        "name": self.POD_NAME_PREFIX,
                        "command": ["sh", "-c", "while true;do date;sleep 5; done"],
                        "resources": {
                            "requests": self.POD_RESOURCE_REQUEST,
                            "limits": self.POD_RESOURCE_LIMIT,
                        },
                    }
                ],
            },
        }
        resp = self.core_api.create_namespaced_pod(body=pod_manifest, namespace=self.POD_NAMESPACE)
        app.logger.info("Created detector successfully: resp={}".format(resp))
        self.session = {"pod": {"name": pod_name}}
        return self.session

    @abstractmethod
    def delete(self):
        app.logger.info("Try to delete detector: session={}".format(self.session))
        try:
            resp = self.core_api.delete_namespaced_pod(
                name=self.session["pod"]["name"], body={}, namespace=self.POD_NAMESPACE
            )
            app.logger.info("Deleted detector successfully: resp={}".format(resp))
        except Exception as error:
            app.logger.error("Error on delete detector: {}".format(error))
        return True

    @abstractmethod
    def run(self, target, mode):
        app.logger.info("Try to run scan: target={}, mode={}, session={}".format(target, mode, self.session))
        resp = stream(
            self.core_api.connect_get_namespaced_pod_exec,
            self.session["pod"]["name"],
            self.POD_NAMESPACE,
            command=[
                "/bin/sh",
                "-c",
                "nohup {command} &".format(command=self.CMD_RUN_SCAN.format(target=target)),
            ],
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        app.logger.info("Run detector successfully: resp={}".format(resp))
        return self.session

    @abstractmethod
    def is_ready(self):
        app.logger.info("Try to check detector is ready: session={}".format(self.session))
        resp = self.core_api.read_namespaced_pod(
            name=self.session["pod"]["name"], namespace=self.POD_NAMESPACE
        )

        app.logger.info("Checked detector is ready successfully: resp={}".format(resp))
        if resp.status.phase != "Pending":
            return True
        else:
            # TODO: Need to handle other phases, e.g., Running, Succeeded, Failed and Unknown
            return False

    @abstractmethod
    def is_running(self):
        app.logger.info("Try to check detector is running: session={}".format(self.session))
        resp = stream(
            self.core_api.connect_get_namespaced_pod_exec,
            self.session["pod"]["name"],
            self.POD_NAMESPACE,
            command=["/bin/sh", "-c", self.CMD_CHECK_SCAN_STATUS],
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        app.logger.info("Checked detector is running successfully: resp={}".format(resp))
        return int(resp) != 0

    @abstractmethod
    def get_results(self):
        app.logger.info("Try to get scan results: session={}".format(self.session))
        report = stream(
            self.core_api.connect_get_namespaced_pod_exec,
            self.session["pod"]["name"],
            self.POD_NAMESPACE,
            command=["/bin/sh", "-c", self.CMD_GET_SCAN_RESULTS],
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        results = []
        app.logger.info("Got scan result successfully: report={}".format(report))
        return results, report


dtm = DetectorManager()
