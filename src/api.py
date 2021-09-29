from flask_restful import Api

from app import app
from routes import *

api = Api(app)
API_BASE = '/api'

api.add_resource(ConferenceRoute, f'{API_BASE}/conferences')
api.add_resource(TeamRoute, f'{API_BASE}/teams')

api.add_resource(RecordRoute, f'{API_BASE}/records')
api.add_resource(SRSRoute, f'{API_BASE}/srs_ratings')
api.add_resource(ConferenceSRSRoute, f'{API_BASE}/conference_srs_ratings')
