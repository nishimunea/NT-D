import re
import xml.etree.ElementTree as et
from datetime import datetime
from datetime import timedelta

import pytz
from flask import current_app as app

from detectors import DetectionMode
from detectors import DetectionTarget
from detectors import DetectorBase
from detectors import ReleaseStage
from detectors import Severity


def get_nmap_ssl_cert_severity(output):
    severity = Severity.INFO.value
    now = datetime.now(tz=pytz.utc)
    try:
        m = re.search(r"Not valid after: *([0-9-T:]+)", output)
        expired_at = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc)
        if now > (expired_at + timedelta(days=30)):
            severity = Severity.MEDIUM.value
    except Exception as error:
        app.logger.warn("Could not check SSL certificate severity output={}, error={}".format(output, error))
    return severity


class Detector(DetectorBase):

    NAME = "Nmap"
    VERSION = "7.80"
    SUPPORTED_MODE = [DetectionMode.SAFE.value]
    TARGET_TYPE = DetectionTarget.HOST.value
    STAGE = ReleaseStage.BETA.value
    DESCRIPTION = "Network security scanner"

    POD_NAME_PREFIX = "nmap"
    POD_NAMESPACE = "default"
    POD_RESOURCE_REQUEST = {"memory": "512Mi", "cpu": "0.5"}
    POD_RESOURCE_LIMIT = {"memory": "1Gi", "cpu": "1"}

    CONTAINER_IMAGE = "docker.io/instrumentisto/nmap:7.80"

    # ToDo: Add -T2
    CMD_RUN_SCAN = "nohup nmap -Pn -sC -sV -O -oX out.xml {target} > /dev/null 2>&1 &"
    CMD_CHECK_SCAN_STATUS = "ps x | grep nmap | grep -v grep | wc -c"
    CMD_GET_SCAN_RESULTS = "cat out.xml"

    SAFE_PORTS = ["80", "443"]

    SEVERITY_DEFINITIONS = {
        "dns-recursion": Severity.LOW.value,
        "ftp-anon": Severity.LOW.value,
        "ftp-bounce": Severity.LOW.value,
        "http-git": Severity.MEDIUM.value,
        "http-methods": Severity.LOW.value,
        "http-open-proxy": Severity.LOW.value,
        "http-webdav-scan": Severity.HIGH.value,
        "sip-methods": Severity.LOW.value,
        "smb-os-discovery": Severity.MEDIUM.value,
        "smb2-security-mode": Severity.MEDIUM.value,
        "socks-open-proxy": Severity.MEDIUM.value,
        "sshv1": Severity.LOW.value,
        "ssl-cert": get_nmap_ssl_cert_severity,
        "ssl-known-key": Severity.MEDIUM.value,
        "sslv2": Severity.LOW.value,
        "upnp-info": Severity.LOW.value,
        "vnc-info": Severity.MEDIUM.value,
        "x11-access": Severity.MEDIUM.value,
        "xmpp-info": Severity.MEDIUM.value,
    }

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
                    severity = self.SEVERITY_DEFINITIONS.get(script.get("id", ""), Severity.INFO.value)
                    if callable(severity):
                        severity = severity(script.get("output", ""))
                    results_script.append(
                        {
                            "host": address,
                            "port": port_str,
                            "name": "{} ({})".format(script.get("id", ""), port_str),
                            "description": script.get("output", ""),
                            "severity": severity,
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
