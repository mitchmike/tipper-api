import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request

from api.schema.fantasy_schema import FantasySchema
from api.schema.match_stats_schema import MatchStatsSchema
from api.schema.supercoach_schema import SuperCoachSchema
from model import Player, PlayerFantasy, PlayerSupercoach, MatchStatsPlayer
from model.base import Base
from model.game import Game
from api.schema.player.player_injury import PlayerInjurySchema
from api.schema.game_schema import GameSchema
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, or_

import datascrape.scrapers.playerScrape as playerScrape
import datascrape.scrapers.injuryScrape as injuryScrape
import datascrape.scrapers.gameScrape as gameScrape
import datascrape.scrapers.fantasyScrape as fantasyScrape
import datascrape.scrapers.match_statsScrape as match_statsScrape

# load_dotenv()
# app = Flask(__name__)
# env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
# app.config.from_object(env_config)

# engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
# # session factory
# Session = sessionmaker(bind=engine)
# Base.metadata.create_all(engine, checkfirst=True)


@app.route("/")
def index():
    secret_key = app.config.get("SECRET_KEY")
    return f"The configured secret key is {secret_key}."





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
