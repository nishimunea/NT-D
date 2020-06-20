from http import HTTPStatus

from flask_restx import Namespace
from flask_restx import Resource
from flask_restx import fields

from detectors import dtm

api = Namespace("detector")

DetectorGetResponseSchema = api.model(
    "Detector Get Response",
    {
        "module": fields.String(required=True),
        "supported_mode": fields.List(fields.String, required=True),
        "target_type": fields.String(required=True),
        "stage": fields.String(required=True),
        "name": fields.String(required=True),
        "version": fields.String(required=True),
        "description": fields.String(required=True),
    },
)


@api.route("/")
@api.doc(security=None)
@api.response(200, HTTPStatus.OK.description)
@api.response(403, HTTPStatus.FORBIDDEN.description)
class Detector(Resource):
    @api.marshal_with(DetectorGetResponseSchema, as_list=True)
    def get(self):

        """
        Retrieve detector information
        """

        return dtm.get_info()
