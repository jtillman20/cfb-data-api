from flask_restful import Api

from app import app
from routes import *

api = Api(app)
API_BASE = '/api'

api.add_resource(ConferenceRoute, f'{API_BASE}/conferences')
api.add_resource(TeamRoute, f'{API_BASE}/teams')

api.add_resource(APPollRoute, f'{API_BASE}/ap_poll')
api.add_resource(APPollRankingRoute, f'{API_BASE}/ap_poll_rankings')

api.add_resource(RecordRoute, f'{API_BASE}/records')
api.add_resource(RPIRoute, f'{API_BASE}/rpi_ratings')
api.add_resource(SRSRoute, f'{API_BASE}/srs_ratings')
api.add_resource(ConferenceSRSRoute, f'{API_BASE}/conference_srs_ratings')

api.add_resource(PassingRoute, f'{API_BASE}/passing/<string:side_of_ball>')
api.add_resource(RushingRoute, f'{API_BASE}/rushing/<string:side_of_ball>')
api.add_resource(ScoringRoute, f'{API_BASE}/scoring/<string:side_of_ball>')
api.add_resource(TotalRoute, f'{API_BASE}/total/<string:side_of_ball>')
