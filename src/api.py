from flask_restful import Api

from app import app
from routes import *

api = Api(app)
API_BASE = '/api'

api.add_resource(ConferenceRoute, f'{API_BASE}/conferences')
api.add_resource(TeamRoute, f'{API_BASE}/teams')
