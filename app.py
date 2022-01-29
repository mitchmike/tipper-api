import os
from dotenv import load_dotenv
from flask import Flask, jsonify

from model.base import Base
from model.game import Game
from api.schema.game import GameSchema
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

import datascrape.scrapers.gameScrape as gameScrape

load_dotenv()
app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
Base.metadata.create_all(engine, checkfirst=True)


@app.route("/")
def index():
    secret_key = app.config.get("SECRET_KEY")
    return f"The configured secret key is {secret_key}."


@app.route("/games")
def select_games():
    session = sessionmaker(bind=engine)
    with session() as session:
        games = session.query(Game).all()
        games_schema = GameSchema(many=True)
        dump_data = games_schema.dump(games)
        return jsonify(dump_data)


@app.route("/scrape_games")
def trigger_scrape_games():
    return gameScrape.scrape_games(2021, 2021)


if __name__ == '__main__':
    app.run(debug=True)
