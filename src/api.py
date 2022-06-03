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
api.add_resource(ConferenceRPIRoute, f'{API_BASE}/conference_rpi_ratings')
api.add_resource(SRSRoute, f'{API_BASE}/srs_ratings')
api.add_resource(ConferenceSRSRoute, f'{API_BASE}/conference_srs_ratings')

api.add_resource(FieldGoalsRoute, f'{API_BASE}/field_goals/<string:side_of_ball>')
api.add_resource(
    FourthDownsRoute, f'{API_BASE}/fourth_down_conversions/<string:side_of_ball>')
api.add_resource(InterceptionsRoute, f'{API_BASE}/interceptions')
api.add_resource(KickoffsRoute, f'{API_BASE}/kickoffs/<string:side_of_ball>')
api.add_resource(
    KickoffReturnsRoute, f'{API_BASE}/kickoff_returns/<string:side_of_ball>')
api.add_resource(
    KickoffReturnPlaysRoute, f'{API_BASE}/kickoff_return_plays/<string:side_of_ball>')
api.add_resource(PassingRoute, f'{API_BASE}/passing/<string:side_of_ball>')
api.add_resource(
    PassingPlaysRoute, f'{API_BASE}/passing_plays/<string:side_of_ball>')
api.add_resource(PATsRoute, f'{API_BASE}/pats/<string:side_of_ball>')
api.add_resource(PenaltiesRoute, f'{API_BASE}/penalties/<string:side_of_ball>')
api.add_resource(PuntingRoute, f'{API_BASE}/punting/<string:side_of_ball>')
api.add_resource(
    PuntReturnsRoute, f'{API_BASE}/punt_returns/<string:side_of_ball>')
api.add_resource(
    PuntReturnPlaysRoute, f'{API_BASE}/punt_return_plays/<string:side_of_ball>')
api.add_resource(
    RedZoneRoute, f'{API_BASE}/red_zone_conversions/<string:side_of_ball>')
api.add_resource(RushingRoute, f'{API_BASE}/rushing/<string:side_of_ball>')
api.add_resource(
    RushingPlaysRoute, f'{API_BASE}/rushing_plays/<string:side_of_ball>')
api.add_resource(ScoringRoute, f'{API_BASE}/scoring/<string:side_of_ball>')
api.add_resource(
    ScrimmagePlaysRoute, f'{API_BASE}/scrimmage_plays/<string:side_of_ball>')
api.add_resource(SacksRoute, f'{API_BASE}/sacks/<string:side_of_ball>')
api.add_resource(
    TacklesForLossRoute, f'{API_BASE}/tackles_for_loss/<string:side_of_ball>')
api.add_resource(
    ThirdDownsRoute, f'{API_BASE}/third_down_conversions/<string:side_of_ball>')
api.add_resource(TotalRoute, f'{API_BASE}/total/<string:side_of_ball>')
api.add_resource(TurnoversRoute, f'{API_BASE}/turnovers')
