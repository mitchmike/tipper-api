from flask import Blueprint, g, render_template, flash, redirect, url_for, request

from api import db
from api.route.auth import admin_required
from api.route.select_api import select_data
from datascrape.scrapers.fantasyScrape import FantasyScraper
from datascrape.scrapers.gameScrape import GameScraper
from datascrape.scrapers.injuryScrape import InjuryScraper
from datascrape.scrapers.match_statsScrape import MatchStatsScraper
from datascrape.scrapers.playerScrape import PlayerScraper
from model.scrape_event import ScrapeEvent

bp = Blueprint('scrape_api', __name__, url_prefix='/scrape')


@bp.before_app_request
def load_db():
    db.get_db()


@bp.route("/")
def scrape_management():
    data = select_data(ScrapeEvent, ())
    data = data.order_by('start_time').limit(50).all()
    data.reverse()
    return render_template('admin/scraper/scraper_management.html', scrape_events=data)


@bp.route("/players")
@admin_required
def trigger_scrape_players():
    return scrape_data(PlayerScraper(g.engine))


@bp.route("/games")
@admin_required
def trigger_scrape_games():
    from_year = request.args.get('from_year', default=2021)
    to_year = request.args.get('to_year', default=2021)
    return scrape_data(GameScraper(g.engine, int(from_year), int(to_year)))


@bp.route("/injuries")
@admin_required
def trigger_scrape_injuries():
    return scrape_data(InjuryScraper(g.engine))


@bp.route("/fantasies")
@admin_required
def trigger_scrape_fantasies():
    from_year = request.args.get('from_year', default=2021)
    to_year = request.args.get('to_year', default=2021)
    from_round = request.args.get('from_round', default=1)
    to_round = request.args.get('to_round', default=1)
    return scrape_data(FantasyScraper(g.engine, int(from_year), int(to_year), int(from_round), int(to_round)))


@bp.route("/match_stats")
@admin_required
def trigger_scrape_match_stats():
    from_year = request.args.get('from_year', default=2021)
    to_year = request.args.get('to_year', default=2021)
    from_round = request.args.get('from_round', default=1)
    to_round = request.args.get('to_round', default=1)
    return scrape_data(MatchStatsScraper(g.engine, int(from_year), int(to_year), int(from_round), int(to_round)))


def scrape_data(clazz):
    result = clazz.scrape()
    if result:
        flash('Scrape successful')
    else:
        flash('Scrape failed')
    return redirect(url_for('scrape_api.scrape_management'))
