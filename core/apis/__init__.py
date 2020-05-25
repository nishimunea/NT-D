from flask_restx import Api

from .audit import api as audit
from .detector import api as detector
from .scan import api as scan
from .session import api as session
from .task import api as task

authorizations = {"API Token": {"type": "apiKey", "in": "header", "name": "Authorization"}}

api = Api(
    title="NT-D",
    version="1.0",
    description="Network Threat Detector",
    license="Apache License 2.0",
    license_url="http://www.apache.org/licenses/LICENSE-2.0",
    authorizations=authorizations,
)

api.add_namespace(audit, path="/audit")
api.add_namespace(detector, path="/detector")
api.add_namespace(scan, path="/scan")
api.add_namespace(session, path="/session")
api.add_namespace(task, path="/task")
