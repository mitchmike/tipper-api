import os
from dotenv import load_dotenv

from flask import Flask

from api.route import auth


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

    from api.route import select_api
    app.register_blueprint(select_api.bp)
    app.register_blueprint(auth.bp)

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app
