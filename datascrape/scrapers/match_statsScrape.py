from os import getenv
from dotenv import load_dotenv
import threading
import requests
import bs4
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select
import datetime
import queue
import logging.config
from threading import Thread

from datascrape.logging_config import LOGGING_CONFIG
from datascrape.scrapers.BaseScraper import BaseScraper
from datascrape.util.MilestoneRecorder import MileStoneRecorder
from model.base import Base
from model.player import Player
from model.game import Game
from model.milestone import Milestone
from model.match_stats_player import MatchStatsPlayer

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)

run_id = round(datetime.datetime.now().timestamp() * 1000)

TEAM_HEADER_MAP = {
    'adelaide-crows': 'adelaide',
    'brisbane-lions': 'brisbane',
    'carlton-blues': 'carlton',
    'collingwood-magpies': 'collingwood',
    'essendon-bombers': 'essendon',
    'fremantle-dockers': 'fremantle',
    'geelong-cats': 'geelong',
    'gold-coast-suns': 'gold coast',
    'greater-western-sydney-giants': 'gws',
    'hawthorn-hawks': 'hawthorn',
    'kangaroos': 'north melbourne',
    'melbourne-demons': 'melbourne',
    'port-adelaide-power': 'port adelaide',
    'richmond-tigers': 'richmond',
    'st-kilda-saints': 'st kilda',
    'sydney-swans': 'sydney',
    'west-coast-eagles': 'west coast',
    'western-bulldogs': 'western bulldogs',
}


