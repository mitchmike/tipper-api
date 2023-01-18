import os

import requests
from flask import Blueprint, request, render_template, redirect, url_for

from api.route.api.ladder_api import get_ladder
from api.route.auth import login_required

serverEndpoint = os.environ.get('TIPPER_SERVER_ENDPOINT')
bp = Blueprint('ladder', __name__)


@bp.route('/ladder', methods=['GET', 'POST'])
@login_required
def ladder():
    season = request.form.get('season')
    # default season to 2021
    if not season:
        season = '2021'
    lad = get_ladder(season)
    return render_template('app/ladder.html', ladder=lad, season=season)
