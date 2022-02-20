from flask import Blueprint, g

from api import db
from datascrape.scrapers import playerScrape, gameScrape, injuryScrape, fantasyScrape, match_statsScrape

bp = Blueprint('scrape_api', __name__, url_prefix='/scrape')


@bp.before_app_request
def load_db():
    db.get_db()


@bp.route("/players")
def trigger_scrape_players():
    return playerScrape.scrape_players(g.engine)


@bp.route("/games")
def trigger_scrape_games():
    return gameScrape.scrape_games(g.engine, 2021, 2021)


@bp.route("/injuries")
def trigger_scrape_injuries():
    return injuryScrape.scrape_injuries(g.engine)


@bp.route("/fantasies")
def trigger_scrape_fantasies():
    return fantasyScrape.scrape_fantasies(g.engine, 2021, 2021, 1, 30)


@bp.route("/match_stats")
def trigger_scrape_match_stats():
    return match_statsScrape.scrape_match_stats(g.engine, 2021, 2021, 1, 30)
