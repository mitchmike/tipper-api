from datetime import datetime

from db_test_util import *
from model import Player, MatchStatsPlayer
from tipperapi.services.predictions.aggregated_match_stats import get_pcnt_diff


def test_get_pcnt_diff(app):
    year_rounds = [(2021, 1), (2021, 2), (2021, 3)]
    # add game data
    add_data_obj_array(app, [
        create_game(1, 'richmond-tigers', 'geelong-cats', year=2021, round_number=1),
        create_game(2, 'richmond-tigers', 'geelong-cats', year=2021, round_number=2),
        create_game(3, 'richmond-tigers', 'geelong-cats', year=2021, round_number=3)
    ])
    # add player data
    add_data(app, Player, ['id', 'name_key', 'DOB'], [1, 'bruce-willis', datetime.now()])
    # add matchstats data
    add_data_array(app, MatchStatsPlayer, ['player_id', 'game_id', 'team', 'disposals', 'marks'],
                   [
                       # round 1: even stats
                       [1, 1, 'richmond-tigers', 32, 10],
                       [1, 1, 'geelong-cats', 32, 10],
                       # round 2: double stats
                       [1, 2, 'richmond-tigers', 16, 10],
                       [1, 2, 'geelong-cats', 32, 5],
                       # round 3: zero stats
                       [1, 3, 'richmond-tigers', 0, 10],
                       [1, 3, 'geelong-cats', 32, 0]
                   ]
                   )

    with app.app_context():
        with db.new_session() as db_s:
            rich = get_pcnt_diff(db_s, 'richmond-tigers', year_rounds)
            geel = get_pcnt_diff(db_s, 'geelong-cats', year_rounds)
            assert rich[0]['disposals'] == 0.0
            assert rich[0]['marks'] == 0.0
            assert rich[1]['disposals'] == -0.5
            assert rich[1]['marks'] == 1.0
            assert rich[2]['disposals'] == -1.0
            assert rich[2]['marks'] == 0.0
            assert geel[0]['disposals'] == 0.0
            assert geel[0]['marks'] == 0.0
            assert geel[1]['disposals'] == 1.0
            assert geel[1]['marks'] == -0.5
            assert geel[2]['disposals'] == 0.0
            assert geel[2]['marks'] == -1.0

