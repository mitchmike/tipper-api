import os

from dotenv import load_dotenv
from flask import Flask, render_template

from tipperapi.route import auth
from tipperapi.route.admin import db_mgmt_api, model_mgmt_api, user_admin, scrape_api, admin_bp
from tipperapi.route.api import select_api, predict_api, ladder_api, api_bp
from tipperapi.route.app import app_bp, ladder, teamdetail, odds, profile, predict
from tipperapi.services.cache import cache


def create_app(test_config=None, testing=False):
    load_dotenv()
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig") if not testing else "config.TestConfig"
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

    app.jinja_env.filters["formatpcnt"] = format_pcnt

    app.register_blueprint(auth.bp)
    app.register_blueprint(admin_bp, cli_group=None)
    app.register_blueprint(api_bp)
    app.register_blueprint(app_bp)

    cache.init_app(app, config=app.config)

    # Ensure responses aren't cached
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

    @app.route('/')
    def index():
        return render_template("app/index.html")

    return app


def format_pcnt(value):
    return f"{value:,.2f}"