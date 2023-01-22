import os
from datetime import time

import requests
from flask import Blueprint, request, render_template

from tipperapi.route.auth import login_required

restEndpoint = os.environ.get('TIPPER_BACKEND_ENDPOINT')
serverEndpoint = os.environ.get('TIPPER_SERVER_ENDPOINT')
tipperMLEP = os.environ.get('TIPPER_ML_ENDPOINT')
bp = Blueprint('odds', __name__)

TEAMMAP = {
    'Brisbane Lions': 'brisbanel',
    'Hawthorn Hawks': 'hawthorn',
    'Collingwood Magpies': 'collingwood',
    'Fremantle Dockers': 'fremantle',
    'Carlton Blues': 'carlton',
    'Essendon Bombers': 'essendon',
    'Geelong Cats': 'geelong',
    'Sydney Swans': 'swans',
    'Greater Western Sydney Giants': 'gws',
    'Gold Coast Suns': 'goldcoast',
    'Adelaide Crows': 'adelaide',
    'Melbourne Demons': 'melbourne',
    'Richmond Tigers': 'richmond',
    'North Melbourne Kangaroos': 'kangaroos',
    'St Kilda Saints': 'stkilda',
    'Port Adelaide Power': 'padelaide',
    'Western Bulldogs': 'bullldogs',
    'West Coast Eagles': 'westcoast'
}


@bp.route('/odds')
@login_required
def tip():
    # TODO: select other rounds and get odds for those
    # if request.method == 'GET':
    #     selectedSeason = request.args.get('selectedSeason')
    #     if not selectedSeason:
    #         selectedSeason='2021'
    #     selectedRound=7
    #     return render_template('odds.html', selectedSeason=selectedSeason, selectedRound=selectedRound)

    # odds = requests.get(f'{restEndpoint}/oddsNextWeek').json()
    odds = []
    game_list = []
    for game in odds:
        game_dict = {'id': game['id'], 'team1': game['teams'][0], 'team2': game['teams'][1],
                     'commence_time': time.strftime('%A %d %B %Y %H:%M:%S', time.localtime(game['commence_time']))}
        game_list.append(game_dict)

    selected_game_id = request.args.get('game')
    selected_game = next((x for x in odds if x['id'] == selected_game_id), None)
    if selected_game:
        for site in selected_game['sites']:
            site.update(last_update=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(site['last_update'])))

        team_ids = [
            TEAMMAP[selected_game['teams'][0]],
            TEAMMAP[selected_game['teams'][1]]
        ]
        selected_game.update(teamIds=team_ids)

        try:
            prediction = requests.get(
                f'{tipperMLEP}/predict/linearregression_pcntdiffstats/{team_ids[0]}/{team_ids[1]}/weighted/0.2').json()
            print(prediction)
            tipper_score = [prediction['team1score'], prediction['team2score']]
            team_scores = ["{:.3f}".format(tipper_score[0]), "{:.3f}".format(tipper_score[1])]
            selected_game.update(teamscores=team_scores)
        except:
            return render_template('app/failure.html', text='could not fetch prediction')

    return render_template("app/odds.html", selectedGame=selected_game, gameList=game_list, odds=odds)
