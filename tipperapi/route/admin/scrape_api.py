from flask import Blueprint, render_template, flash, redirect, url_for, request, g
from sqlalchemy import desc

from tipperapi.db import new_session
from tipperapi.route.auth import admin_required
from tipperapi.route.admin.db_mgmt_api import safe_int
from datascrape.scrapers.fantasyScrape import FantasyScraper
from datascrape.scrapers.gameScrape import GameScraper
from datascrape.scrapers.injuryScrape import InjuryScraper
from datascrape.scrapers.match_statsScrape import MatchStatsScraper
from datascrape.scrapers.playerScrape import PlayerScraper
from model.scrape_event import ScrapeEvent

bp = Blueprint('scrape_api', __name__, url_prefix='/scrape')


@bp.route("/")
@admin_required
def scrape_management():
    with new_session() as session:
        data = session.query(ScrapeEvent)
        data = data.order_by(desc('start_time')).limit(50).all()
    return render_template('admin/scraper_management.html', scrape_events=data)


@bp.route("/players")
@admin_required
def trigger_scrape_players():
    return scrape_data(PlayerScraper(g.engine))


@bp.route("/games")
@admin_required
def trigger_scrape_games():
    from_year, to_year = get_req_params(['from_year', 'to_year'])
    if None in [from_year, to_year]:
        flash('Scrape not started. Must supply all fields')
        return redirect(url_for('admin.scrape_api.scrape_management'))
    return scrape_data(GameScraper(g.engine, int(from_year), int(to_year)))


@bp.route("/injuries")
@admin_required
def trigger_scrape_injuries():
    return scrape_data(InjuryScraper(g.engine))


@bp.route("/fantasies")
@admin_required
def trigger_scrape_fantasies():
    from_year, to_year, from_round, to_round = get_req_params(['from_year', 'to_year', 'from_round', 'to_round'])
    if None in [from_year, to_year, from_round, to_round]:
        flash('Scrape not started. Must supply all fields')
        return redirect(url_for('admin.scrape_api.scrape_management'))
    return scrape_data(FantasyScraper(g.engine, int(from_year), int(to_year), int(from_round), int(to_round)))


@bp.route("/match_stats")
@admin_required
def trigger_scrape_match_stats():
    from_year, to_year, from_round, to_round = get_req_params(['from_year', 'to_year', 'from_round', 'to_round'])
    if None in [from_year, to_year, from_round, to_round]:
        flash('Scrape not started. Must supply all fields')
        return redirect(url_for('admin.scrape_api.scrape_management'))
    return scrape_data(MatchStatsScraper(g.engine, from_year, to_year, from_round, to_round))


def get_req_params(params):
    result = []
    for param in params:
        result.append(safe_int(request.args.get(param)))
    return result


def scrape_data(clazz):
    result = clazz.scrape()
    if result:
        flash('Scrape successful')
    else:
        flash('Scrape failed')
    return redirect(url_for('admin.scrape_api.scrape_management'))
