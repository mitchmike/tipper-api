import os
from dotenv import load_dotenv
from flask import Flask, jsonify

from model.base import Base
from model.game import Game
from api.schema.game import GameSchema
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

import datascrape.scrapers.playerScrape as playerScrape
import datascrape.scrapers.injuryScrape as injuryScrape
import datascrape.scrapers.gameScrape as gameScrape
import datascrape.scrapers.fantasyScrape as fantasyScrape
import datascrape.scrapers.match_statsScrape as match_statsScrape

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


@app.route("/games/<string:team>")
def select_games_by_team(team):
    session = sessionmaker(bind=engine)
    with session() as session:
        games = session.query(Game).filter_by(home_team=team).all()
        games_schema = GameSchema(many=True)
        dump_data = games_schema.dump(games)
        return jsonify(dump_data)


@app.route("/games/<int:game_id>")
def select_games_by_id(game_id):
    session = sessionmaker(bind=engine)
    with session() as session:
        games = session.query(Game).filter_by(id=game_id).all()
        games_schema = GameSchema(many=True)
        dump_data = games_schema.dump(games)
        return jsonify(dump_data)


@app.route("/scrape_players")
def trigger_scrape_players():
    return playerScrape.scrape_players(engine)


@app.route("/scrape_games")
def trigger_scrape_games():
    return gameScrape.scrape_games(engine, 2021, 2021)


@app.route("/scrape_injuries")
def trigger_scrape_injuries():
    return injuryScrape.scrape_injuries(engine)


@app.route("/scrape_fantasies")
def trigger_scrape_fantasies():
    return fantasyScrape.scrape_fantasies(engine, 2021, 2021, 1, 30)


@app.route("/scrape_match_stats")
def trigger_scrape_match_stats():
    return match_statsScrape.scrape_match_stats(engine, 2021, 2021, 1, 30)


if __name__ == '__main__':
    app.run(debug=True)
