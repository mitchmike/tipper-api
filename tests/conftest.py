import pytest

from model.base import Base
from tipperapi import create_app, db, admin_bp, api_bp, app_bp


@pytest.fixture()
def app():
    app = create_app(testing=True)

    # other setup can go here

    yield app

    # clean up / reset resources here
    with app.app_context():
        if 'test' in app.config['SQLALCHEMY_DATABASE_URI']:  # just to avoid accidental deletion
            Base.metadata.drop_all(db.get_db())

    # hack to remove blueprints from child bps - https://github.com/pallets/flask/issues/4786
    admin_bp._blueprints = []
    admin_bp._got_registered_once = False
    api_bp._blueprints = []
    api_bp._got_registered_once = False
    app_bp._blueprints = []
    app_bp._got_registered_once = False


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
