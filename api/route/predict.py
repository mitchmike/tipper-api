from flask import jsonify, Blueprint, request

from api.db import new_session
from predictions.ResultPredictor import ResultPredictor

bp = Blueprint('predict', __name__, url_prefix='/predict')


@bp.route('/')
def predict():
    # TODO cleanup
    team = request.args.get('team', 'richmond-tigers')
    opp = request.args.get('opp', 'melbourne-demons')
    with new_session() as session:
        predictor = ResultPredictor(session, team, opp,
                        'LinearRegression', 'pcnt_diff',
                        ['kicks','disposals','marks', 'handballs'],
                        [], [])
        prediction = predictor.get_prediction()
        return jsonify(prediction)