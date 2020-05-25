from urllib.parse import parse_qs
from urllib.parse import urlencode
from urllib.parse import urlparse

from flask import current_app as app
from flask import g
from flask_jwt_extended import JWTManager
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended.utils import decode_token
from flask_jwt_extended.view_decorators import _decode_jwt_from_headers
from jwt.exceptions import ExpiredSignatureError
from werkzeug.exceptions import Unauthorized

jwt = JWTManager()


class token_required:
    def __init__(self, **kwargs):
        self.admin = kwargs.get("admin", False)

    def __call__(self, f):
        def decorate(*args, **kwargs):

            resp = Unauthorized()
            resp.data = {"message": "Invalid token"}

            target_audit_uuid = ""
            if "audit_uuid" in kwargs:
                target_audit_uuid = kwargs["audit_uuid"]
            elif "scan_uuid" in kwargs:
                target_audit_uuid = kwargs["scan_uuid"][0:24] + "0" * 8

            # Anonymous access configuration is allowed for non administration APIs only
            if app.config["ALLOW_ANONYMOUS_AUDIT_ACCESS"] is True and self.admin is False:
                identity = {"name": ""}
            else:
                try:
                    # Check if given JWT is valid
                    verify_jwt_in_request()
                    identity = get_jwt_identity()
                # If the token is valid but already expired
                except ExpiredSignatureError:
                    encoded_token, _ = _decode_jwt_from_headers()
                    expired_token = decode_token(encoded_token, allow_expired=True)
                    identity = expired_token["sub"]
                    if "auth_endpoint" in identity:
                        # Offer re-authorization endpoint for the target audit
                        url = urlparse(identity["auth_endpoint"])
                        audit_qs = {"audit": target_audit_uuid}
                        new_qs = {**parse_qs(url.query), **audit_qs}
                        auth_endpoint = url._replace(query=urlencode(new_qs, doseq=True)).geturl()
                        resp.data["reauth_endpoint"] = auth_endpoint
                    raise resp
                except Exception:
                    raise resp

                # Anonymous token is not allowed when anonymous access configuration is disabled
                if "name" not in identity or len(identity["name"]) == 0:
                    raise resp

                # Check if the token's scope is valid for the specified API's target
                target_scopes = ["*"]
                if self.admin is False and len(target_audit_uuid) > 0:
                    target_scopes.append(target_audit_uuid)
                if identity["scope"] not in target_scopes:
                    raise resp

            g.identity = identity
            return f(*args, **kwargs)

        return decorate
