import json
from urllib.parse import urlparse

import requests
from flask import request

from detectors import Severity
from detectors import dtm
from integrators import AbstractIntegrator
from integrators import NotificationType


class Integrator(AbstractIntegrator):
    def send(self, notification_type, scan, task, settings):

        title = ""
        emoji = ""
        if notification_type == NotificationType.START:
            if not settings["verbose"]:
                # Do nothing
                return
            title = "Now Scanning"
            emoji = ""
        elif notification_type == NotificationType.ERROR:
            title = "Scan Failed"
            emoji = ":rotating_light:"
        elif notification_type == NotificationType.RESULT:
            title = "Scan Completed"
            emoji = ":sparkles:"

        payload = {
            "text": title,
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": "{} *{}*".format(emoji, title)}},
                {"type": "divider"},
            ],
        }

        detector = [dt for dt in dtm.get_info() if dt["module"] == task["detection_module"]][0]
        detector_info = "{} {} ({})".format(detector["name"], detector["version"], detector["stage"])
        fields = [
            {"type": "mrkdwn", "text": "*Scan Name*\n{}".format(scan["name"])},
            {"type": "mrkdwn", "text": "*Target*\n{}".format(task["target"])},
            {"type": "mrkdwn", "text": "*Detector*\n{}".format(detector_info)},
        ]

        if notification_type == NotificationType.ERROR:
            fields.append({"type": "mrkdwn", "text": "*Error*\n{}".format(scan["error_reason"])})

        if notification_type == NotificationType.RESULT:
            # Total
            fields.append({"type": "mrkdwn", "text": "*Total*\n{}".format(len(task["results"]))})

            # By severity
            counts = {
                Severity.HIGH.value: 0,
                Severity.MEDIUM.value: 0,
                Severity.LOW.value: 0,
                Severity.INFO.value: 0,
            }
            for result in task["results"]:
                counts[result["severity"]] += 1
            for severity in counts:
                if counts[severity] > 0:
                    fields.append({"type": "mrkdwn", "text": "*{}*\n{}".format(severity, counts[severity])})

        payload["blocks"].append({"type": "section", "fields": fields})

        host = urlparse("https://" + request.headers.get("Host"))
        scan_url = host._replace(query=scan["uuid"].hex)
        actions = [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Show Details"},
                "url": scan_url.geturl(),
            }
        ]

        payload["blocks"].append({"type": "actions", "elements": actions})

        requests.post(settings["url"], data=json.dumps(payload))
