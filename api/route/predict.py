from flask import jsonify, Blueprint, request

from api.db import new_session
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
    else:
        user_id = request.form.get('user_id')
        team = request.form.get('team')
        opp = request.form.get('opp')
        model_features = request.form.getlist('model_features')
        target_variable = request.form.get('target_variable', 'score')
    if team is None or opp is None or model_features is None:
        return None
    with new_session() as db_session:
        predictor = ResultPredictor(db_session, user_id, team, opp,
                                    'LinearRegression', 'pcnt_diff',
                                    model_features,
                                    target_variable,
                                    [], [])
        prediction = predictor.get_prediction()
        return jsonify(prediction)


@bp.route('/available_features')
def available_features():
    return ModelBuilder.available_features()
