import threading

import requests
import bs4
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select
import datetime
import queue
from threading import Thread

from datascrape.repositories.base import Base
from datascrape.repositories.player import Player
from datascrape.repositories.game import Game
from datascrape.repositories.milestone import Milestone
from datascrape.repositories.match_stats_player import MatchStatsPlayer

engine = create_engine('postgresql://postgres:oscar12!@localhost:5432/tiplos?gssencmode=disable')
Session = sessionmaker(bind=engine)
milestone_session = Session()
run_id = round(datetime.datetime.now().timestamp() * 1000)
request_q = queue.Queue()
response_q = queue.Queue()


def create_request_queue():
    year = 2021
    for round_number in range(60):
        with Session() as games_session:
            # get match ids for year / round
            matches = games_session.execute(select(Game.id).filter_by(year=year, round_number=round_number)).scalars().all()
            for match_id in matches:
                for mode in ['basic', 'advanced']:  # advanced stats on 2nd link
                    request_q.put({'year': year, 'round_number': round_number,
                                   'match_id': match_id, 'mode': mode,
                                   'url': None, 'response': None})


def send_request():  # need to run on threads
    while not len(request_q.queue) == 0:  # request q is complete
        req = request_q.get()
        if req['mode'] == 'basic':
            req_url = f"https://www.footywire.com/afl/footy/ft_match_statistics?mid={req['match_id']}"
        else:
            req_url = f"https://www.footywire.com/afl/footy/ft_match_statistics?mid={req['match_id']}&advv=Y"
        req['url'] = req_url
        print(f'Thread {threading.get_ident()}: sending req: {req_url}')
        add_milestone(req['match_id'], req['mode'], f"request_start")
        req['res'] = requests.get(req_url)
        print(f'Thread {threading.get_ident()}: got response for {req_url}')
        add_milestone(req['match_id'], req['mode'], f"request_finish")
        response_q.put(req)
        request_q.task_done()


def main():
    Base.metadata.create_all(engine, checkfirst=True)
    create_request_queue()  # synchronously create list of urls
    threads = 10
    for i in range(threads):
        t = Thread(target=send_request)  # async create threads for sending requests
        t.daemon = True
        t.start()
    # pick up responses and synchronously process them
    while True:
        response = response_q.get()
        process_response(response)
        response_q.task_done()
        if len(request_q.queue) == 0 and len(response_q.queue) == 0:
            break
    milestone_session.commit()
    milestone_session.close()


def process_response(res_obj):
    year = res_obj['year']
    round_number = res_obj['round_number']
    match_id = res_obj['match_id']
    mode = res_obj['mode']
    url = res_obj['url']
    res = res_obj['res']
    add_milestone(match_id, mode, f"match_start")
    print(f'Scraping match stats for year: {year}, round: {round_number}, match: {match_id}, url: {url}')
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    for i in [0, 1]:  # both teams on match stats page
        print(f'scraping for team: {"home" if i == 0 else "away"}')
        data = soup.select('.tbtitle')[i].parent.parent.select('.statdata')
        first_row = data[0].parent
        headers = [x.text for x in first_row.findPrevious('tr').find_all('td')]
        add_milestone(match_id, mode, f'process_row_start_{i}')
        match_stats_list = process_row(first_row, headers, [], match_id)
        add_milestone(match_id, mode, f'process_row_finish_{i}')
        upsert_match_stats(match_id, match_stats_list)
        add_milestone(match_id, mode, f'persist_finish_{i}')
    add_milestone(match_id, mode, "match_finish")


def process_row(row, headers, match_stats_list, match_id):
    try:
        stats_row = scrape_stats(row)
        match_stats_player = populate_stats(stats_row, headers, match_id)
    except ValueError as e:
        print(f'Exception processing row: {stats_row}: {e}')
        match_stats_player = None
    if match_stats_player:
        match_stats_list.append(match_stats_player)
    next_row = row.findNext('tr')
    if len(next_row.select('.statdata')):
        process_row(next_row, headers, match_stats_list, match_id)
    return match_stats_list


def scrape_stats(row):
    stats_row = []
    for td in row.find_all('td'):
        if td.find('a'):
            # get players name and team from link
            href_tag = td.find('a').attrs['href'].split('--')
            stats_row.append([href_tag[0].split('pp-')[1], href_tag[1]])
            continue
        stats_row.append(td.text.strip())
    return stats_row


