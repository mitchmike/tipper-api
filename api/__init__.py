import os
from dotenv import load_dotenv

from flask import Flask, url_for, redirect

from api.route import auth, admin, select_api, scrape_api, users, db_mgmt_api, model_mgmt_api


def create_app(test_config=None):
    load_dotenv()
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
    app.config.from_object(env_config)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    with app.app_context():
        db.init_app(app)

    app.register_blueprint(select_api.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(scrape_api.bp)
    app.register_blueprint(db_mgmt_api.bp)
    app.register_blueprint(model_mgmt_api.bp)

    @app.route('/')
    def index():
        return redirect(url_for('admin.index'))

    return app
