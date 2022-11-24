import datetime
import logging.config
import re
from os import getenv

import bs4
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from datascrape.logging_config import LOGGING_CONFIG
from datascrape.scrapers.BaseScraper import BaseScraper
from model.base import Base
from model.player import Player

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)

TEAMS = [
    'carlton-blues',
    'essendon-bombers',
    'western-bulldogs',
    'geelong-cats',
    'adelaide-crows',
    'melbourne-demons',
    'fremantle-dockers',
    'west-coast-eagles',
    'greater-western-sydney-giants',
    'hawthorn-hawks',
    'kangaroos',
    'brisbane-lions',
    'collingwood-magpies',
    'port-adelaide-power',
    'st-kilda-saints',
    'gold-coast-suns',
    'sydney-swans',
    'richmond-tigers'
]

PLAYER_HEADER_MAP = {
    'No': 'number',
    'Name': 'name',
    'Games': 'games',
    'Age': 'age',
    'Date of Birth': 'DOB',
    'Height': 'height',
    'Weight': 'weight',
    'Origin': 'origin',
    'Position': 'position'
}


class PlayerScraper(BaseScraper):

    def __init__(self, engine):
        super().__init__(engine, "Player")

    def scrape_entities(self):
        LOGGER.info("Starting PLAYER SCRAPE")
        Base.metadata.create_all(self.engine, checkfirst=True)
        player_count = 0
        for team in TEAMS:
            LOGGER.info(f'Processing players for {team}...')
            res = requests.get(f'https://www.footywire.com/afl/footy/tp-{team}')
            soup = bs4.BeautifulSoup(res.text, 'html.parser')
            data = soup.select('.data')
            # Get the first row
            first_row = data[0].parent
            # Mapping of field names in html table in index order
            headers = [x.text for x in first_row.findPrevious('tr').find_all('a')]
            # recursive function to continue through rows until they no longer have data children
            players = self.process_row(first_row, headers, team, [])
            LOGGER.info(f'Found {len(players)} records for team: {team}. Upserting to database')
            self.upsert_team(players, self.engine)
            player_count += len(players)
        LOGGER.info("Finished PLAYER SCRAPE")
        return player_count

    def process_row(self, row, headers, team, players):
        try:
            player_row = self.scrape_one_player(row)
            player = self.populate_player(player_row, headers, team)
        except ValueError as e:
            LOGGER.error(f'Exception processing row: {player_row}: {e}')
            player = None
        if player:
            players.append(player)
        next_row = row.findNext('tr')
        if len(next_row.select('.data')):
            self.process_row(next_row, headers, team, players)
        return players

    @staticmethod
    def scrape_one_player(row):
        player_row = []
        for td in row.find_all('td'):
            [x.decompose() for x in td.select('.playerflag')]
            if td.find('a'):
                # get players name key from link
                player_row.append(td.find('a').attrs['href'].split('--')[1])
                continue
            player_row.append(td.text.strip())
        return player_row

    @staticmethod
    def populate_player(player_row, headers, team):
        player = Player(None, team, None)
        player.updated_at = datetime.datetime.now()
        for i in range(len(player_row)):
            key = PLAYER_HEADER_MAP[headers[i]]
            value = player_row[i]
            if key == 'name':
                if value == '':
                    raise ValueError("Player row has no name")
                player.name_key = value
                player.first_name = value.split('-')[0].strip().title()
                player.last_name = " ".join(value.split('-')[1:]).strip().title()
            elif key == 'number':
                player.number = int(value) if value else None
            elif key == 'games':
                player.games = int(value) if value else None
            elif key == 'age':
                player.age = value
            elif key == 'DOB':
                if value == '' or value is None:
                    raise ValueError("Player row has no DateOfBirth")
                player.DOB = datetime.datetime.strptime(value, '%d %b %Y').date()
            elif key == 'height':
                player.height = int(re.sub("[^0-9]", "", value)) if value else None
            elif key == 'weight':
                player.weight = int(re.sub("[^0-9]", "", value)) if value else None
            elif key == 'position':
                player.position = value
        return player

    @staticmethod
    def upsert_team(players, engine):
        session = sessionmaker(bind=engine)
        with session() as session:
            for player in players:
                if player.name_key is None or player.team is None or player.DOB is None:
                    LOGGER.debug(f'Player is missing details required for persistance. doing nothing. Player: {player}')
                    continue
                db_matches = session.query(Player).filter_by(name_key=player.name_key, DOB=player.DOB).all()
                if len(db_matches) > 0:
                    # just add the id to our obj, then merge, then commit session
                    player.id = db_matches[0].id
                else:
                    LOGGER.debug(f'New player: {player.first_name} {player.last_name} will be added to DB')
                try:
                    session.merge(player)  # merge updates if id exists and adds new if it doesnt
                    session.commit()
                except Exception as e:
                    LOGGER.exception(f'Caught exception {e} \n'
                                     f'Rolling back {player}')
                    session.rollback()


if __name__ == '__main__':
    load_dotenv()
    db_engine = create_engine(getenv('DATABASE_URL'))
    PlayerScraper(db_engine).scrape()