def populate_stats(stat_row, headers, match_id):
    match_stats_player = MatchStatsPlayer()
    match_stats_player.game_id = match_id
    match_stats_player.updated_at = datetime.datetime.now()
    for i in range(len(stat_row)):
        key = headers[i].upper()
        value = stat_row[i]
        if key == 'PLAYER':
            match_stats_player.team = value[0]
            match_stats_player.player_name = value[1]
            match_stats_player.player_id = find_player_id(value[0], value[1])
            if match_stats_player.player_id is None:
                print(f'Player not in current season player list {value}. Adding without playerid.')
        elif key == "K":
            match_stats_player.kicks = int(value)
        elif key == "HB":
            match_stats_player.handballs = int(value)
        elif key == "D":
            match_stats_player.disposals = int(value)
        elif key == "M":
            match_stats_player.marks = int(value)
        elif key == "G":
            match_stats_player.goals = int(value)
        elif key == "B":
            match_stats_player.behinds = int(value)
        elif key == "T":
            match_stats_player.tackles = int(value)
        elif key == "HO":
            match_stats_player.hit_outs = int(value)
        elif key == "GA":
            match_stats_player.goal_assists = int(value)
        elif key == "I50":
            match_stats_player.inside_50s = int(value)
        elif key == "CL":
            match_stats_player.clearances = int(value)
        elif key == "CG":
            match_stats_player.clangers = int(value)
        elif key == "R50":
            match_stats_player.rebound_50s = int(value)
        elif key == "FF":
            match_stats_player.frees_for = int(value)
        elif key == "FA":
            match_stats_player.frees_against = int(value)
        # advanced
        elif key == "CP":
            match_stats_player.contested_possessions = int(value)
        elif key == "UP":
            match_stats_player.uncontested_possessions = int(value)
        elif key == "ED":
            match_stats_player.effective_disposals = int(value)
        elif key == "DE%":
            match_stats_player.disposal_efficiency = float(value)
        elif key == "CM":
            match_stats_player.contested_marks = int(value)
        elif key == "MI5":
            match_stats_player.marks_inside_50 = int(value)
        elif key == "1%":
            match_stats_player.one_percenters = int(value)
        elif key == "BO":
            match_stats_player.bounces = int(value)
        elif key == "CCL":
            match_stats_player.centre_clearances = int(value)
        elif key == "SCL":
            match_stats_player.stoppage_clearances = int(value)
        elif key == "SI":
            match_stats_player.score_involvements = int(value)
        elif key == "MG":
            match_stats_player.metres_gained = int(value)
        elif key == "TO":
            match_stats_player.turnovers = int(value)
        elif key == "ITC":
            match_stats_player.intercepts = int(value)
        elif key == "T5":
            match_stats_player.tackles_inside_50 = int(value)
        elif key == "TOG%":
            match_stats_player.time_on_ground_pcnt = int(value)
    return match_stats_player


def find_player_id(team_name, player_name):
    Session = sessionmaker(bind=engine)
    with Session() as session:
        player = session.execute(select(Player).filter_by(team=team_name, name_key=player_name)).first()
        if player:
            return player[0].id
        return None


def add_milestone(match_id, mode, milestone_name):
    new_milestone = Milestone()
    new_milestone.run_id = run_id
    new_milestone.match_id = match_id
    new_milestone.mode = mode
    new_milestone.milestone = milestone_name
    new_milestone.milestone_time = datetime.datetime.now()
    milestone_session.add(new_milestone)


def upsert_match_stats(match_id, match_stats_list):
    Session = sessionmaker(bind=engine)
    with Session() as session:
        stats_from_db = session.execute(select(MatchStatsPlayer).filter_by(game_id=match_id)).all()
        for match_stats in match_stats_list:
            if match_stats.player_name is None or match_stats.team is None:
                print(f'match_stats is missing details required for persistance. doing nothing. '
                      f'match_stats: {match_stats}')
                continue
            db_matches = [x[0] for x in stats_from_db if match_stats.game_id == x[0].game_id and match_stats.player_name
                          == x[0].player_name and match_stats.team == x[0].team]
            if len(db_matches) > 0:
                # just add the id to our obj, then merge, then commit session
                match_stats.id = db_matches[0].id
            # else:
                # print(f'New match_stat: match_id:{match_stats.game_id} player:{match_stats.player_name}'
                #       f' team:{match_stats.team} will be added to DB')
            session.merge(match_stats)  # merge updates if id exists and adds new if it doesnt
        try:
            session.commit()
        except Exception as e:
            print(f'Caught exception {e} \n'
                  f'Rolling back {match_stats_list}')
            session.rollback()


if __name__ == '__main__':
    main()
