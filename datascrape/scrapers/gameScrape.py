from os import getenv
from dotenv import load_dotenv
import requests
import bs4
import logging.config

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select
import datetime

from datascrape.logging_config import LOGGING_CONFIG
from datascrape.scrapers.BaseScraper import BaseScraper
from model.base import Base
from model.game import Game

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)

FINAL_ROUNDS = {
    'qualifying final': 50,
    'elimination final': 51,
    'semi final': 52,
    'preliminary final': 53,
    'grand final': 54
}


class GameScraper(BaseScraper):

    def __init__(self, engine, from_year, to_year):
        super().__init__(engine, "Game")
        self.from_year = from_year
        self.to_year = to_year

    def scrape_entities(self):
        LOGGER.info("Starting GAME SCRAPE")
        Base.metadata.create_all(self.engine, checkfirst=True)
        games = []
        for year in range(self.from_year, self.to_year + 1):
            year_start = datetime.datetime.now()
            LOGGER.info(f'Processing games from footywire for year: {year}')
            res = requests.get(f'https://www.footywire.com/afl/footy/ft_match_list?year={year}')
            soup = bs4.BeautifulSoup(res.text, 'html.parser')
            data = soup.select('.data')
            # Get the first row
            first_row = data[0].parent
            # Mapping of field names in html table in index order
            headers = [x.text.split('\n')[0].strip() for x in first_row.findPrevious('tr').find_all(['td', 'th'])]
            # recursive function to continue through rows until they no longer have data children
            games = self._process_row(first_row, headers, games, year, 1)
            self._upsert_games(games, self.engine)
            LOGGER.info(f'Time taken: {datetime.datetime.now() - year_start}')
        LOGGER.info("Finished GAME SCRAPE")
        return len(games)

    def _process_row(self, row, headers, games, year, round_number):
        if len(row.select('.data')):  # data row
            try:
                game_row = self._scrape_one_game(row)
                game = self._populate_game(game_row, headers, year, round_number)
            except ValueError as e:
                LOGGER.exception(f'Exception processing row: {game_row}: {e}')
                game = None
            if game:
                games.append(game)
        elif len(row.select('.tbtitle')):  # round header
            round_string = row.select('.tbtitle')[0].text.strip()
            if 'final' in round_string.lower():
                try:
                    round_number = FINAL_ROUNDS[round_string.lower()]
                except KeyError as e:
                    LOGGER.exception(e)
            else:
                round_number = int(row.select('.tbtitle')[0].text.strip().split()[1])
        next_row = row.findNext('tr')
        if next_row:
            self._process_row(next_row, headers, games, year, round_number)
        return games

    @staticmethod
    def _scrape_one_game(row):
        game_row = []
        for td in row.find_all('td'):
            links = td.find_all('a')
            if links:
                # multiple links is teams
                if len(links) == 2 and 'th' in links[0].attrs['href']:
                    game_row.append([x.attrs['href'].split('th-')[1].strip() for x in links])
                # single link is result (with gameid)
                elif len(links) == 1 and 'mid' in links[0].attrs['href']:
                    id_score = [x.attrs['href'].split('mid=')[1] for x in links]
                    for score in td.text.split('-'):
                        id_score.append(score.strip())
                    game_row.append(id_score)
                elif 'ft' in links[0].attrs['href']:
                    # ignore player links in table
                    game_row.append(td.text.strip())
                else:
                    # no matching link structure - just append raw text
                    game_row.append(td.text.strip())
                continue
            game_row.append(td.text.strip())
        return game_row

    @staticmethod
    def _populate_game(game_row, headers, year, round_number):
        game = Game(None, None, None, year, round_number)
        game.updated_at = datetime.datetime.now()
        for i in range(len(game_row)):
            key = headers[i]
            value = game_row[i]
            if key == 'Date':
                if value:
                    try:
                        game.date_time = datetime.datetime.strptime(value + str(year), '%a %d %b %I:%M%p%Y')
                    except ValueError:
                        LOGGER.warning(f'Unexpected date format for value: {value}, expected like Fri 26 Mar 7:45pm')
            elif key == 'Home v Away Teams':
                if type(value) == list:
                    game.home_team = value[0]
                    game.away_team = value[1]
            elif key == 'Venue':
                if value == 'BYE':
                    return None
                game.venue = value
            elif key == 'Crowd':
                if value:
                    game.crowd = int(value)
            elif key == 'Result':
                if len(value) == 3:
                    game.id = int(value[0])
                    game.home_score = int(value[1])
                    game.away_score = int(value[2])
                else:
                    # Game has not happened yet - ignoring as we have no results.
                    return None
            elif key == 'Disposals':
                # Not interested in this field
                None
            elif key == 'Goals':
                # Not interested in this field
                None
        # add winner after all fields populated
        if game.home_score > game.away_score:
            game.winner = game.home_team
        elif game.home_score < game.away_score:
            game.winner = game.away_team
        else:
            game.winner = 'DRAW'
        return game

    @staticmethod
    def _upsert_games(games, engine):
        LOGGER.info(f'Upserting {len(games)} game(s) to the database')
        session = sessionmaker(bind=engine)
        with session() as session:
            for game in games:
                if game.id is None or game.home_team is None or game.away_team is None:
                    LOGGER.warning(f'Game is missing details required for persistance. doing nothing. Game: {game}')
                    continue
                if not session.execute(select(Game).filter_by(id=game.id)).first():
                    LOGGER.info(
                        f'New game: year: {game.year}, round: {game.round_number}, {game.home_team} v {game.away_team} '
                        f'will be added to DB')
                try:
                    session.merge(game)
                    session.commit()
                except Exception as e:
                    LOGGER.exception(f'Caught exception {e} \n'
                                     f'Rolling back {game}')
                    session.rollback()


if __name__ == '__main__':
    start_all = datetime.datetime.now()
    load_dotenv()
    db_engine = create_engine(getenv('DATABASE_URL'))
    GameScraper(db_engine, 2021, 2021).scrape()
    LOGGER.info(f'Total time taken: {datetime.datetime.now() - start_all}')
