import datetime
import logging.config
import argparse
from os import getenv
from dotenv import load_dotenv
from sqlalchemy import create_engine

from datascrape.scrapers import *
from datascrape.util.latest_round import CALENDAR_DICT
from datascrape.util.latest_round import find_latest_round
from logging_config import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)


def run_full_scrape(from_year, to_year, from_round, to_round, engine):
    LOGGER.info("Starting Full DataScrape")
    playerScrape.scrape_players(engine)
    injuryScrape.scrape_injuries(engine)
    gameScrape.scrape_games(engine, from_year, to_year)
    fantasyScrape.scrape_fantasies(engine, from_year, to_year, from_round, to_round)
    match_statsScrape.scrape_match_stats(engine, from_year, to_year, from_round, to_round)
    LOGGER.info("Finished Full DataScrape")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrape AFL data")
    parser.add_argument('--from_year', help='scrape data from this year onwards',
                        type=int, choices=range(1990, datetime.datetime.now().year + 1), default=2021)
    parser.add_argument('--to_year', help='scrape data up until this year (inclusive)',
                        type=int, choices=range(1990, datetime.datetime.now().year + 1), default=datetime.datetime.now().year)
    parser.add_argument('--from_round', help='scrape data from this round onwards',
                        type=int, choices=range(1, 30), default=1)
    parser.add_argument('--to_round', help='scrape data up until this round (inclusive)',
                        type=int, choices=range(1, 30), default=30)
    parser.add_argument('-l', '--latest', help='scrape the latest data only', action="store_true")
    args = parser.parse_args()
    if args.latest:
        LOGGER.info("\"Latest\" flag provided: Ignoring any from/to arguments and scraping for the latest rounds")
        args.from_year = datetime.datetime.now().year
        args.to_year = datetime.datetime.now().year
        args.from_round = find_latest_round(CALENDAR_DICT, datetime.datetime.now())
        args.to_round = args.from_round
    load_dotenv()
    db_engine = create_engine(getenv('DATABASE_URL'))
    run_full_scrape(from_year=args.from_year, to_year=args.to_year, from_round=args.from_round, to_round=args.to_round,
                    engine=db_engine)
