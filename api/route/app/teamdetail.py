import os

import requests
from flask import Blueprint, request, render_template
from sqlalchemy import or_

from api import db
from api.route.auth import login_required
from api.services.utils import safe_int
from model import Team, Game
from predictions.aggregated_match_stats import ALL_ROUNDS, get_pcnt_diff

DEFAULT_YEAR = 2021

DISPLAY_X_GAMES = 10

serverEndpoint = os.environ.get('TIPPER_SERVER_ENDPOINT')
bp = Blueprint('teamdetail', __name__)


@bp.route('/teamdetail', methods=['GET', 'POST'])
@login_required
def teamdetail():
    year = safe_int(request.form.get('season'))
    session = db.new_session()
    if not year:
        year = DEFAULT_YEAR
    # team is required for teamdetail.
    if request.method == 'GET':
        team = request.args.get('team')
    else:
        team = request.form.get('team')
    if not team:
        teams = session.query(Team).all()
        return render_template("app/teamdetail.html", teamslist=teams)

    # team detail
    team_detail = session.query(Team).filter(Team.team_identifier == team).first()
    # team_detail = requests.get(f'{serverEndpoint}/select/teams?team_identifier={team}').json()

    # recent games data
    games = session.query(Game).filter(Game.year == year, or_(Game.home_team == team, Game.away_team == team)).all()
    # games = requests.get(f'{serverEndpoint}/select/games?year={year}&team={team}').json()
    games = sorted(games, key=lambda i: safe_int(i.round_number), reverse=True)
    games = games[:DISPLAY_X_GAMES]

    # get raw data for chart
    pcnt_diff_stats = get_pcnt_diff(session, team, [(year, ALL_ROUNDS)])
    # pcnt_diff_stats = requests.get(f'{serverEndpoint}/select/pcntdiff?year={year}&team={team}').json()
    if len(pcnt_diff_stats) == 0:
        available_stats = []
    else:
        available_stats = [item for item in list(pcnt_diff_stats[0].keys()) if item not in [
            'team_id', 'opponent', 'year', 'round_number'
        ]]

    selected_stats = request.form.getlist('stat')
    if not selected_stats:
        # default selected stats
        selected_stats = ['disposals']

    # populate data for chart
    data = []
    for stat in selected_stats:
        series = {
            'type': "line",
            'name': stat,
            'showInLegend': True,
            'markerSize': 0,
            'dataPoints': []
        }
        for round_number in pcnt_diff_stats:
            series['dataPoints'].append({'x': round_number['round_number'], 'y': round_number[stat]})
        data.append(series)

    # to remember location on page when looking at stats
    scroll_pos = request.form.get("scrollPos", "")
    return render_template("app/teamdetail.html",
                           team_detail=team_detail, team=team, games=games, pcntdiffs=data,
                           availablestats=available_stats, selectedstats=selected_stats,
                           scrollPos=scroll_pos, season=year
                           )
