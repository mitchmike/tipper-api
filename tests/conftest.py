import pytest

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
