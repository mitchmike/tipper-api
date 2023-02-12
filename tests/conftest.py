import pytest

from db_test_util import *
from model import User
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


@pytest.fixture()
def admin_user(app, client):
    admin_user = add_data(app, User, USER_COL_NAMES, [1, 'email', 'p', ['ADMIN']])
    with client.session_transaction() as pre_session:
        pre_session['user_id'] = admin_user.id
    return admin_user


@pytest.fixture()
def standard_user(app, client):
    standard_user = add_data(app, User, USER_COL_NAMES, [1, 'email', 'p', []])
    with client.session_transaction() as pre_session:
        pre_session['user_id'] = standard_user.id
    return standard_user