class MatchStatsScraper(BaseScraper):

    def __init__(self, engine, from_year, to_year, from_round, to_round):
        super().__init__(engine, "MatchStats")
        self.from_year = from_year
        self.to_year = to_year
        self.from_round = from_round
        self.to_round = to_round
        self.milestone_recorder = MileStoneRecorder(self.engine)
        self.rows_updated = 0

    def scrape_entities(self):
        LOGGER.info("Starting MATCH STATS SCRAPE")

        start = datetime.datetime.now()
        Base.metadata.create_all(self.engine, checkfirst=True)
        request_q = self.populate_request_queue()  # synchronously create list of urls
        response_q = queue.Queue()
        threads = 5
        for i in range(threads):
            t = Thread(target=self.send_request, args=(request_q, response_q))  # async create threads for sending requests
            t.daemon = True
            t.start()
        # pick up responses and synchronously process them
        while True:
            response = response_q.get()
            self.process_response(response)
            response_q.task_done()
            if len(request_q.queue) == 0 and len(response_q.queue) == 0:
                break
        self.milestone_recorder.commit_milestones()
        LOGGER.info(f"Total time taken: {datetime.datetime.now() - start}")
        LOGGER.info("Finished MATCH STATS SCRAPE")
        return self.rows_updated

    def populate_request_queue(self):
        session = sessionmaker(bind=self.engine)
        request_q = queue.Queue()
        for year in range(self.from_year, self.to_year + 1):
            for round_number in range(self.from_round, self.to_round + 1):
                with session() as games_session:
                    # get match ids for year / round
                    matches = games_session.execute(select(Game.id).filter_by(year=year, round_number=round_number)).scalars().all()
                    for match_id in matches:
                        for mode in ['basic', 'advanced']:  # advanced stats on 2nd link
                            request_q.put({'year': year, 'round_number': round_number,
                                           'match_id': match_id, 'mode': mode,
                                           'url': None, 'response': None})
        return request_q

    def send_request(self, request_q, response_q):
        while not len(request_q.queue) == 0:  # request q is complete
            req = request_q.get()
            if req['mode'] == 'basic':
                req_url = f"https://www.footywire.com/afl/footy/ft_match_statistics?mid={req['match_id']}"
            else:
                req_url = f"https://www.footywire.com/afl/footy/ft_match_statistics?mid={req['match_id']}&advv=Y"
            req['url'] = req_url
            LOGGER.debug(f'Thread {threading.get_ident()}: sending req: {req_url}')
            self.add_milestone(req['match_id'], req['mode'], f"request_start")
            req['response'] = requests.get(req_url).text
            LOGGER.debug(f'Thread {threading.get_ident()}: got response for {req_url}')
            self.add_milestone(req['match_id'], req['mode'], f"request_finish")
            response_q.put(req)
            request_q.task_done()

    def process_response(self, res_obj):
        year = res_obj['year']
        round_number = res_obj['round_number']
        match_id = res_obj['match_id']
        mode = res_obj['mode']
        url = res_obj['url']
        res = res_obj['response']
        self.add_milestone(match_id, mode, f"match_start")
        LOGGER.info(f'Scraping match stats for year: {year}, round: {round_number}, match: {match_id}, url: {url}')
        soup = bs4.BeautifulSoup(res, 'lxml')
        team_links = soup.select('#matchscoretable')[0].find_all('a')
        teams = []
        for i in [0,1]:
            teams.append('-'.join(team_links[i].attrs['href'].split('-')[1:]))
        for i in [0, 1]:  # both teams on match stats page
            LOGGER.debug(f'Scraping for team: {"home" if i == 0 else "away"}')
            team = teams[i]
            stats_table_header = soup.select('.tbtitle')[i]
            self.verify_team(stats_table_header, team)
            first_row = stats_table_header.parent.parent.select('.statdata')[0].parent
            headers = [x.text for x in first_row.findPrevious('tr').find_all('td')]
            self.add_milestone(match_id, mode, f'process_row_start_{i}')
            match_stats_list = self.process_row(first_row, headers, [], team, match_id)
            self.add_milestone(match_id, mode, f'process_row_finish_{i}')
            self.upsert_match_stats(match_id, match_stats_list)
            self.add_milestone(match_id, mode, f'persist_finish_{i}')
            self.rows_updated += len(match_stats_list)
        self.add_milestone(match_id, mode, "match_finish")

    def process_row(self, row, headers, match_stats_list, team, match_id):
        try:
            stats_row = self.scrape_stats_one_row(row)
            match_stats_player = self.populate_stats(stats_row, headers, team, match_id)
        except ValueError as e:
            LOGGER.exception(f'Exception processing row: {stats_row}: {e}')
            match_stats_player = None
        if match_stats_player:
            match_stats_list.append(match_stats_player)
        next_row = row.findNext('tr')
        if next_row is not None and len(next_row.select('.statdata')):
            self.process_row(next_row, headers, match_stats_list, team, match_id)
        return match_stats_list

    @staticmethod
    def scrape_stats_one_row(row):
        stats_row = []
        for td in row.find_all('td'):
            if td.find('a'):
                # get players name from link
                href_tag = td.find('a').attrs['href'].split('--')
                stats_row.append(href_tag[1])
                continue
            stats_row.append(td.text.strip())
        return stats_row

    def populate_stats(self, stat_row, headers, team, match_id):
        match_stats_player = MatchStatsPlayer()
        match_stats_player.game_id = match_id
        match_stats_player.updated_at = datetime.datetime.now()
        for i in range(len(stat_row)):
            key = headers[i].upper()
            value = stat_row[i]
            if key == 'PLAYER':
                match_stats_player.team = team
                match_stats_player.player_name = value
                match_stats_player.player_id = self.find_player_id(team, value, self.engine)
                if match_stats_player.player_id is None:
                    LOGGER.debug(f'Player not in current season player list {value}. Adding without playerid.')
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

    def upsert_match_stats(self, match_id, match_stats_list):
        session = sessionmaker(bind=self.engine)
        with session() as session:
            stats_from_db = session.execute(select(MatchStatsPlayer).filter_by(game_id=match_id)).all()
            for match_stats in match_stats_list:
                if match_stats.player_name is None or match_stats.team is None:
                    LOGGER.warning(f'Match_stats is missing details required for persistance. doing nothing. '
                                   f'match_stats: {match_stats}')
                    continue
                db_matches = [x[0] for x in stats_from_db if match_stats.game_id == x[0].game_id and match_stats.player_name
                              == x[0].player_name and match_stats.player_id == x[0].player_id]
                if len(db_matches) > 0:
                    # just add the id to our obj, then merge, then commit session
                    match_stats.id = db_matches[0].id
                session.merge(match_stats)  # merge updates if id exists and adds new if it doesnt
            try:
                session.commit()
            except Exception as e:
                LOGGER.warning(f'Caught exception {e} \n'
                               f'Rolling back {match_stats_list}')
                session.rollback()

    def add_milestone(self, match_id, mode, milestone_name):
        new_milestone = Milestone(run_id, match_id, mode, milestone_name)
        self.milestone_recorder.add_milestone(new_milestone)

    @staticmethod
    def verify_team(header, team):
        expected_words = len(TEAM_HEADER_MAP[team].split())
        header_team = ' '.join(header.text.strip().split()[0:0+expected_words]).lower()
        if TEAM_HEADER_MAP[team] != header_team:
            LOGGER.error(f'Team link does not match expected team name - '
                         f'please check for data integrity issues. team from header: {header_team}, team_id: {team}')

    @staticmethod
    def find_player_id(team_name, player_name, engine):
        session = sessionmaker(bind=engine)
        with session() as session:
            player_match = session.execute(select(Player).filter_by(name_key=player_name)).all()
            for player in player_match:
                if player[0].team == team_name:
                    # more likely to be the player we want as they are on the expected team
                    return player[0].id
            # no team matches, just check for any match and return that
            if len(player_match):
                return player_match[0][0].id
            return None


if __name__ == '__main__':
    load_dotenv()
    db_engine = create_engine(getenv('DATABASE_URL'))
    MatchStatsScraper(db_engine, 2021, 2021, 1, 30).scrape()
