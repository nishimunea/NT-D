import ipaddress
import os
import socket
import urllib
from datetime import datetime

import pytz
import validators
from flask import abort

from models import ScanTable

SCAN_SCHEDULABLE_DAYS_FROM_NOW = 7


def get_scan_by_uuid(scan_uuid):
    try:
        query = ScanTable.select().where(ScanTable.uuid == scan_uuid)
        return query.dicts()[0], query
    except:
        abort(404)


def validate_schedule(scheduled_at):
    scheduled_at = scheduled_at.replace(tzinfo=pytz.utc)
    now = datetime.now(tz=pytz.utc).astimezone(pytz.timezone("Asia/Tokyo"))
    from_now = scheduled_at - now

    if from_now.days > SCAN_SCHEDULABLE_DAYS_FROM_NOW:
        abort(401, "Schedule must be within {} days".format(SCAN_SCHEDULABLE_DAYS_FROM_NOW))

    return True


def get_safe_url(target):
    url = urllib.parse.urlparse(target)

    if len(url.scheme) == 0 or url.scheme not in ["http", "https"]:
        raise Exception("URL schema is not http: and https:")

    path = url.path
    if len(path) > 0:
        path = os.path.normpath(path)
        path = urllib.parse.quote(path)

    try:
        port = url.port
    except:
        raise Exception("Port in URL is not a number")

    if port is not None:
        if port < 1:
            raise Exception("Port number is less than 1")
        if port > 65535:
            raise Exception("Port number is larger than 65535")
        port = ":{}".format(port)

    if url.hostname is None:
        raise Exception("Hostname is empty")
    validate_host(url.hostname)

    return "{schema}://{hostname}{port}{path}".format(
        schema=url.scheme, hostname=url.hostname, port=port or "", path=path
    )


def validate_host(target):
    if validators.ip_address.ipv4(target):
        if not ipaddress.ip_address(target).is_global:
            raise Exception("Private IP address is not allowed")
    elif validators.domain(target):
        try:
            _, _, addrs = socket.gethostbyname_ex(target)
        except:
            raise Exception("FQDN could not be resolved")

        if len(addrs) == 0:
            raise Exception("FQDN has no active hosts")
        else:
            for addr in addrs:
                if not ipaddress.ip_address(addr).is_global:
                    raise Exception("Private IP address is not allowed")
    else:
        raise Exception("Not a valid FQDN or IPv4 address")

    return True
