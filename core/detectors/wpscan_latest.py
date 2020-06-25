import json
from ast import literal_eval

from detectors import DetectionMode
from detectors import DetectionTarget
from detectors import DetectorBase
from detectors import ReleaseStage
from detectors import Severity


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

    CMD_RUN_SCAN = "wpscan --url {target} --update --disable-tls-checks --rua -t 200 -e ap,at,tt,cb,dbe -f json -o /wpscan/out.json > /dev/null 2>&1"
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
        results, report = super().get_results()
        report = literal_eval(report)

        if "scan_aborted" in report:
            raise Exception(report["scan_aborted"])

        default_host = ""
        if "effective_url" in report:
            default_host = report["effective_url"]

        # Interesting Findings
        for interesting_finding in report["interesting_findings"]:
            severity = Severity.INFO.value
            if len(interesting_finding["references"]) > 0:
                severity = Severity.MEDIUM.value

            description = interesting_finding["to_s"]
            if len(interesting_finding["interesting_entries"]) > 0:
                description += ", "
                description += ", ".join(interesting_finding["interesting_entries"])

            results.append(
                {
                    "host": interesting_finding["url"],
                    "name": interesting_finding["type"],
                    "description": description,
                    "severity": severity,
                }
            )

        # Version
        if len(report["version"]) > 0:
            version = report["version"]
            severity = Severity.INFO.value
            if version["status"] == "insecure":
                severity = Severity.MEDIUM.value

            results.append(
                {
                    "host": default_host,
                    "name": "WordPress version ({})".format(version["status"]),
                    "description": "{} (Released at {})".format(version["number"], version["release_date"]),
                    "severity": severity,
                }
            )

        # Plugins
        plugins = report["plugins"]
        for key in plugins:
            plugin = plugins[key]
            name = "Plugin"
            severity = Severity.INFO.value
            description = "{} {}".format(plugin["slug"], plugin["version"]["number"])
            if plugin["outdated"] is True:
                name = "Outdated plugin"
                severity = Severity.LOW.value
                description += " (Latest version is {}, released at {})".format(
                    plugin["latest_version"], plugin["last_updated"]
                )

            results.append(
                {"host": plugin["location"], "name": name, "description": description, "severity": severity}
            )

        # Themes
        themes = report["themes"]
        for key in themes:
            theme = themes[key]
            name = "Theme"
            severity = Severity.INFO.value
            description = "{} {}".format(theme["slug"], theme["version"]["number"])
            if theme["outdated"] is True:
                name = "Outdated theme"
                severity = Severity.LOW.value
                description += " (Latest version is {}, released at {})".format(
                    theme["latest_version"], theme["last_updated"]
                )

            results.append(
                {"host": theme["location"], "name": name, "description": description, "severity": severity}
            )

        # Config Backups
        for url in report["config_backups"]:
            results.append(
                {"host": url, "name": "Config backups", "description": url, "severity": Severity.MEDIUM.value}
            )

        # DB Exports
        for url in report["db_exports"]:
            results.append(
                {"host": url, "name": "Database exports", "description": url, "severity": Severity.HIGH.value}
            )

        return results, json.dumps(report)
