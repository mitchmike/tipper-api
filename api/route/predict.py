from flask import jsonify, Blueprint, request

from api.db import new_session
from api.route.db_mgmt_api import safe_int
from predictions.ModelBuilder import ModelBuilder
from predictions.ResultPredictor import ResultPredictor

bp = Blueprint('predict', __name__, url_prefix='/predict')

DEFAULT_FEATURES = sorted(
    ['kicks', 'disposals', 'behinds', 'frees_against', 'stoppage_clearances', 'metres_gained', 'goals'])


@bp.route('/', methods=('GET', 'POST'))
def predict():
    user_id = None
    if request.method == 'GET':
        team = request.args.get('team')
        opp = request.args.get('opp')
        model_features = DEFAULT_FEATURES
        target_variable = request.args.get('target_var', 'score')
        team_year_rounds = [(2022,)]
        opp_year_rounds = [(2022,)]
    else:
        user_id = request.json.get('user_id')
        team = request.json.get('team')
        opp = request.json.get('opp')
        model_features = request.json.get('model_features')
        target_variable = request.json.get('target_variable', 'score')
        team_year_rounds = parse_year_round(request.json.get('team_year_rounds'))
        opp_year_rounds = parse_year_round(request.json.get('opp_year_rounds'))
    if team is None or opp is None or model_features is None:
        return None
    with new_session() as db_session:
        predictor = ResultPredictor(db_session, user_id, team, opp,
                                    'LinearRegression', 'pcnt_diff',
                                    model_features,
                                    target_variable)
        prediction = predictor.get_prediction(team_year_rounds, opp_year_rounds)
        return jsonify(prediction)


@bp.route('/available_features')
def available_features():
    return ModelBuilder.available_features()


def parse_year_round(ls):
    tuples = []
    for yr in ls:
        y, r = yr
        t = tuple([safe_int(y), safe_int(r)])
        tuples.append(t)
    return tuples
