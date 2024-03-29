from os import getenv
from dotenv import load_dotenv
import logging.config

import requests
import bs4
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select

import sys
import datetime
import re
import os

from datascrape.logging_config import LOGGING_CONFIG
from datascrape.scrapers.BaseScraper import BaseScraper
from model.base import Base
from model.player import Player
from model.player_fantasy import PlayerFantasy
from model.player_supercoach import PlayerSupercoach

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)


class FantasyScraper(BaseScraper):

    def __init__(self, engine, from_year, to_year, from_round, to_round):
        super().__init__(engine, "Fantasy")
        self.from_year = from_year
        self.to_year = to_year
        self.from_round = from_round
        self.to_round = to_round

    def scrape_entities(self):
        LOGGER.info("Starting FANTASY SCRAPE")
        Base.metadata.create_all(self.engine, checkfirst=True)
        rows = 0
        for year in range(self.from_year, self.to_year + 1):
            for mode in ['dream_team', 'supercoach']:
                for round_number in range(self.from_round, self.to_round + 1):
                    LOGGER.info(f'Scraping {mode} points for year: {year} and round_number {round_number}')
                    url = f'https://www.footywire.com/afl/footy/{mode}_round?year={year}&round={round_number}&p=&s=T'
                    res = requests.get(url)
                    soup = bs4.BeautifulSoup(res.text, 'html.parser')
                    try:
                        table, headers = self.get_data_table(soup)
                    except Exception as e:
                        LOGGER.error(f'Failed to parse data for {year} round_number {round_number}. Exception was: {e}')
                        continue
                    data_rows = self.scrape_rows(table)
                    LOGGER.info(f'Found {len(data_rows)} fantasy records for {year}, round_number {round_number}')
                    rows += len(data_rows)
                    fantasies = []
                    for row in data_rows:
                        fantasies.append(self.populate_fantasy(mode, row, headers, year, round_number, self.engine))
                    self.insert_fantasies(mode, fantasies, year, round_number, self.engine)
        LOGGER.info("Finished FANTASY SCRAPE")
        return rows

    @staticmethod
    def get_data_table(soup):
        header_row = soup.select('.bnorm')[0].parent
        table = header_row.parent.contents
        table = [x for x in table if x != '\n']
        headers = []
        for header in header_row.findAll('td'):
            text = header.text.strip()
            if re.match('^20.*Salary', text):
                headers.append('round_salary')
            elif re.match('.*Score', text):
                headers.append('round_score')
            elif re.match('.*Value', text):
                headers.append('round_value')
            else:
                headers.append(text)
        return table, headers

    @staticmethod
    def scrape_rows(table):
        rows = []
        for row in table[1:]:
            fantasy_row = []
            for d in [x for x in row.children if x != '\n']:
                if d != '\n':
                    # dirty logic to get team and player names from links
                    if d.find('a'):
                        try:
                            href = d.find('a').attrs['href']
                            if re.match('^p[ru]', href):
                                fantasy_row.append(href.split('--')[1])
                                fantasy_row.append('-'.join(href.split('--')[0].split('-')[1:]))
                            continue
                        except KeyError:
                            LOGGER.warning(f'Cannot scrape cell due to missing href in link: {d}')
                    fantasy_row.append(d.text.strip().split('\n')[0])
            rows.append(fantasy_row)
        return rows

    @staticmethod
    def populate_fantasy(mode, fantasy_row, headers, fantasy_year, fantasy_round, engine):
        session = sessionmaker(bind=engine)
        fantasy = PlayerFantasy() if mode == 'dream_team' else PlayerSupercoach()
        fantasy.updated_at = datetime.datetime.now()
        fantasy.year = fantasy_year
        fantasy.round = fantasy_round
        # get team first so player lookup can occur
        team_name = ''
        for i in range(len(fantasy_row)):
            if headers[i].lower() == 'team':
                team_name = fantasy_row[i]
                break
        for i in range(len(fantasy_row)):
            key = headers[i].lower()
            value = fantasy_row[i]
            if key == 'player':
                with session() as session:
                    player = session.execute(select(Player).filter_by(team=team_name, name_key=value)).first()
                    if not player:
                        # try just the player name
                        player = session.execute(select(Player).filter_by(name_key=value)).first()
                        if not player:
                            LOGGER.debug(f'No player for {fantasy_row}, {value}')
                            continue
                    fantasy.player_id = player[0].id
            elif key == 'rank':
                fantasy.round_ranking = value
            elif key == 'round_salary':
                fantasy.round_salary = value
            elif key == 'round_score':
                fantasy.round_score = value
            elif key == 'round_value':
                fantasy.round_value = value
        return fantasy

    @staticmethod
    def insert_fantasies(mode, fantasies, fantasy_year, fantasy_round, engine):
        session = sessionmaker(bind=engine)
        with session() as commit_session:
            fantasies_persisted = commit_session.execute(select(PlayerFantasy if mode == 'dream_team' else PlayerSupercoach)
                                              .filter_by(year=fantasy_year, round=fantasy_round)).all()
            LOGGER.info(f'{len(fantasies_persisted)} Records already found in DB for {fantasy_year}, round {fantasy_round}')
            update_count = 0
            new_count = 0
            for fantasy in fantasies:
                if fantasy.player_id is None:
                    LOGGER.debug(f'Record is missing details required for persistence (player_id). Doing nothing. Record: {fantasy}')
                    continue
                db_match = [x[0] for x in fantasies_persisted
                            if fantasy.player_id == x[0].player_id
                            and fantasy.round == x[0].round
                            and fantasy.year == x[0].year]
                if db_match:
                    fantasy.id = db_match[0].id  # just add the id to our obj, then merge
                    update_count = update_count + 1
                else:
                    new_count = new_count + 1
                commit_session.merge(fantasy)
            try:
                LOGGER.info(f'Persisting fantasy data to db. new: {new_count}, updated: {update_count}')
                commit_session.commit()
            except Exception as e:
                LOGGER.exception(f'Could not commit fantasy: {fantasies} due to exception: {e} \n Rolling back')
                commit_session.rollback()


if __name__ == '__main__':
    load_dotenv()
    db_engine = create_engine(getenv('DATABASE_URL'))
    FantasyScraper(db_engine, 2021, 2021, 1, 24).scrape()
