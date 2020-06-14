import uuid
import xml.etree.ElementTree as et

from flask import current_app as app
from kubernetes.client.api import core_v1_api
from kubernetes.stream import stream

from detectors import AbstractDetector
from detectors import DetectionMode
from detectors import GKEConfiguration
from detectors import LocalKubernetesConfiguration
from detectors import ReleaseStage
from detectors import Severity
from utils import Utils


class Detector(AbstractDetector):

    NAME = "Nmap"
    VERSION = "7.80"
    SUPPORTED_MODE = [DetectionMode.SAFE.value]
    STAGE = ReleaseStage.BETA.value
    DESCRIPTION = "Network security scannner"

    POD_NAME_PREFIX = "nmap"
    POD_NAMESPACE = "default"
    CONTAINER_IMAGE = "docker.io/instrumentisto/nmap:7.80"

    SAFE_PORTS = ["80", "443"]

    CMD_RUN_SCAN_SAFE = "nohup nmap -Pn -T2 -sC -sV -O -oX out.xml {target} > /dev/null 2>&1 &"

    CMD_CHECK_SCAN_STATUS = "ps x | grep nmap | grep -v grep | wc -c"
    CMD_GET_SCAN_RESULTS = "cat out.xml"

    def __init__(self, session):
        super().__init__(session)

        if Utils.is_gcp():
            GKEConfiguration().set_config()
        else:
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
                            "requests": {"memory": "512Mi", "cpu": "0.5"},
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

        report = stream(
            self.core_api.connect_get_namespaced_pod_exec,
            self.session["pod"]["name"],
            Detector.POD_NAMESPACE,
            command=["/bin/sh", "-c", Detector.CMD_GET_SCAN_RESULTS],
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )

        app.logger.info("Got scan result successfully: report={}".format(report))

        # ToDo: Store raw reports in GCS

        results = []
        results_script = []

        nmaprun = et.fromstring(report)
        host = nmaprun.find("host")

        address = host.find("address").get("addr")
        status = host.find("status").get("state")
        if status != "up":
            raise Exception("Host '{}' is not running, status={}".format(address, status))

        hostnames = host.find("hostnames")
        hostnames_desc = ""
        for hostname in hostnames.findall("hostname"):
            hostnames_desc += "{} ({})\n".format(hostname.get("name"), hostname.get("type"))
        results.append(
            {
                "host": address,
                "name": "Hostnames",
                "description": hostnames_desc.strip(),
                "severity": Severity.INFO.value,
            }
        )

        oses = host.find("os")
        oses_desc = ""
        for osmatch in oses.findall("osmatch"):
            oses_desc += "{} ({}%)\n".format(osmatch.get("name"), osmatch.get("accuracy"))
        results.append(
            {
                "host": address,
                "name": "OS Detection",
                "description": oses_desc.strip(),
                "severity": Severity.INFO.value,
            }
        )

        ports = host.find("ports")
        openports_desc = ""
        openports_severity = Severity.INFO.value
        for port in ports.findall("port"):
            state = port.find("state")
            if "open" in state.get("state"):
                # Open Ports
                protocol = port.get("protocol")
                portid = port.get("portid")
                if portid not in Detector.SAFE_PORTS:
                    openports_severity = Severity.MEDIUM.value
                port_str = "{}:{}".format(protocol, portid)

                service = port.find("service")
                service_str = ""
                if service:
                    product = service.get("product")
                    version = service.get("version", "")
                    if product:
                        service_str = "{} {}".format(product, version).strip()
                    else:
                        service_str = service.get("name")
                openports_desc += "{} ({})".format(port_str, service_str) if service_str else port_str
                openports_desc += "\n"

                # Scripts
                for script in port.findall("script"):
                    results_script.append(
                        {
                            "host": address,
                            "port": port_str,
                            "name": "{} ({})".format(script.get("id", ""), port_str),
                            "description": script.get("output", ""),
                            "severity": Severity.INFO.value,
                        }
                    )

        results.append(
            {
                "host": address,
                "name": "Open Ports",
                "description": openports_desc.strip(),
                "severity": openports_severity,
            }
        )

        results.extend(results_script)
        return results, report
