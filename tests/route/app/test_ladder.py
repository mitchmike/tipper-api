from werkzeug.security import generate_password_hash

from model import User
from tests.db_test_util import create_team, create_game
from tipperapi import db
from tipperapi.route.api.ladder_api import get_ladder


def test_ladder_get_request(app, client):
    add_teams_and_game(app)
    with client.session_transaction() as session:
        # set a user id without going through the login route
        session["user_id"] = 1
    with client:
        # should give the latest year that we have data for
        response = client.get("/ladder")
        assert response.status_code == 200
        assert b"2021 Ladder" in response.data


def test_ladder_post_request(app, client):
    add_teams_and_game(app)
    with client.session_transaction() as session:
        # set a user id without going through the login route
        session["user_id"] = 1
    with client:
        # should give the latest year that we have data for
        response = client.post("/ladder", data={'year': 2021})
        assert response.status_code == 200
        assert b"2021 Ladder" in response.data
        assert '''<tr id=geelong-cats class="clickable-row" style="cursor: pointer;" data-href="/teamdetail?team=geelong-cats">
                            <td style="text-align: end;">Geelong Cats</td>
                            <td>7</td>
                            <td>6</td>
                            <td>0</td>
                            <td>110.33</td>
                        </tr>
                
                        <tr id=richmond-tigers class="clickable-row" style="cursor: pointer;" data-href="/teamdetail?team=richmond-tigers">
                            <td style="text-align: end;">Richmond Tigers</td>
                            <td>6</td>
                            <td>5</td>
                            <td>1</td>
                            <td>97.02</td>
                        </tr>
                
                        <tr id=melbourne-demons class="clickable-row" style="cursor: pointer;" data-href="/teamdetail?team=melbourne-demons">
                            <td style="text-align: end;">Melbourne Demons</td>
                            <td>4</td>
                            <td>6</td>
                            <td>1</td>
                            <td>91.75</td>
                        </tr>''' in response.text


def test_get_ladder(app):
    # simple unit test
    add_teams_and_game(app)
    with app.app_context():
        result = get_ladder(2021)
        assert len(result) == 3
        assert_team_position(result, 'geelong-cats', 7, 6, 0, 1004, 910, 0)
        assert_team_position(result, 'richmond-tigers', 6, 5, 1, 847, 873, 1)
        assert_team_position(result, 'melbourne-demons', 4, 6, 1, 756, 824, 2)


def assert_team_position(result, teamname, wins, losses, draws, pf, pa, position):
    res = result[position]
    assert res['teamname'] == teamname
    assert res['wins'] == wins
    assert res['losses'] == losses
    assert res['draws'] == draws
    assert res['pf'] == pf
    assert res['pa'] == pa


def add_teams_and_game(app):
    with app.app_context():
        richmond = create_team(1, 'Richmond', 'Tigers', 'richmond-tigers', True)
        melbourne = create_team(48, 'Melbourne', 'Demons', 'melbourne-demons', True)
        geelong = create_team(44, 'Geelong', 'Cats', 'geelong-cats', True)

        user = User('a', 'a', 'a', generate_password_hash('abc'))
        user.follows_team = 1
        with db.new_session() as test_db_session:
            test_db_session.add(richmond)
            test_db_session.add(melbourne)
            test_db_session.add(geelong)
            test_db_session.add(create_game(10395, 'richmond-tigers', 'geelong-cats', 63, 126, 'geelong-cats'))
            test_db_session.add(create_game(10595, 'richmond-tigers', 'melbourne-demons', 76, 76, 'DRAW'))
            test_db_session.add(create_game(10326, 'richmond-tigers', 'geelong-cats', 81, 50, 'richmond-tigers'))
            test_db_session.add(create_game(9766, 'richmond-tigers', 'melbourne-demons', 85, 42, 'richmond-tigers'))
            test_db_session.add(create_game(9820, 'richmond-tigers', 'geelong-cats', 37, 104, 'geelong-cats'))
            test_db_session.add(create_game(9925, 'richmond-tigers', 'geelong-cats', 85, 66, 'richmond-tigers'))

            test_db_session.add(create_game(10482, 'geelong-cats', 'richmond-tigers', 95, 57, 'geelong-cats'))
            test_db_session.add(create_game(10519, 'geelong-cats', 'melbourne-demons', 77, 81, 'melbourne-demons'))
            test_db_session.add(create_game(10663, 'geelong-cats', 'richmond-tigers', 89, 86, 'geelong-cats'))
            test_db_session.add(create_game(10681, 'geelong-cats', 'melbourne-demons', 91, 63, 'geelong-cats'))
            test_db_session.add(create_game(10301, 'geelong-cats', 'richmond-tigers', 31, 57, 'richmond-tigers'))
            test_db_session.add(create_game(9734, 'geelong-cats', 'melbourne-demons', 126, 46, 'geelong-cats'))

            test_db_session.add(create_game(10361, 'melbourne-demons', 'geelong-cats', 85, 60, 'melbourne-demons'))
            test_db_session.add(create_game(10376, 'melbourne-demons', 'richmond-tigers', 82, 48, 'melbourne-demons'))
            test_db_session.add(create_game(10541, 'melbourne-demons', 'geelong-cats', 125, 42, 'melbourne-demons'))
            test_db_session.add(create_game(10189, 'melbourne-demons', 'richmond-tigers', 52, 79, 'richmond-tigers'))
            test_db_session.add(create_game(10151, 'melbourne-demons', 'geelong-cats', 44, 47, 'geelong-cats'))
            test_db_session.add(create_game(9887, 'melbourne-demons', 'richmond-tigers', 60, 93, 'richmond-tigers'))
            test_db_session.add(user)
            test_db_session.commit()
