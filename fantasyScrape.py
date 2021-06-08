import requests
import bs4
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, Float, String, Date, DateTime, Boolean, Sequence, UniqueConstraint, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import MONEY
from sqlalchemy import update, select

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


Session=sessionmaker(bind=engine)
session = Session()

def main():
    year=2021
    # TODO: parameterise round / year / find current round based on date / call to footywire.
    for mode in ['dream_team','supercoach']:
        for round in range(1,25):
            print(f'Scraping {mode} points for year: {year} and round {round}')
            url=f'https://www.footywire.com/afl/footy/{mode}_round?year={year}&round={round}&p=&s=T'
            res = requests.get(url)
            soup = bs4.BeautifulSoup(res.text,'html.parser')
            try:
                headerRow = soup.select('.bnorm')[0].parent
                table = headerRow.parent.contents
                table = [x for x in table if x != '\n']
                headers = []
                for header in headerRow.findAll('td'):
                    text = header.text.strip()
                    if re.match('^20.*Salary',text):
                        headers.append('round_salary')
                    elif re.match('.*Score',text):
                        headers.append('round_score')
                    elif re.match('.*Value',text):
                        headers.append('round_value')
                    else:
                        headers.append(text)
            except Exception as e:
                print(f'Failed to grab data for {year} round {round}. Exception was: {e}')
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                continue
            datarows = scrape_rows(table)
            print(f'Found {len(datarows)} fantasy records for {year}, round {round}')
            fantasies = []
            for row in datarows:
                fantasies.append(populate_fantasy(mode, row, headers, year, round))
            insert_fantasies(mode, fantasies, year, round)
        


def scrape_rows(table):
    rows = []
    for row in table[1:]:
        fantasyRow = []
        for d in [x for x in row.children if x != '\n']:
            if d != '\n':
                #dirty logic to get team and player names from links
                if (d.find('a')):
                    try:
                        href = d.find('a').attrs['href']
                        if (re.match('^th',href)):
                            fantasyRow.append('-'.join(href.split('?')[0].split('-')[1:]))
                            continue
                        if (re.match('^p[ru]',href)):
                            fantasyRow.append(href.split('--')[1])
                            continue
                    except KeyError:
                        print(f'Cannot scrape cell due to missing href in link: {d}')
                fantasyRow.append(d.text.strip().split('\n')[0])
        rows.append(fantasyRow)
    return rows

def populate_fantasy(mode, fantasyRow, headers, year, round):
    fantasy = PlayerFantasy() if mode == 'dream_team' else PlayerSupercoach()
    fantasy.updated_at = datetime.datetime.now()
    fantasy.year = year
    fantasy.round= round
    # get team first so player lookup can occur
    for i in range(len(fantasyRow)):
        if headers[i].lower() == 'team':
            team_name = fantasyRow[i]
            break
    for i in range(len(fantasyRow)):
        key = headers[i].lower()
        value = fantasyRow[i]
        if key == 'player':
            player = session.execute(select(Player).filter_by(team=team_name,name_key=value)).first()
            if player:
                fantasy.player_id = player[0].id
            else:
                print(f'no player for {fantasyRow}, {value}')
        elif key == 'rank':
            fantasy.round_ranking = value
        elif key == 'round_salary':
            fantasy.round_salary = value
        elif key == 'round_score':
            fantasy.round_score = value
        elif key == 'round_value':
            fantasy.round_value = value
    return fantasy


def insert_fantasies(mode, fantasies, year, round):
    fantasiesPersisted = session.execute(select(PlayerFantasy if mode == 'dream_team' else PlayerSupercoach).filter_by(year = year, round = round)).all()
    print(f'{len(fantasiesPersisted)} Records already found in DB for {year}, round {round}')
    for fantasy in fantasies:
        if fantasy.player_id is None:
            print(f'Record is missing details required for persistance (player_id). doing nothing. Record: {fantasy}')
            continue
        dbMatch = [x[0] for x in fantasiesPersisted if fantasy.player_id == x[0].player_id and fantasy.round == x[0].round and fantasy.year == x[0].year ]
        # just add the id to our obj, then merge, then commit session
        if dbMatch:
            fantasy.id = dbMatch[0].id
            continue #do nothing
        session.add(fantasy) #add only if new
    try:
        session.commit()
    except Exception as e:
        print(f'Could not commit fantasy: {fantasy} due to exception: {e} \n Rolling back')
        session.rollback()


if __name__ == '__main__':
    main()