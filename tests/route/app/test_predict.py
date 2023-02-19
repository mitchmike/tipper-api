from datetime import datetime

from werkzeug.datastructures import ImmutableMultiDict

from db_test_util import *
from model import Player, MatchStatsPlayer
from tipperapi.route.api import select_api, predict_api
from tipperapi.route.app import predict
from tipperapi.schema.games.game_schema import GameSchema


def test_get_recent_games(app, monkeypatch):
    g1 = GameSchema().dump(create_game(game_id=1, year=2022, round_number=20, away_team='geelong-cats'))
    g2 = GameSchema().dump(create_game(game_id=2, year=2022, round_number=19, away_team='melbourne-demons'))
    g3 = GameSchema().dump(create_game(game_id=3, year=2022, round_number=18, away_team='some-other-team'))
    with app.app_context():
        monkeypatch.setattr(select_api, "get_games", lambda *args: [g1, g2, g3])
        monkeypatch.setattr(select_api, "get_recent_year_rounds", lambda *args: [(2022, 20), (2022, 19)])
        result = predict.get_recent_games('richmond-tigers', 2)
        assert len(result) == 2
        assert [g for g in result if g['round_number'] == 20][0]['opponent'] == 'geelong-cats'
        assert [g for g in result if g['round_number'] == 19][0]['opponent'] == 'melbourne-demons'
        assert [g for g in result if g['round_number'] == 18] == []


def test_get_recent_games_atest(app):
    add_test_games_to_db(app)
    with app.app_context():
        assert len(predict.get_recent_games('richmond-tigers', 4)) == 3
        assert len(predict.get_recent_games('richmond-tigers', 3)) == 3
        assert len(predict.get_recent_games('richmond-tigers', 2)) == 2
        assert len(predict.get_recent_games('richmond-tigers', 1)) == 1


def test_parse_year_rounds():
    result = predict.parse_year_rounds(['2022,52', '2022,51'])
    assert result == [[2022, 52], [2022, 51]]


def test_get_recent_games_endpoint(app, client):
    add_test_games_to_db(app)
    with client:
        response = client.get('/recent_games')
        assert len(response.json) == 3
        assert response.json[0] == {"round_number": 20, "year": 2022}


def test_predict_get(app, client, standard_user, monkeypatch):
    with client:
        response = client.get('/predict')
        assert response.status_code == 200


def test_predict_post(app, client, standard_user, monkeypatch):
    monkeypatch.setattr(select_api, "get_recent_year_rounds", lambda *args: [(2022, 20), (2022, 19)])
    monkeypatch.setattr(predict_api, "get_prediction", lambda *args: sample_prediction)
    data = ImmutableMultiDict(
        [('team', 'richmond-tigers'), ('opponent', 'geelong-cats'), ('selected_features', 'kicks'),
         ('selected_features', 'handballs'), ('target_variable', 'score'),
         ('team_year_rounds', '2022, 20'), ('team_year_rounds', '2022, 19'),
         ('opp_year_rounds', '2022, 20'), ('opp_year_rounds', '2022, 19')])
    with client:
        response = client.post('/predict', data=data)
        assert response.status_code == 200
        # assert result table is present
        assert b'<h1>Result</h1>' in response.data


def test_predict_post_atest(app, client, standard_user):
    add_data_obj_array(app, [
        create_game(1, 'richmond-tigers', 'geelong-cats', year=2022, round_number=18),
        create_game(2, 'richmond-tigers', 'geelong-cats', year=2022, round_number=19),
        create_game(3, 'richmond-tigers', 'geelong-cats', year=2022, round_number=20)
    ])
    # add teams
    add_data_obj(app, create_team())
    # add player data
    add_data(app, Player, ['id', 'name_key', 'DOB'], [1, 'bruce-willis', datetime.now()])
    # add matchstats data
    add_data_array(app, MatchStatsPlayer, ['player_id', 'game_id', 'team', 'kicks', 'handballs'],
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
    data = ImmutableMultiDict(
        [('team', 'richmond-tigers'), ('opponent', 'geelong-cats'), ('selected_features', 'kicks'),
         ('selected_features', 'handballs'), ('target_variable', 'win'),
         ('team_year_rounds', '2022, 20'), ('team_year_rounds', '2022, 19'),
         ('opp_year_rounds', '2022, 20'), ('opp_year_rounds', '2022, 19')])
    with client:
        response = client.post('/predict', data=data)
        assert response.status_code == 200
        # assert result table is present
        assert b'<h1>Result</h1>' in response.data


def add_test_games_to_db(app):
    g1 = create_game(game_id=1, year=2022, round_number=20, away_team='geelong-cats')
    g2 = create_game(game_id=2, year=2022, round_number=19, away_team='melbourne-demons')
    g3 = create_game(game_id=3, year=2022, round_number=18, away_team='some-other-team')
    add_data_obj_array(app, [g1, g2, g3])


sample_prediction = {'new_model': True, 'winner': 'brisbane-lions',
              'prediction_for_model': {'model_type': 'LinearRegression', 'results': None,
                                       'file_name': 'LinearRegression_123.sav',
                                       'score': 0.24380683436118067, 'target_variable': 'score', 'active': True,
                                       'features': ['kicks'], 'model_strategy': 'pcnt_diff', 'id': 5477,
                                       'created_at': '2023-02-12T12:38:51.558914'}, 'opponent': 'brisbane-lions',
              'team_score': 66.21766163855754, 'opponent_score': 84.77101329867509, 'team': 'adelaide-crows',
              'prediction_for_user': 1, 'id': 122, 'created_at': '2023-02-12T12:38:51.644425'}
