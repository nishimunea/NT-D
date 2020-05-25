import ipaddress
import socket
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

    # if scheduled_at < now:
    #    abort(401, "Schedule must be a future date")

    if from_now.days > SCAN_SCHEDULABLE_DAYS_FROM_NOW:
        abort(401, "Schedule must be within {} days".format(SCAN_SCHEDULABLE_DAYS_FROM_NOW))

    return True


def validate_target(target):
    if validators.ip_address.ipv4(target):
        if not ipaddress.ip_address(target).is_global:
            raise Exception("Private ip address is not allowed")
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
                    raise Exception("Private ip address is not allowed")
    else:
        raise Exception("Target is not FQDN or IPv4 address")

    return True
