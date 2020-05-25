import uuid

from flask import current_app as app
from kubernetes.client.api import core_v1_api
from kubernetes.stream import stream

from detectors import AbstractDetector
from detectors import DetectionMode
from detectors import LocalKubernetesConfiguration
from detectors import ReleaseStage
from detectors import Severity


class Detector(AbstractDetector):

    NAME = "Nmap"
    VERSION = "Version"
    SUPPORTED_MODE = [DetectionMode.UNSAFE.value]
    STAGE = ReleaseStage.DEPRECATED.value
    DESCRIPTION = "Nmap Description"

    POD_NAME_PREFIX = "nmap"
    POD_NAMESPACE = "default"
    CONTAINER_IMAGE = "docker.io/instrumentisto/nmap:7.80"

    CMD_RUN_SCAN_SAFE = "nohup nmap -sV -O -sC -Pn -oX out.xml {target} &"
    CMD_CHECK_SCAN_STATUS = "ps x | grep nmap | grep -v grep | wc -c"
    CMD_GET_SCAN_RESULTS = "cat out.xml"

    def __init__(self, session):
        super().__init__(session)
        # TODO: Load GKE configuration here
        LocalKubernetesConfiguration().set_config()
        self.core_api = core_v1_api.CoreV1Api()

    def create(self):
        app.logger.info("Try to create detector: session={}".format(self.session))

        pod_name = Detector.POD_NAME_PREFIX + "-" + uuid.uuid4().hex
        resp = None

        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": pod_name},
            "spec": {
                "restartPolicy": "Never",
                "containers": [
                    {
                        "image": Detector.CONTAINER_IMAGE,
                        "image_pull_policy": "IfNotPresent",
                        "name": Detector.POD_NAME_PREFIX,
                        "command": ["sh", "-c", "while true;do date;sleep 5; done"],
                        "resources": {
                            "requests": {"memory": "512Mi", "cpu": "1"},
                            "limits": {"memory": "1Gi", "cpu": "1"},
                        },
                    }
                ],
            },
        }
        resp = self.core_api.create_namespaced_pod(body=pod_manifest, namespace=Detector.POD_NAMESPACE)
        app.logger.info("Created detector successfully: resp={}".format(resp))
        self.session = {"pod": {"name": pod_name}}
        return self.session

    def delete(self):
        app.logger.info("Try to delete detector: session={}".format(self.session))
        try:
            resp = self.core_api.delete_namespaced_pod(
                name=self.session["pod"]["name"], body={}, namespace=Detector.POD_NAMESPACE
            )
            app.logger.info("Deleted detector successfully: resp={}".format(resp))
        except Exception as error:
            app.logger.error("Error on delete detector: {}".format(error))

    def run(self, target, mode):
        app.logger.info("Try to run scan: target={}, mode={}, session={}".format(target, mode, self.session))

        resp = stream(
            self.core_api.connect_get_namespaced_pod_exec,
            self.session["pod"]["name"],
            Detector.POD_NAMESPACE,
            command=["/bin/sh", "-c", Detector.CMD_RUN_SCAN_SAFE.format(target=target)],
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )

        app.logger.info("Run detector successfully: resp={}".format(resp))
        return self.session

    def is_ready(self):
        app.logger.info("Try to check detector is ready: session={}".format(self.session))
        resp = self.core_api.read_namespaced_pod(
            name=self.session["pod"]["name"], namespace=Detector.POD_NAMESPACE
        )

        app.logger.info("Checked detector is ready successfully: resp={}".format(resp))
        if resp.status.phase != "Pending":
            return True
        else:
            # TODO: Need to handle other phases, e.g., Running, Succeeded, Failed and Unknown
            return False

    def is_running(self):
        app.logger.info("Try to check detector is running: session={}".format(self.session))

        resp = stream(
            self.core_api.connect_get_namespaced_pod_exec,
            self.session["pod"]["name"],
            Detector.POD_NAMESPACE,
            command=["/bin/sh", "-c", Detector.CMD_CHECK_SCAN_STATUS],
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )

        app.logger.info("Checked detector is running successfully: resp={}".format(resp))
        return int(resp) != 0

    def get_results(self):
        app.logger.info("Try to get scan results: session={}".format(self.session))

        resp = stream(
            self.core_api.connect_get_namespaced_pod_exec,
            self.session["pod"]["name"],
            Detector.POD_NAMESPACE,
            command=["/bin/sh", "-c", Detector.CMD_GET_SCAN_RESULTS],
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )

        results = [
            {
                "host": "__nmap host1__",
                "port": "__nmap port1__",
                "name": "__nmap name1__",
                "description": "__nmap description1__",
                "severity": Severity.HIGH.value,
            },
            {
                "host": "__nmap host2__",
                "port": "__nmap port2__",
                "name": "__nmap name2__",
                "description": "__nmap description2__",
                "severity": Severity.MEDIUM.value,
            },
            {
                "host": "__nmap host3__",
                "port": "__nmap port3__",
                "name": "__nmap name3__",
                "description": "__nmap description3__",
                "severity": Severity.LOW.value,
            },
            {
                "host": "__nmap host4__",
                "port": "__nmap port4__",
                "name": "__nmap name4__",
                "description": "__nmap description4__",
                "severity": Severity.INFO.value,
            },
            {
                "host": "__nmap host5__",
                "port": "__nmap port5__",
                "name": "__nmap name5__",
                "description": "__nmap description5__",
                "severity": Severity.HIGH.value,
            },
            {
                "host": "__nmap host6__",
                "port": "__nmap port6__",
                "name": "__nmap name6__",
                "description": "__nmap description6__",
                "severity": Severity.MEDIUM.value,
            },
            {
                "host": "__nmap host7__",
                "port": "__nmap port7__",
                "name": "__nmap name7__",
                "description": "__nmap description7__",
                "severity": Severity.LOW.value,
            },
            {
                "host": "__nmap host8__",
                "port": "__nmap port8__",
                "name": "__nmap name8__",
                "description": "__nmap description8__",
                "severity": Severity.INFO.value,
            },
        ]

        app.logger.info("Got scan result successfully: resp={}".format(resp))

        # TODO: Set actual scan result
        return results
