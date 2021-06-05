import requests
import bs4
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Date, DateTime, Sequence, UniqueConstraint
from sqlalchemy import create_engine
from sqlalchemy import update, select
import sys
import datetime
import re

import base
from player import Player
from injury import Injury

engine = create_engine('postgresql://postgres:oscar12!@localhost:5432/tiplos?gssencmode=disable')
base.Base.metadata.create_all(engine, checkfirst=True)

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
    'No':'number',
    'Name':'name',
    'Games':'games',
    'Age':'age',
    'Date of Birth':'DOB',
    'Height':'height',
    'Weight':'weight',
    'Origin':'origin',
    'Position':'position'
}

def main():
    for team in TEAMS:
        print(f'Processing players for {team}...')
        res = requests.get(f'https://www.footywire.com/afl/footy/tp-{team}')
        soup = bs4.BeautifulSoup(res.text,'html.parser')
        data = soup.select('.data')
        # Get the first row
        firstRow = data[0].parent
        #Mapping of field names in html table in index order

        headers = [x.text for x in firstRow.findPrevious('tr').find_all('a')]
        # recursive function to continue through rows until they no longer have data children
        players = process_row(firstRow,headers,team,[])
        print(f'Found {len(players)} records for team: {team}. Upserting to database')
        upsert_team(team,players)
        



def scrape_player(row):
    playerRow = []
    for td in row.find_all('td'):
        [ x.decompose() for x in td.select('.playerflag')]
        playerRow.append(td.text.strip())
    return playerRow

def populate_player(playerRow,headers,team):
    try:
        player = Player()
        player.team = team
        player.updated_at = datetime.datetime.now()
        for i in range(len(playerRow)):
            key = PLAYER_HEADER_MAP[headers[i]]
            value = playerRow[i]
            if key == 'name':
                if value == '':
                    raise Exception("Player row has no name")
                player.first_name = value.split(',')[1].strip()
                player.last_name = value.split(',')[0].strip()
            elif key == 'number':
                player.number = int(value) if value else None
            elif key == 'games':
                player.games = int(value) if value else None
            elif key == 'age':
                player.age = value
            elif key == 'DOB':
                if value == '' or value is None:
                    raise Exception("Player not initialised with DateOfBirth yet")
                player.DOB = datetime.datetime.strptime(value,'%d %b %Y').date()
            elif key == 'height':
                player.height = int(re.sub("[^0-9]","",value)) if value else None
            elif key == 'weight':
                player.weight = int(re.sub("[^0-9]","",value)) if value else None
            elif key == 'position':
                player.position = value
    except Exception as e:
        print(f'Exception processing row: {playerRow}: {e}')
        player = None
    return player

def process_row(row,headers,team,players):
    playerRow = scrape_player(row)
    player = populate_player(playerRow,headers,team)
    if player:
        players.append(player) 
    nextRow = row.findNext('tr')
    if len(nextRow.select('.data')):
        process_row(nextRow,headers,team,players)
    return players


def upsert_team(team,players):
    Session=sessionmaker(bind=engine)
    session = Session()
    playersFromDB = session.execute(select(Player).filter_by(team=team)).all()
    for player in players:
        if player.first_name is None or player.last_name is None or player.team is None or player.DOB is None:
            print(f'Player is missing details required for persistance. doing nothing. Player: {player}')
            continue
        dbMatches = [x[0] for x in playersFromDB if player.first_name == x[0].first_name and player.last_name == x[0].last_name and player.DOB == x[0].DOB]
        if len(dbMatches) > 0:
            # print(f'found {len(dbMatches)} matches for {player.first_name} {player.last_name}')
            # just add the id to our obj, then merge, then commit session
            player.id = dbMatches[0].id
        else:
            print(f'New player: {player.first_name} {player.last_name} will be added to DB')
        session.merge(player) #merge updates if id exists and adds new if it doesnt
    try:
        session.commit()
    except Exception as e:
        print(f'Could not commit for team: {team} due to exception: {e} \n Rolling back')
        session.rollback()
    finally:
        session.close()


if __name__ == '__main__':
    main()