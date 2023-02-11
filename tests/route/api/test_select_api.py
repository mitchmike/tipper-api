import datetime

from model import PlayerFantasy, Player, MatchStatsPlayer
from tests.db_test_util import *
from tipperapi import db
from tipperapi.route.api import select_api
from tipperapi.route.api.select_api import select_data, get_games


def test_select_teams(app, client):
    add_data_array(app, Team, TEAM_COL_NAMES,
                   [
                       [49, 'North Melbourne', 'Kangaroos', 'kangaroos', True],
                       [46, 'Greater Western Sydney', 'Giants', 'greater-western-sydney-giants'],
                       [45, 'Gold Coast', 'Suns', 'gold-coast-suns'],
                       [48, 'Melbourne', 'Demons', 'melbourne-demons']
                   ]
                   )
    freo = add_data(app, Team, TEAM_COL_NAMES, [43, 'Fremantle', 'Dockers', 'fremantle-dockers'])
    with client:
        response = client.get('/api/select/teams')
        json = response.json
        assert len(json) == 5
        json_freo = find_obj_in_json(json, freo.as_dict(), 'id')
        assert dict_equals(json_freo, freo.as_dict(), ['followers'])


def test_get_recent_year_rounds(app):
    add_games(app, 30)
    with app.app_context():
        last10 = select_api.get_recent_year_rounds(10)
        assert last10 == [(2022, 50), (2022, 23), (2022, 22), (2022, 21), (2022, 20), (2022, 19), (2022, 18),
                          (2022, 17), (2022, 16), (2022, 15)]
        last23 = select_api.get_recent_year_rounds(23)
        assert last23 == [(2022, 50), (2022, 23), (2022, 22), (2022, 21), (2022, 20), (2022, 19), (2022, 18),
                          (2022, 17), (2022, 16), (2022, 15), (2022, 14), (2022, 13), (2022, 11), (2022, 10), (2022, 9),
                          (2022, 8), (2022, 7), (2022, 6), (2022, 5), (2022, 4), (2022, 3), (2022, 2), (2022, 1)]


def test_select_data(app):
    with app.app_context():
        with db.new_session() as dbs:
            g1 = add_data(app, Game, GAME_COL_NAMES,
                          [9721, 'carlton-blues', 'richmond-tigers', 'MCG', 85016, 64, 97, 'richmond-tigers', 2019, 1])
            assert len(select_data(dbs, Game, ('id', 'home_team', 'away_team', 'year'), {'year': 2019}).all()) == 1
            assert len(select_data(dbs, Game, ('id', 'home_team', 'away_team', 'year'), {'year': 2020}).all()) == 0
            assert len(select_data(dbs, Game, ('id', 'home_team', 'away_team', 'year'),
                                   {'home_team': 'carlton-blues'}).all()) == 1
            assert len(select_data(dbs, Game, ('id', 'home_team', 'away_team', 'year'),
                                   {'home_team': 'richmond-tigers'}).all()) == 0
            assert len(select_data(dbs, Game, ('id', 'home_team', 'away_team', 'year'),
                                   {'away_team': 'richmond-tigers'}).all()) == 1
            assert len(
                select_data(dbs, Game, ('id', 'home_team', 'away_team', 'year'), {'venue': 'BLA BLA'}).all()) == 1
            assert len(select_data(dbs, Game, ('id', 'home_team', 'away_team', 'year'), {'id': 9721}).all()) == 1
            assert len(
                select_data(dbs, Game, ('id', 'home_team', 'away_team', 'year'), {'id': 9721, 'year': 2020}).all()) == 0
            assert len(
                select_data(dbs, Game, ('id', 'home_team', 'away_team', 'year'), {'id': 9721, 'year': 2019}).all()) == 1
            r1 = select_data(dbs, Game, ('id', 'home_team', 'away_team', 'year'), {'id': 9721, 'year': 2019}).first()
            assert dict_equals(g1.as_dict(), r1.as_dict(), [])

            t1 = add_data(app, Team, TEAM_COL_NAMES, [49, 'North Melbourne', 'Kangaroos', 'kangaroos', True])
            assert len(select_data(dbs, Team, ('team_identifier', 'id'), {'id': 49, 'year': 2019}).all()) == 1
            assert len(select_data(dbs, Team, ('team_identifier', 'id'),
                                   {'id': 49, 'team_identifier': 'carlton-blues'}).all()) == 0
            assert len(select_data(dbs, Team, ('team_identifier', 'id'),
                                   {'id': 49, 'team_identifier': 'kangaroos'}).all()) == 1
            r2 = select_data(dbs, Team, ('team_identifier', 'id'), {'id': 49, 'team_identifier': 'kangaroos'}).first()
            assert dict_equals(t1.as_dict(), r2.as_dict(), [])


