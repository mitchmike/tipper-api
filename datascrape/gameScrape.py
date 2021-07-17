import requests
import bs4

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime

from datascrape.repositories.base import Base
from datascrape.repositories.game import Game


def main():
    engine = create_engine('postgresql://postgres:oscar12!@localhost:5432/tiplos?gssencmode=disable')
    Base.metadata.create_all(engine, checkfirst=True)

    year = '2021'
    res = requests.get(f'https://www.footywire.com/afl/footy/ft_match_list?year={year}')
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    data = soup.select('.data')
    # Get the first row
    first_row = data[0].parent
    # Mapping of field names in html table in index order
    headers = [x.text.split('\n')[0].strip() for x in first_row.findPrevious('tr').find_all(['td','th'])]
    # recursive function to continue through rows until they no longer have data children
    games = process_row(first_row, headers, [], year, 1)
    upsert_games(games, year, engine)


def process_row(row, headers, games, year, round_number):
    if len(row.select('.data')): #data row
        try:
            game_row = scrape_game(row)
            game = populate_game(game_row, headers, year, round_number)
        except ValueError as e:
            print(f'Exception processing row: {game_row}: {e}')
            game = None
        if game:
            games.append(game)
    elif len(row.select('.tbtitle')): #round header
        round_number = int(row.select('.tbtitle')[0].text.strip().split()[1])
    next_row = row.findNext('tr')
    if next_row:
        process_row(next_row, headers, games, year, round_number)
    return games


def scrape_game(row):
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
                print('Unexpected number/format of links found in td - please check data source '
                      f'- appending raw text from cell {td}')
                game_row.append(td.text.strip())
            continue
        game_row.append(td.text.strip())
    return game_row


def populate_game(game_row, headers, year, round_number):
    game = Game()
    game.year = year
    game.round = round_number
    game.updated_at = datetime.datetime.now()
    for i in range(len(game_row)):
        key = headers[i]
        value = game_row[i]
        if key == 'Date':
            if value:
                game.date_time = datetime.datetime.strptime(value + year, '%a %d %b %I:%M%p%Y')
        elif key == 'Home v Away Teams':
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
                game.id = value[0]
                game.home_score = value[1]
                game.away_score = value[2]
            else:
                print(f'Game has not happened yet {game}. ignoring as we have no results.')
                return None
        elif key == 'Disposals':
            #Not interested in this field
            None
        elif key == 'Goals':
            # Not interested in this field
            None
    return game


def upsert_games(games, year, engine):
    print(f'Upserting {len(games)} game(s) to the database')
    Session = sessionmaker(bind=engine)
    with Session() as session:
        # games_from_db = session.execute(select(Game).filter_by(year=year)).all()
        for game in games:
            if game.id is None or game.home_team is None or game.away_team is None:
                print(f'Game is missing details required for persistance. doing nothing. Game: {game}')
                continue

            print(f'New game: year: {game.year}, round: {game.round}, {game.home_team} v {game.away_team} '
                  f'will be added to DB')
            try:
                session.merge(game)
                session.commit()
            except Exception as e:
                print(f'Caught exception {e} \n'
                      f'Rolling back {game}')
                session.rollback()


if __name__ == '__main__':
    main()
