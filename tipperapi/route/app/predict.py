import os

from flask import Blueprint, render_template, request, flash, session, jsonify

from model import Team
from tipperapi.services.predictions.ModelBuilder import ModelBuilder
from tipperapi import db
from tipperapi.route.api import select_api, predict_api
from tipperapi.route.auth import login_required
from tipperapi.services.utils import safe_int

serverEndpoint = os.environ.get('TIPPER_SERVER_ENDPOINT')

bp = Blueprint('predict', __name__)

DEFAULT_GAME_COUNT = 20


@bp.route('/predict', methods=('POST', 'GET'))
@login_required
def predict():
    form_detail = {}
    db_session = db.new_session()
    teams = db_session.query(Team).order_by(Team.team_identifier).all()
    form_detail['teams'] = teams
    team_map = {}
    for team in teams:
        team_map[team.team_identifier] = team.city + " " + team.name
    form_detail['team_map'] = team_map
    features = ModelBuilder.available_features()
    form_detail['features'] = features
    game_count = safe_int(request.form.get('game_count', DEFAULT_GAME_COUNT))
    form_detail['game_count'] = game_count
    recent_year_rounds = select_api.get_recent_year_rounds(game_count)
    team_year_rounds = recent_year_rounds
    opp_year_rounds = recent_year_rounds
    prediction = None
    if request.method == 'POST':
        team = request.form.get('team')
        opp = request.form.get('opponent')
        selected_features = request.form.getlist('selected_features')
        target_variable = request.form.get('target_variable')
        team_year_rounds = parse_year_rounds(request.form.getlist('team_year_rounds'))
        if len(team_year_rounds) == 0:  # none selected
            flash(f'No rounds selected for {team}')
        raw_opp_yr = request.form.getlist('opp_year_rounds')
        opp_year_rounds = parse_year_rounds(raw_opp_yr)
        if len(opp_year_rounds) == 0:  # none selected
            flash(f'No rounds selected for {opp}')
        if selected_features is None or len(selected_features) == 0:
            flash('No features selected for model')
        elif target_variable is None:
            flash('No target_variable selected for model')
        elif team is not None and opp is not None and len(team_year_rounds) > 0 and len(opp_year_rounds) > 0:
            prediction = predict_api.get_prediction(session.get('user_id'), team, opp, selected_features, target_variable, team_year_rounds, opp_year_rounds)
    form_detail['team_year_rounds'] = team_year_rounds
    form_detail['opp_year_rounds'] = opp_year_rounds
    form_detail['default_target_var'] = 'score'
    form_detail['recent_year_rounds'] = recent_year_rounds
    return render_template('app/predict.html', prediction=prediction, **form_detail)


@bp.route('/recent_games')
def recent_games():
    team = request.args.get('team')
    game_count = request.args.get('game_count', DEFAULT_GAME_COUNT)
    result = get_recent_games(team, game_count)
    return jsonify(result)


def get_recent_games(team, count):
    year_rounds = select_api.get_recent_year_rounds(count)
    team_games = select_api.get_games({'team': team, 'lastXRounds': count})
    result = []
    for yr in year_rounds:
        y = yr[0]
        r = yr[1]
        row = {'year': y, 'round_number': r}
        for g in team_games:
            if g['year'] == y and g['round_number'] == r:
                row['opponent'] = g['home_team'] if g['home_team'] != team else g['away_team']
                row['venue'] = g['venue']
                row['winner'] = g['winner']
        result.append(row)
    return result


def parse_year_rounds(string_year_rounds):
    # convert ['2022,52', '2022,51'] to [[2022, 52], [2022, 51]]
    return [[safe_int(x), safe_int(y)] for (x, y) in [yr.split(',') for yr in string_year_rounds]]