def test_get_games(app):
    add_games(app, 10)
    with app.app_context():
        games = get_games({'team': 'richmond-tigers', 'lastXRounds': 9})
        assert len(games) == 9
        assert len([game for game in games if
                    game['home_team'] == 'richmond-tigers' or game['away_team'] == 'richmond-tigers']) == 9


def test_select_player_points(app, client):
    with client:
        assert client.post('/api/select/player_points').status_code == 405
        r1 = client.get('/api/select/player_points')
        assert r1.status_code == 400
        assert b"Required argument 'mode' is not valid" in r1.data
        r2 = client.get('/api/select/player_points?mode=fantasy')
        assert r2.status_code == 200
        assert r2.json == []
        add_data(app, Player, ['id', 'name_key', 'DOB'], [1, 'bruce-willis', datetime.datetime.now()])
        f1 = add_data(app, PlayerFantasy, ['id', 'player_id', 'round_ranking'], [3, 1, 101])
        r3 = client.get('/api/select/player_points?mode=fantasy&name_key=bruce-willis')
        assert r3.status_code == 200
        assert r3.json[0]['player'] == f1.as_dict()['player_id']
        assert r3.json[0]['round_ranking'] == f1.as_dict()['round_ranking']


def test_select_matchstats(app, client):
    with client:
        assert client.post('/api/select/match_stats').status_code == 405
        r1 = client.get('/api/select/match_stats')
        assert r1.status_code == 400
        assert b"Endpoint requires at least one of the following request params" in r1.data
        r2 = client.get('/api/select/match_stats?id=1')
        assert r2.status_code == 200
        assert r2.json == []
        add_data(app, Player, ['id', 'name_key', 'DOB'], [1, 'bruce-willis', datetime.datetime.now()])
        f1 = add_data(app, MatchStatsPlayer, ['id', 'player_id', 'disposals'], [12, 1, 32])
        r3 = client.get('/api/select/match_stats?id=12')
        assert r3.status_code == 200
        assert r3.json[0]['player'] == f1.as_dict()['player_id']
        assert r3.json[0]['disposals'] == f1.as_dict()['disposals']


def test_select_pcnt_diff(app, client):
    # testing of pcnt diff calculation to be done in predictions / aggregated_match_stats
    with client:
        assert client.post('/api/select/pcntdiff').status_code == 405
        r1 = client.get('/api/select/pcntdiff')
        assert r1.status_code == 400
        assert b"Required params not supplied" in r1.data
        r2 = client.get('/api/select/pcntdiff?team=abc&year=2022')
        assert r2.status_code == 200
        assert r2.json == []


def test_select_players(app, client):
    with client:
        assert client.post('/api/select/players').status_code == 405
        today = datetime.datetime.now().date()
        add_data(app, Player, ['id', 'name_key', 'DOB', 'team'], [1, 'bruce-willis', today, 'richmond-tigers'])
        p1 = add_data(app, Player, ['id', 'name_key', 'DOB', 'team'], [2, 'matt-damon', today, 'richmond-tigers'])
        add_data(app, Player, ['id', 'name_key', 'DOB', 'team'], [3, 'chrisdian-bale', today, 'carlton-blues'])
        r1 = client.get('/api/select/players')
        assert r1.status_code == 200
        assert len(r1.json) == 3
        r3 = client.get('/api/select/players?id=2')
        assert r3.status_code == 200
        assert len(r3.json) == 1
        assert dict_equals(r3.json[0], p1.as_dict(), ['injuries', 'DOB'])
        assert r3.json[0]['DOB'] == str(p1.DOB)
