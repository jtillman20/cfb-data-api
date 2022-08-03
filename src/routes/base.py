from flask_restful import Resource

from models.base import TeamStat
from utils import flask_response


class TeamStatRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> list[TeamStat]:
        pass
