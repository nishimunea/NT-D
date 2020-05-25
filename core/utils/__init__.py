import os
import re
from urllib.parse import urlparse

SLACK_DOMAIN = "slack.com"


class Utils:
    @staticmethod
    def load_env_from_config_file(config_file_path):
        with open(config_file_path, "r") as f:
            content = f.readlines()
            content = [re.split("\s*=\s*", x.strip(), 1) for x in content if "=" in x]
            for k, v in dict(content).items():
                os.environ[k] = v
            return True

    @staticmethod
    def is_slack_url(value):
        try:
            url = urlparse(value)
            return url.hostname.endswith(SLACK_DOMAIN)
        except Exception:
            return False

    @staticmethod
    def is_gcp():
        return bool(os.getenv("GAE_ENV", ""))
