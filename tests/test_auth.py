import pytest
from flask import session
from werkzeug.security import generate_password_hash

from model import User, Team
from tipperapi import db


def test_login(app, client):
    add_user_and_team(app)
    with client:
        response = client.post("/auth/login", data={'email': 'a', 'password': 'abc'}, follow_redirects=True)
        assert len(response.history) == 1
        assert response.request.path == "/"
        assert response.status_code == 200
        assert session['user_id'] == 1
        assert session['team_identifier'] == 'richmond-tigers'


def test_logout(app, client):
    add_user_and_team(app)
    with client:
        with client.session_transaction() as pre_session:
            pre_session['user_id'] = 1
            pre_session['team_identifier'] = 'richmond-tigers'
        response = client.get("/auth/logout", follow_redirects=True)
        assert len(response.history) == 1
        assert response.request.path == "/"
        assert response.status_code == 200
        assert len(session.keys()) == 0


@pytest.mark.parametrize("first_name, last_name, email, password, re_password, flash, result",
                          [('b', 'b', 'b', 'b', 'b', 'Registration successful', True),
                           ('b', 'b', 'a', 'b', 'b', 'already registered', False),  # existing email conflict
                           (None, 'b', 'b', 'b', 'b', 'Registration successful', True),  # TODO fail this
                           ('b', None, 'b', 'b', 'b', 'Registration successful', True),  # TODO fail this
                           ('b', 'b', None, 'b', 'b', 'Email is required', False),
                           ('b', 'b', 'b', None, 'b', 'Password is required', False),
                           ('b', 'b', 'b', 'a', 'b', 'not matching', False),  # passwords dont match
                           ('b', 'b', 'b', 'b', 'a', 'not matching', False),
                           ])
def test_register(app, client, first_name, last_name, email, password, re_password, flash, result):
    add_user_and_team(app)  # existing user
    with client:
        response = client.post('/auth/register', data={'first_name': first_name, 'last_name': last_name, 'email': email, 'password': password, 're_password': re_password}, follow_redirects=True)

        if result:
            assert session['user_id'] == 2
            assert len(response.history) == 1
            assert response.request.path == "/"
            assert response.status_code == 200
        else:
            assert session.get('user_id') is None
        assert flash in response.get_data(as_text=True)


def add_user_and_team(app):
    with app.app_context():
        team = Team()
        team.id = 1
        team.team_identifier = 'richmond-tigers'
        team.name = 'Tigers'
        team.city = 'Richmond'
        team.active_in_competition = True
        user = User('a', 'a', 'a', generate_password_hash('abc'))
        user.follows_team = 1
        with db.new_session() as db_session:
            db_session.add(team)
            db_session.add(user)
            db_session.commit()
