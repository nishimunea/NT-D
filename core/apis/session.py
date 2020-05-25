from http import HTTPStatus

from flask import abort
from flask import current_app as app
from flask_jwt_extended import create_access_token
from flask_restx import Namespace
from flask_restx import Resource
from flask_restx import fields

from .parsers import Parser

api = Namespace("session")

SessionPostResponseSchema = api.model("Session Post Response", {"token": fields.String(required=True)})


@api.route("/")
@api.doc(security=None)
@api.response(200, HTTPStatus.OK.description)
@api.response(400, HTTPStatus.BAD_REQUEST.description)
@api.response(401, HTTPStatus.UNAUTHORIZED.description)
@api.response(403, HTTPStatus.FORBIDDEN.description)
class Session(Resource):
    @api.expect(Parser.SessionPostRequest)
    @api.marshal_with(SessionPostResponseSchema)
    def post(self):

        """
        Create new administrator token
        """

        params = Parser.SessionPostRequest.parse_args()
        if params["password"] != app.config["ADMIN_PASSWORD"]:
            abort(401, "Invalid password")

        token = create_access_token(identity={"scope": "*", "name": app.config["ADMIN_NAME"]})
        return {"token": token}
