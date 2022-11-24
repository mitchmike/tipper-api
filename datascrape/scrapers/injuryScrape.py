from os import getenv
from dotenv import load_dotenv
import logging.config

import requests
import bs4
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select

import datetime

from datascrape.logging_config import LOGGING_CONFIG
from datascrape.scrapers.BaseScraper import BaseScraper
from model.base import Base
from model.player import Player
from model.injury import Injury

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)

HEADER_MAP = {
    'Player': 'player',
    'Injury': 'injury',
    'Returning': 'returning',
}

TEAMS = {
    'Carlton Blues': 'carlton-blues',
    'Essendon Bombers': 'essendon-bombers',
    'Western Bulldogs': 'western-bulldogs',
    'Geelong Cats': 'geelong-cats',
    'Adelaide Crows': 'adelaide-crows',
    'Melbourne Demons': 'melbourne-demons',
    'Fremantle Dockers': 'fremantle-dockers',
    'West Coast Eagles': 'west-coast-eagles',
    'GWS Giants': 'greater-western-sydney-giants',
    'Hawthorn Hawks': 'hawthorn-hawks',
    'North Melbourne Kangaroos': 'kangaroos',
    'Brisbane Lions': 'brisbane-lions',
    'Collingwood Magpies': 'collingwood-magpies',
    'Port Adelaide Power': 'port-adelaide-power',
    'St Kilda Saints': 'st-kilda-saints',
    'Gold Coast Suns': 'gold-coast-suns',
    'Sydney Swans': 'sydney-swans',
    'Richmond Tigers': 'richmond-tigers',
}


class InjuryScraper(BaseScraper):

    def __init__(self, engine):
        super().__init__(engine, "Injury")

    def scrape_entities(self):
        LOGGER.info("Starting INJURY SCRAPE")
        Base.metadata.create_all(self.engine, checkfirst=True)
        res = requests.get(f'https://www.footywire.com/afl/footy/injury_list')
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        data = soup.select('.tbtitle')

        injuries = []
        for team in data:
            team_name = TEAMS[team.text.split('(')[0].strip()]
            LOGGER.info(f'Processing data for {team_name} ')
            # rows of team table including headers
            team_table = team.parent.findNext('tr').findAll('tr')
            headers = []
            for header in team_table[0].findAll('td'):
                headers.append(header.text.strip())
            data_rows = self.scrape_rows(team_table)
            LOGGER.info(f'Found {len(data_rows)} injuries for {team_name}')
            for injury in data_rows:
                injuries.append(self.populate_injury(injury, team_name, headers, self.engine))
        # persist all injuries in one go
        self.upsert_injuries(injuries, self.engine)
        LOGGER.info("Finished INJURY SCRAPE")
        return len(injuries)

    @staticmethod
    def scrape_rows(team_table):
        rows = []
        for row in team_table[1:]:
            injury_row = []
            for td in row.findAll('td'):
                if td.find('a'):
                    # name_key from link
                    injury_row.append(td.find('a').attrs['href'].split('--')[1])
                else:
                    injury_row.append(td.text.strip())
            rows.append(injury_row)
        return rows

    @staticmethod
    def populate_injury(injury_row, team_name, headers, engine):
        session = sessionmaker(bind=engine)
        injury = Injury()
        for i in range(len(injury_row)):
            key = HEADER_MAP[headers[i]]
            value = injury_row[i]
            injury.recovered = False
            injury.updated_at = datetime.datetime.now()
            if key == 'player':
                with session() as session:
                    player = session.execute(select(Player).filter_by(team=team_name, name_key=value)).first()
                    if player:
                        injury.player_id = player[0].id
                    else:
                        LOGGER.info(f'no player for {injury_row}, {value}')
            elif key == 'injury':
                injury.injury = value
            elif key == 'returning':
                injury.returning = value
        return injury

    @staticmethod
    def upsert_injuries(injury_list, engine):
        session = sessionmaker(bind=engine)
        LOGGER.info(f'Upserting {len(injury_list)} records to database')
        with session() as upsert_session:
            injuries_persisted = upsert_session.execute(select(Injury)).all()
            for injury in injuries_persisted:
                # all are recovered unless they appear in the scrape results
                injury[0].recovered = True
            for injury in injury_list:
                db_match = [x[0] for x in injuries_persisted if injury.player_id == x[0].player_id]
                # just add the id to our obj, then merge, then commit session
                if db_match:
                    injury.id = db_match[0].id
                upsert_session.merge(injury)  # merge updates if id exists and adds new if it doesnt
            try:
                upsert_session.commit()
            except Exception as e:
                LOGGER.exception(f'Could not commit injuries: {injury_list} due to exception: {e} \n Rolling back')
                upsert_session.rollback()


if __name__ == '__main__':
    load_dotenv()
    db_engine = create_engine(getenv('DATABASE_URL'))
    InjuryScraper(db_engine).scrape()
