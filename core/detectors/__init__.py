import importlib
import json
import os
import sys
from abc import ABCMeta
from abc import abstractmethod
from ast import literal_eval
from enum import Enum
from enum import unique

import requests
from kubernetes import config
from kubernetes.client import Configuration


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
                    "stage": self.detectors[dt].STAGE,
                    "description": self.detectors[dt].DESCRIPTION,
                }
            )

    def get_info(self):
        return self.info

    def load_detector(self, module, session):
        try:
            return self.detectors[module](session)
        except:
            raise Exception("Detector `{}` could not be loaded".format(module))


@unique
class DetectionMode(Enum):
    SAFE = "safe"
    UNSAFE = "unsafe"


@unique
class ReleaseStage(Enum):
    ALPHA = "alpha"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"


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
        Configuration.set_default(configuration)


class AbstractDetector(metaclass=ABCMeta):

    NAME = "__name__"
    VERSION = "__version__"
    SUPPORTED_MODE = [DetectionMode.UNSAFE.value]
    STAGE = ReleaseStage.DEPRECATED.value
    DESCRIPTION = "__description__"

    @abstractmethod
    def __init__(self, session):
        try:
            self.session = literal_eval(session)
        except Exception:
            self.session = session

    @abstractmethod
    def create(self):
        return self.session

    @abstractmethod
    def run(self, target, mode):
        return self.session

    @abstractmethod
    def is_ready(self):
        return False

    @abstractmethod
    def is_running(self):
        return True

    @abstractmethod
    def get_results(self):
        results = [
            {
                "host": "__host_1__",
                "port": "__port_1__",
                "name": "__name_1__",
                "description": "__description_1__",
            },
            {
                "host": "__host_2__",
                "port": "__port_2__",
                "name": "__name_2__",
                "description": "__description_2__",
            },
        ]
        return results

    @abstractmethod
    def delete(self):
        return True


dtm = DetectorManager()
