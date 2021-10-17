import logging.config
import requests
import bs4
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select
import datetime
import re

from logging_config import LOGGING_CONFIG
from repositories.base import Base
from repositories.player import Player

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


def main():
    LOGGER.info("Starting PLAYER SCRAPE")
    engine = create_engine('postgresql://postgres:oscar12!@localhost:5432/tiplos?gssencmode=disable')
    Base.metadata.create_all(engine, checkfirst=True)
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
        players = process_row(first_row, headers, team, [])
        LOGGER.info(f'Found {len(players)} records for team: {team}. Upserting to database')
        upsert_team(team, players, engine)
    LOGGER.info("Finished PLAYER SCRAPE")


def process_row(row, headers, team, players):
    try:
        player_row = scrape_player(row)
        player = populate_player(player_row, headers, team)
    except ValueError as e:
        LOGGER.error(f'Exception processing row: {player_row}: {e}')
        player = None
    if player:
        players.append(player)
    next_row = row.findNext('tr')
    if len(next_row.select('.data')):
        process_row(next_row, headers, team, players)
    return players


def scrape_player(row):
    player_row = []
    for td in row.find_all('td'):
        [x.decompose() for x in td.select('.playerflag')]
        if td.find('a'):
            # get players name key from link
            player_row.append(td.find('a').attrs['href'].split('--')[1])
            continue
        player_row.append(td.text.strip())
    return player_row


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


def upsert_team(team, players, engine):
    session = sessionmaker(bind=engine)
    with session() as session:
        players_from_db = session.execute(select(Player).filter_by(team=team)).all()
        for player in players:
            if player.name_key is None or player.team is None or player.DOB is None:
                LOGGER.debug(f'Player is missing details required for persistance. doing nothing. Player: {player}')
                continue
            db_matches = [x[0] for x in players_from_db if player.name_key == x[0].name_key and player.DOB == x[0].DOB]
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
    main()
