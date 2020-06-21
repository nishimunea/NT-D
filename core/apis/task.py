from http import HTTPStatus

from flask import abort
from flask import current_app as app
from flask_restx import Namespace
from flask_restx import Resource

from tasks.pending import PendingTaskHandler
from tasks.running import RunningTaskHandler
from tasks.schedule import TaskScheduler
from tasks.stopped import StoppedTaskHandler

api = Namespace("task")


@api.route("/<string:task>/")
@api.doc(security="None")
@api.response(200, HTTPStatus.OK.description)
class Task(Resource):
    def get(self, task):

        """
        Invoke task handlers
        """

        tasks = {
            "schedule": TaskScheduler(),
            "pending": PendingTaskHandler(),
            "running": RunningTaskHandler(),
            "stopped": StoppedTaskHandler(),
        }

        try:
            tasks[task].poll()
        except Exception as error:
            app.logger.error(error)
            abort(404)

        return True
