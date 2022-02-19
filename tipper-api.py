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
        games = session.query(Game)
        for key in request.args.keys():
            value = request.args.get(key)
            if key == 'id':
                games = games.filter_by(id=value)
            elif key == 'team':
                games = games.filter(or_(Game.home_team == value, Game.away_team == value))
            elif key == 'home_team':
                games = games.filter_by(home_team=value)
            elif key == 'away_team':
                games = games.filter_by(away_team=value)
            elif key == 'year':
                games = games.filter_by(year=value)
        games = games.order_by('year', 'round_number').all()
        games_schema = GameSchema(many=True)
        dump_data = games_schema.dump(games)
        return jsonify(dump_data)


@app.route("/players")
def select_players():
    session = sessionmaker(bind=engine)
    with session() as session:
        players = session.query(Player)
        for key in request.args.keys():
            value = request.args.get(key)
            if key == 'id':
                players = players.filter_by(id=value)
            elif key == 'team':
                players = players.filter_by(team=value)
        players = players.order_by('team', 'number').all()
        players_schema = PlayerInjurySchema(many=True)
        dump_data = players_schema.dump(players)
        return jsonify(dump_data)


@app.route("/player_points")
def select_supercoach():
    available_modes = ['supercoach', 'fantasy']
    mode = request.args.get('mode')
    if mode not in available_modes:
        return f"Required argument 'mode' is not valid. valid values: {available_modes}", 400
    session = sessionmaker(bind=engine)
    with session() as session:
        model = PlayerSupercoach if mode == 'supercoach' else PlayerFantasy
        data = session.query(model)
        for key in request.args.keys():
            value = request.args.get(key)
            if key == 'id':
                data = data.filter_by(id=value)
            if key == 'round':
                data = data.filter_by(round=value)
            if key == 'year':
                data = data.filter_by(year=value)
            if key == 'team':
                data = data.filter(model.player.has(team=value))
            if key == 'name_key':
                data = data.filter(model.player.has(name_key=value))
        data = data.order_by('year', 'round').all()
        schema = SuperCoachSchema(many=True) if mode == 'supercoach' else FantasySchema(many=True)
        dump_data = schema.dump(data)
        return jsonify(dump_data)


@app.route("/match_stats")
def select_matchstats():
    required_param_opts = ['id', 'game_id']
    accept_request = False
    for opt in required_param_opts:
        if opt in request.args:
            accept_request = True
            break
    if not accept_request:
        return f"Endpoint requires at least one of the following request params: {required_param_opts}"
    session = sessionmaker(bind=engine)
    with session() as session:
        data = session.query(MatchStatsPlayer)
        for key in request.args.keys():
            value = request.args.get(key)
            if key == 'id':
                data = data.filter_by(id=value)
            elif key == 'team':
                data = data.filter_by(team=value)
            elif key == 'game_id':
                data = data.filter_by(game_id=value)
        data = data.order_by('id').all()
        schema = MatchStatsSchema(many=True)
        dump_data = schema.dump(data)
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
