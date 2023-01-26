from flask import session
from werkzeug.security import generate_password_hash

from model import User
from tests.conftest import add_team
from tipperapi import db


def test_login(app, client):
    add_team(app)
    with app.app_context():
        user = User('a', 'a', 'a', generate_password_hash('abc'))
        user.follows_team = 1
        with db.new_session() as db_session:
            db_session.add(user)
            db_session.commit()

    with client:
        response = client.post("/auth/login", data={'email': 'a', 'password': 'abc'})
        assert response.status_code == 302
        assert session['user_id'] == 1
        assert session['team_identifier'] == 'richmond-tigers'
