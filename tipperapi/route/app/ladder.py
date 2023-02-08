import datetime
import os

from flask import Blueprint, request, render_template

from model import Team, Game
from tipperapi import db
from tipperapi.route.api.ladder_api import get_ladder
from tipperapi.route.auth import login_required
from tipperapi.services.utils import safe_int

serverEndpoint = os.environ.get('TIPPER_SERVER_ENDPOINT')
bp = Blueprint('ladder', __name__)


@bp.route('/ladder', methods=['GET', 'POST'])
@login_required
def ladder():
    with db.new_session() as db_session:
        teams = db_session.query(Team).order_by(Team.team_identifier).all()
        team_map = {}
        for team in teams:
            team_map[team.team_identifier] = team.city + " " + team.name
        default_season = datetime.datetime.now().year
        season_started = False
        while not season_started:
            season_started = db_session.query(Game).filter(Game.year == default_season).first() is not None
            if not season_started:
                default_season = default_season - 1
    season = safe_int(request.form.get('season', default_season))
    lad = get_ladder(season)
    return render_template('app/ladder.html', ladder=lad, season=season, team_map=team_map)
