from detectors import DetectionMode
from detectors import DetectionTarget
from detectors import DetectorBase
from detectors import ReleaseStage


class Detector(DetectorBase):

    NAME = "WPScan"
    VERSION = "latest"
    SUPPORTED_MODE = [DetectionMode.SAFE.value]
    TARGET_TYPE = DetectionTarget.URL.value
    STAGE = ReleaseStage.BETA.value
    DESCRIPTION = "WordPress security scanner"

    POD_NAME_PREFIX = "wpscan"
    POD_NAMESPACE = "default"
    POD_RESOURCE_REQUEST = {"memory": "512Mi", "cpu": "0.5"}
    POD_RESOURCE_LIMIT = {"memory": "1Gi", "cpu": "1"}

    CONTAINER_IMAGE = "docker.io/wpscanteam/wpscan:latest"

    CMD_RUN_SCAN = "nohup wpscan --url {target} --format json --disable-tls-checks --max-threads 1 --throttle 1 --enumerate vp,vt,tt,cb,dbe > /wpscan/out.json 2> /dev/null &"
    CMD_CHECK_SCAN_STATUS = "ps x | grep wpscan | grep -v grep | wc -c"
    CMD_GET_SCAN_RESULTS = "cat /wpscan/out.json"

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
        return super().get_results()
