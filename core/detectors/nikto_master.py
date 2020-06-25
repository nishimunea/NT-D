import json
from ast import literal_eval

from detectors import DetectionMode
from detectors import DetectionTarget
from detectors import DetectorBase
from detectors import ReleaseStage
from detectors import Severity


class Detector(DetectorBase):

    NAME = "Nikto"
    VERSION = "master"
    SUPPORTED_MODE = [DetectionMode.SAFE.value]
    TARGET_TYPE = DetectionTarget.URL.value
    STAGE = ReleaseStage.ALPHA.value
    DESCRIPTION = "Web server scanner"

    POD_NAME_PREFIX = "nikto"
    POD_NAMESPACE = "default"
    POD_RESOURCE_REQUEST = {"memory": "512Mi", "cpu": "0.5"}
    POD_RESOURCE_LIMIT = {"memory": "1Gi", "cpu": "1"}

    CONTAINER_IMAGE = "docker.io/securecodebox/nikto:master"

    CMD_RUN_SCAN = (
        "nikto-master/program/nikto.pl -h {target} -o /tmp/result.json  > /dev/null 2> /tmp/error.txt"
    )
    CMD_CHECK_SCAN_STATUS = "ps x | grep nikto | grep -v grep | wc -c"
    CMD_GET_SCAN_RESULTS = "cat /tmp/result.json"
    CMD_GET_ERROR_REASON = "cat /tmp/error.txt"

    def __init__(self, session):
        super().__init__(session)

    def create(self):
        return super().create()

    def delete(self):
        return super().delete()

    def run(self, target, mode):
        return super().run(target, mode)

    def is_ready(self):
        return super().is_ready()

    def is_running(self):
        return super().is_running()

    def get_results(self):
        results, report = super().get_results()

        if len(report) > 0:
            report = literal_eval(report)
            for vulnerability in report["vulnerabilities"]:
                results.append(
                    {
                        "host": "{} ({})".format(report["host"], report["ip"]),
                        "port": report["port"],
                        "name": "{} ({} {})".format(
                            vulnerability["id"], vulnerability["method"], vulnerability["url"]
                        ),
                        "description": vulnerability["msg"],
                        "severity": Severity.INFO.value,
                    }
                )
        else:
            resp = self._pod_exec(self.CMD_GET_ERROR_REASON)
            raise Exception(resp)

        return results, json.dumps(report)
