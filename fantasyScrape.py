import requests
import bs4
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select

import sys
import datetime
import re
import os

import base
from player import Player
from injury import Injury
from playerFantasy import PlayerFantasy
from playerSupercoach import PlayerSupercoach

engine = create_engine('postgresql://postgres:oscar12!@localhost:5432/tiplos?gssencmode=disable')
base.Base.metadata.create_all(engine, checkfirst=True)

Session = sessionmaker(bind=engine)
session = Session()


def main():
    year = 2021
    # TODO: parameterise round / year / find current round based on date / call to footywire.
    for mode in ['dream_team', 'supercoach']:
        for round in range(1, 25):
            print(f'Scraping {mode} points for year: {year} and round {round}')
            url = f'https://www.footywire.com/afl/footy/{mode}_round?year={year}&round={round}&p=&s=T'
            res = requests.get(url)
            soup = bs4.BeautifulSoup(res.text, 'html.parser')
            try:
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
            except Exception as e:
                print(f'Failed to grab data for {year} round {round}. Exception was: {e}')
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                continue
            data_rows = scrape_rows(table)
            print(f'Found {len(data_rows)} fantasy records for {year}, round {round}')
            fantasies = []
            for row in data_rows:
                fantasies.append(populate_fantasy(mode, row, headers, year, round))
            insert_fantasies(mode, fantasies, year, round)
        

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
                        if re.match('^th', href):
                            fantasy_row.append('-'.join(href.split('?')[0].split('-')[1:]))
                            continue
                        if re.match('^p[ru]', href):
                            fantasy_row.append(href.split('--')[1])
                            continue
                    except KeyError:
                        print(f'Cannot scrape cell due to missing href in link: {d}')
                fantasy_row.append(d.text.strip().split('\n')[0])
        rows.append(fantasy_row)
    return rows


def populate_fantasy(mode, fantasy_row, headers, fantasy_year, fantasy_round):
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
            player = session.execute(select(Player).filter_by(team=team_name, name_key=value)).first()
            if player:
                fantasy.player_id = player[0].id
            else:
                print(f'no player for {fantasy_row}, {value}')
        elif key == 'rank':
            fantasy.round_ranking = value
        elif key == 'round_salary':
            fantasy.round_salary = value
        elif key == 'round_score':
            fantasy.round_score = value
        elif key == 'round_value':
            fantasy.round_value = value
    return fantasy


def insert_fantasies(mode, fantasies, fantasy_year, fantasy_round):
    fantasies_persisted = session.execute(select(PlayerFantasy if mode == 'dream_team' else PlayerSupercoach)
                                          .filter_by(year=fantasy_year, round=fantasy_round)).all()
    print(f'{len(fantasies_persisted)} Records already found in DB for {fantasy_year}, round {fantasy_round}')
    for fantasy in fantasies:
        if fantasy.player_id is None:
            print(f'Record is missing details required for persistance (player_id). doing nothing. Record: {fantasy}')
            continue
        db_match = [x[0] for x in fantasies_persisted
                    if fantasy.player_id == x[0].player_id
                    and fantasy.round == x[0].round
                    and fantasy.year == x[0].year]
        # just add the id to our obj, then merge, then commit session
        if db_match:
            fantasy.id = db_match[0].id
            continue  # do nothing
        session.add(fantasy)  # add only if new
    try:
        session.commit()
    except Exception as e:
        print(f'Could not commit fantasy: {fantasies} due to exception: {e} \n Rolling back')
        session.rollback()


if __name__ == '__main__':
    main()
