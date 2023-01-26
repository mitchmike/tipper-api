import pytest

from model import Team
from model.base import Base
from tipperapi import create_app, db


@pytest.fixture()
def app():
    app = create_app(testing=True)

    # other setup can go here

    yield app

    # clean up / reset resources here
    with app.app_context():
        if 'test' in app.config['SQLALCHEMY_DATABASE_URI']:  # just to avoid accidental deletion
            Base.metadata.drop_all(db.get_db())


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def add_team(app):
    with app.app_context():
        team = Team()
        team.id = 1
        team.team_identifier = 'richmond-tigers'
        team.name = 'Tigers'
        team.city = 'Richmond'
        team.active_in_competition = True
        with db.new_session() as db_session:
            db_session.add(team)
            db_session.commit()
