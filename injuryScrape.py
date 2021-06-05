import requests
import bs4
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Sequence, UniqueConstraint
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update, select

import sys
import datetime
import re

import base
from player import Player
from injury import Injury

engine = create_engine('postgresql://postgres:oscar12!@localhost:5432/tiplos?gssencmode=disable')
base.Base.metadata.create_all(engine, checkfirst=True)

Session=sessionmaker(bind=engine)
session = Session()

HEADER_MAP = {
    'Player':'player',
    'Injury':'injury',
    'Returning':'returning',
}


TEAMS = {
    'Carlton Blues':'carlton-blues',
    'Essendon Bombers':'essendon-bombers',
    'Western Bulldogs':'western-bulldogs',
    'Geelong Cats':'geelong-cats',
    'Adelaide Crows':'adelaide-crows',
    'Melbourne Demons':'melbourne-demons',
    'Fremantle Dockers':'fremantle-dockers',
    'West Coast Eagles':'west-coast-eagles',
    'GWS Giants':'greater-western-sydney-giants',
    'Hawthorn Hawks':'hawthorn-hawks',
    'North Melbourne Kangaroos':'kangaroos',
    'Brisbane Lions':'brisbane-lions',
    'Collingwood Magpies':'collingwood-magpies',
    'Port Adelaide Power':'port-adelaide-power',
    'St Kilda Saints':'st-kilda-saints',
    'Gold Coast Suns':'gold-coast-suns',
    'Sydney Swans':'sydney-swans',
    'Richmond Tigers':'richmond-tigers',
}

def main():
    res = requests.get(f'https://www.footywire.com/afl/footy/injury_list')
    soup = bs4.BeautifulSoup(res.text,'html.parser')
    data = soup.select('.tbtitle')
    
    injuries = []
    for team in data:
        team_name = TEAMS[team.text.split('(')[0].strip()]
        print(f'Processing data for {team_name} ')
        #rows of team table including headers
        teamtable = team.parent.findNext('tr').findAll('tr')
        headers=[]
        for header in teamtable[0].findAll('td'):
            headers.append(header.text.strip())
        datarows = scrape_rows(teamtable)
        print(f'Found {len(datarows)} injuries for {team_name}')
        for injury in datarows:
            injuries.append(populate_injury(injury, team_name, headers))
    #persist all injuries in one go
    upsert_injuries(injuries)
    session.close()


def scrape_rows(teamtable):
    rows= []
    for row in teamtable[1:]:
        injuryRow = []
        for td in row.findAll('td'):
            injuryRow.append(td.text.strip())
        rows.append(injuryRow)
    return rows


def populate_injury(injuryRow, team_name, headers):
    injury = Injury()
    for i in range(len(injuryRow)):
        key = HEADER_MAP[headers[i]]
        value = injuryRow[i]
        injury.recovered = False
        injury.updated_at = datetime.datetime.now()
        if key == 'player':
            names = value.split()
            first_name=names[0].strip()
            last_name=" ".join(names[1:]).strip() if len(names) > 2 else names[1].strip()
            player = session.execute(select(Player).filter_by(team=team_name,first_name=first_name,last_name=last_name)).first()
            if player:
                injury.player_id = player[0].id
            else:
                print(f'no player for {injuryRow}, {first_name}, {last_name}')
        elif key == 'injury':
            injury.injury = value
        elif key == 'returning':
            injury.returning = value
    return injury


def upsert_injuries(injuryList):
    print(f'Upserting {len(injuryList)} records to database')
    injuriesPersisted = session.execute(select(Injury)).all()
    for injury in injuriesPersisted:
        #all are recovered unless they appear in the scrape results
        injury[0].recovered=True
    for injury in injuryList:
        dbMatch = [x[0] for x in injuriesPersisted if injury.player_id == x[0].player_id]
        # just add the id to our obj, then merge, then commit session
        if dbMatch:
            injury.id = dbMatch[0].id
        session.merge(injury) #merge updates if id exists and adds new if it doesnt
    try:
        session.commit()
    except Exception as e:
        print(f'Could not commit injury: {injury} due to exception: {e} \n Rolling back')
        session.rollback()



if __name__ == '__main__':
    main()