from detectors import AbstractDetector
from detectors import DetectionMode
from detectors import ReleaseStage
from detectors import Severity


class Detector(AbstractDetector):

    NAME = "OpenVAS"
    VERSION = "Version"
    SUPPORTED_MODE = [DetectionMode.UNSAFE.value]
    STAGE = ReleaseStage.DEPRECATED.value
    DESCRIPTION = "OpenVAS Description"

    def __init__(self, session):
        super().__init__(session)
        self.name = "OpenVAS"

    def create(self):
        print("----------------------- Create OpenVAS Pod ----------------------------")
        session = {}
        return session

    def delete(self):
        print("----------------------- Delete OpenVAS Pod ----------------------------")
        return True

    def run(self, target, mode):
        print("----------------------- Run OpenVAS ----------------------------")
        return session

    def is_ready(self):
        print("----------------------- OpenVAS is ready? ----------------------------")
        return True

    def is_running(self):
        print("----------------------- OpenVAS is running? ----------------------------")
        return False

    def get_results(self):
        print("----------------------- Get OpenVAS result ----------------------------")
        results = [
            {
                "host": "__openvas host1__",
                "port": "__openvas port1__",
                "name": "__openvas name1__",
                "description": "__openvas description1__",
                "severity": Severity.HIGH.value,
            },
            {
                "host": "__openvas host2__",
                "port": "__openvas port2__",
                "name": "__openvas name2__",
                "description": "__openvas description2__",
                "severity": Severity.LOW.value,
            },
        ]
        return results
