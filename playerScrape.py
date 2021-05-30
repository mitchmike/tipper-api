import requests
import bs4
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Date, DateTime, Sequence, UniqueConstraint
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
import sys
import datetime
import re


engine = create_engine('postgresql://postgres:oscar12!@localhost:5432/tiplos?gssencmode=disable')

Base = declarative_base()
class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, Sequence('player_id_seq'), primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    number = Column(Integer)
    team = Column(String)
    games = Column(Integer)
    age = Column(String)
    DOB = Column(Date)
    height = Column(Integer)
    weight = Column(Integer)
    position = Column(String)
    updated_at = Column(DateTime)
    __table_args__ = (UniqueConstraint('first_name', 'last_name', 'number', 'team', name='uix_1'), )
    def __repr__(self):
        return "<Player(id='%s', number='%s', team='%s', \
first_name='%s', last_name='%s', games='%s', \
age='%s', DOB='%s', height='%s', weight='%s', \
position='%s')>" % (self.id, self.number, self.team, self.first_name, 
            self.last_name, self.games, self.age, self.DOB, self.height,
        self.weight, self.position)

Base.metadata.create_all(engine)


Session=sessionmaker(bind=engine)
session = Session()

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

def main():
    Session=sessionmaker(bind=engine)
    session = Session()
    for team in TEAMS:
        print(f'Processing players for {team}...')
        res = requests.get(f'https://www.footywire.com/afl/footy/tp-{team}')
        soup = bs4.BeautifulSoup(res.text,'html.parser')
        
        data = soup.select('.data')
        # first row
        row = data[0].parent
        # get headers
        #Mapping of fields in html table in index order
        headerMap = {
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
        headers = [x.text for x in row.findPrevious('tr').find_all('a')]
        # recursive function to continue through rows until they no longer have data children
        players=[]
        process_row(row)
        print(f'Found {len(players)} records for team: {team}. Upserting to database')
        for player in players:
            upsert_player(player)
        try:
            session.commit()
        except:
            session.rollback()


def scrape_player(row):
    playerRow = []
    for td in row.find_all('td'):
        [ x.decompose() for x in td.select('.playerflag')]
        playerRow.append(td.text.strip())
    return playerRow

def populate_player(playerRow):
    player = Player()
    player.team = team
    player.updated_at = datetime.datetime.now()
    for i in range(len(playerRow)):
        key = headerMap[headers[i]]
        value = playerRow[i]
        if key == 'name':
            player.first_name = value.split(',')[1].strip()
            player.last_name = value.split(',')[0].strip()
        elif key == 'number':
            player.number = int(value) if value else None
        elif key == 'games':
            player.games = int(value) if value else None
        elif key == 'age':
            player.age = value
        elif key == 'DOB':
            player.DOB = datetime.datetime.strptime(value,'%d %b %Y')
        elif key == 'height':
            player.height = int(re.sub("[^0-9]","",value)) if value else None
        elif key == 'weight':
            player.weight = int(re.sub("[^0-9]","",value)) if value else None
        elif key == 'position':
            player.position = value

    return player

def process_row(row):
    playerRow = scrape_player(row)
    player = populate_player(playerRow)
    players.append(player) 
    nextRow = row.findNext('tr')
    if len(nextRow.select('.data')):
        process_row(nextRow)


def upsert_player(player):
    #sqlite
    if 'sqlite' in str(engine.dialect):
        stmt = insert(Player).values(first_name=player.first_name,
                                     last_name=player.last_name,
                                     team=player.team,
                                     number=player.number,
                                     games=player.games,
                                     age=player.age,
                                     DOB=player.DOB,
                                     height=player.height,
                                     weight=player.weight,
                                     position=player.position,
                                     updated_at=player.updated_at
                                    ).on_conflict_do_update(
            index_elements=['first_name','last_name','team','number'],
                            set_=dict(first_name=player.first_name,
                                     last_name=player.last_name,
                                     team=player.team,
                                     number=player.number,
                                     games=player.games,
                                     age=player.age,
                                     DOB=player.DOB,
                                     height=player.height,
                                     weight=player.weight,
                                     position=player.position,
                                     updated_at=player.updated_at)
        )
    elif 'postgresql' in str(engine.dialect):
        #postgresql
        stmt = insert(Player).values(first_name=player.first_name,
                                     last_name=player.last_name,
                                     team=player.team,
                                     number=player.number,
                                     games=player.games,
                                     age=player.age,
                                     DOB=player.DOB,
                                     height=player.height,
                                     weight=player.weight,
                                     position=player.position,
                                     updated_at=player.updated_at
                                    ).on_conflict_do_update(
                            constraint='uix_1',
                            set_=dict(first_name=player.first_name,
                                     last_name=player.last_name,
                                     team=player.team,
                                     number=player.number,
                                     games=player.games,
                                     age=player.age,
                                     DOB=player.DOB,
                                     height=player.height,
                                     weight=player.weight,
                                     position=player.position,
                                     updated_at=player.updated_at)
        )
    return session.execute(stmt)


if __name__ == '__main__':
    main()