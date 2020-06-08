import importlib
import os
import sys
from abc import ABCMeta
from abc import abstractmethod
from enum import Enum
from enum import auto
from enum import unique

from models import IntegrationTable
from models import ScanTable


class IntegratorManager:
    def __init__(self):
        self.integrators = {}
        self.info = []

    def init(self):
        current_path = os.path.dirname(__file__)
        sys.path.insert(0, current_path)

        for f in os.listdir(current_path):
            fname, ext = os.path.splitext(f)
            if ext == ".py" and fname != "__init__":
                module = importlib.import_module(fname)
                self.integrators[fname] = module.Integrator
        sys.path.pop(0)

        for dt in self.integrators:

            self.info.append({"module": dt})

    def get_info(self):
        return self.info

    def send(self, notification_type, task):
        integrations = IntegrationTable.select().where(IntegrationTable.audit_id == task["audit_id"])

        if len(integrations.dicts()) > 0:
            scan = ScanTable.select().where(ScanTable.id == task["scan_id"]).dicts()[0]
            for integration in integrations.dicts():
                self.integrators[integration["service"]]().send(notification_type, scan, task, integration)


@unique
class NotificationType(Enum):
    START = auto()
    ERROR = auto()
    RESULT = auto()


class AbstractIntegrator(metaclass=ABCMeta):
    @abstractmethod
    def send(self, notification_type, scan, task, settings):
        return


im = IntegratorManager()
