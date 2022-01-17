import copy
import datetime
import bs4
import os

from sqlalchemy import select
from datascrape.scrapers import gameScrape
from model import base
from model import Game
from datascrape.test import get_html
from datascrape.test.scrapertest.BaseScraperTest import BaseScraperTest


class TestGameScrape(BaseScraperTest):
    # for testing the entire html document
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    HTML_SOURCE_FILE = os.path.join(DIR_PATH, '../html_files', get_html.GAMES_FILE_NAME)
    YEAR = 2019

    # for testing an individual row
    HTML_ONE_ROW = '''<tr bgcolor="#f2f4f7" onmouseout="this.bgColor='#f2f4f7';" onmouseover="this.bgColor='#cbcdd0';">
                <td class="data" height="24"> Thu 21 Mar 7:25pm</td>
                <td class="data">
                <a href="th-carlton-blues">Carlton</a>
                v 
                <a href="th-richmond-tigers">Richmond</a>
                </td>
                <td class="data">MCG</td>
                <td align="center" class="data">85016</td>
                <td align="center" class="data"><a href="ft_match_statistics?mid=9721">64-97</a></td>
                <td class="data">
                <a href="ft_player_profile?pid=3930" rel="nofollow">P. Cripps</a> 32<br/>
                </td>
                <td class="data">
                <a href="ft_player_profile?pid=3457" rel="nofollow">T. Lynch</a> 3<br/>
                <a href="ft_player_profile?pid=3952" rel="nofollow">T. Nankervis</a> 3<br/>
                <a href="ft_player_profile?pid=6465" rel="nofollow">J. Higgins</a> 3<br/>
                </td>
                </tr>
                '''

    HTML_FINALS_ROW = '''<tr><td height="28" align="center" colspan="7" class="tbtitle">
            Grand Final
    </td></tr>
    <tr bgcolor="#f2f4f7" onmouseout="this.bgColor='#f2f4f7';" onmouseover="this.bgColor='#cbcdd0';">
                <td class="data" height="24"> Thu 21 Mar 7:25pm</td>
                <td class="data">
                <a href="th-carlton-blues">Carlton</a>
                v 
                <a href="th-richmond-tigers">Richmond</a>
                </td>
                <td class="data">MCG</td>
                <td align="center" class="data">85016</td>
                <td align="center" class="data"><a href="ft_match_statistics?mid=9721">64-97</a></td>
                <td class="data">
                <a href="ft_player_profile?pid=3930" rel="nofollow">P. Cripps</a> 32<br/>
                </td>
                <td class="data">
                <a href="ft_player_profile?pid=3457" rel="nofollow">T. Lynch</a> 3<br/>
                <a href="ft_player_profile?pid=3952" rel="nofollow">T. Nankervis</a> 3<br/>
                <a href="ft_player_profile?pid=6465" rel="nofollow">J. Higgins</a> 3<br/>
                </td>
                </tr>
                '''

    def setUp(self):
        with TestGameScrape.Session() as cleanup_session:
            cleanup_session.query(Game).delete()
            cleanup_session.commit()
        # Stub html file used - to refresh file run get_html.py with 'players' as first arg
        with open(self.HTML_SOURCE_FILE, 'r') as file:
            soup = bs4.BeautifulSoup(file.read(), 'html.parser')
        data = soup.select('.data')
        self.first_row = data[0].parent
        self.headers = [x.text.split('\n')[0].strip() for x in self.first_row.findPrevious('tr').find_all(['td', 'th'])]
        # one row test data:
        self.one_row_soup = bs4.BeautifulSoup(self.HTML_ONE_ROW, 'html.parser')
        self.ONE_GAME_ROW = ['Thu 21 Mar 7:25pm', ['carlton-blues', 'richmond-tigers'], 'MCG', '85016', ['9721', '64', '97'],
                        'P. Cripps 32', 'T. Lynch 3\nT. Nankervis 3\nJ. Higgins 3']
        self.game = gameScrape.populate_game(self.ONE_GAME_ROW, self.headers, self.YEAR, 1)
        # all rows test data
        self.games = gameScrape.process_row(self.first_row, self.headers, [], self.YEAR, 1)

    def test_process_row(self):
        one_game = gameScrape.process_row(self.one_row_soup, self.headers, [], self.YEAR, 1)
        self.assertIsNotNone(one_game)
        self.assertEqual(one_game[0].id, 9721)
        self.assertEqual(one_game[0].home_team, 'carlton-blues')
        self.assertEqual(one_game[0].away_team, 'richmond-tigers')
        self.assertEqual(one_game[0].venue, 'MCG')
        self.assertEqual(one_game[0].crowd, 85016)
        self.assertEqual(one_game[0].home_score, 64)
        self.assertEqual(one_game[0].away_score, 97)
        self.assertEqual(one_game[0].winner, 'richmond-tigers')
        self.assertEqual(one_game[0].date_time, datetime.datetime(self.YEAR, 3, 21, 19, 25, 0))
        self.assertEqual(one_game[0].year, self.YEAR)
        self.assertEqual(one_game[0].round_number, 1)

    def test_process_row_multiple(self):
        games = gameScrape.process_row(self.first_row, self.headers, [], self.YEAR, 1)
        self.assertIsNotNone(games)
        self.assertEqual(len(games), 207)
        self.assertEqual(games[0].id, 9721)
        self.assertEqual(games[-1].id, 9927)

    def test_process_row_finals_round(self):
        finals_soup = bs4.BeautifulSoup(self.HTML_FINALS_ROW, 'html.parser')  # contains grand-final row header
        finals_first_row = finals_soup.select('tr')[0]
        finals_games = gameScrape.process_row(finals_first_row, self.headers, [], self.YEAR, 1)
        self.assertIsNotNone(finals_games)
        self.assertEqual(finals_games[0].round_number, 54)  # round for grand-final

    def test_scrape_game(self):
        row = self.one_row_soup.find('tr')
        game_row = gameScrape.scrape_game(row)
        self.assertEqual(len(game_row), 7)
        self.assertEqual(game_row[0], 'Thu 21 Mar 7:25pm')
        self.assertEqual(game_row[1][0], 'carlton-blues')
        self.assertEqual(game_row[1][1], 'richmond-tigers')
        self.assertEqual(game_row[2], 'MCG')
        self.assertEqual(game_row[3], '85016')
        self.assertEqual(game_row[4][0], '9721')
        self.assertEqual(game_row[4][1], '64')
        self.assertEqual(game_row[4][2], '97')

    def test_scrape_game_missing_data(self):
        row = self.one_row_soup.find('tr')
        row.find_all('td')[3].string = ''
        game_row = gameScrape.scrape_game(row)
        self.assertEqual(len(game_row), 7)
        self.assertEqual(game_row[0], 'Thu 21 Mar 7:25pm')
        self.assertEqual(game_row[1][0], 'carlton-blues')
        self.assertEqual(game_row[1][1], 'richmond-tigers')
        self.assertEqual(game_row[2], 'MCG')
        self.assertEqual(game_row[3], '')
        self.assertEqual(game_row[4][0], '9721')
        self.assertEqual(game_row[4][1], '64')
        self.assertEqual(game_row[4][2], '97')

    def test_scrape_game_populate_game_bad_links(self):
        row = self.one_row_soup.find('tr')
        td_to_change = row.find_all('td')[1]
        td_to_change.find_all('a')[1].decompose() # remove one a tag from this td
        game_row = gameScrape.scrape_game(row)
        self.assertEqual(len(game_row), 7)
        self.assertEqual(game_row[0], 'Thu 21 Mar 7:25pm')
        self.assertEqual(game_row[1], 'Carlton\n                v')
        self.assertEqual(game_row[2], 'MCG')
        self.assertEqual(game_row[3], '85016')
        self.assertEqual(game_row[4][0], '9721')
        self.assertEqual(game_row[4][1], '64')
        self.assertEqual(game_row[4][2], '97')
        game = gameScrape.populate_game(game_row, self.headers, self.YEAR, 1)
        self.assertIsNone(game.home_team)
        self.assertIsNone(game.away_team)

    def test_populate_game(self):
        game = gameScrape.populate_game(self.ONE_GAME_ROW, self.headers, self.YEAR, 1)
        self.assertEqual(game.id, 9721)
        self.assertEqual(game.home_team, 'carlton-blues')
        self.assertEqual(game.away_team, 'richmond-tigers')
        self.assertEqual(game.venue, 'MCG')
        self.assertEqual(game.crowd, 85016)
        self.assertEqual(game.home_score, 64)
        self.assertEqual(game.away_score, 97)
        self.assertEqual(game.winner, 'richmond-tigers')
        self.assertEqual(game.date_time, datetime.datetime(self.YEAR, 3, 21, 19, 25, 0))
        self.assertEqual(game.year, self.YEAR)
        self.assertEqual(game.round_number, 1)

    def test_populate_game_draw(self):
        # set scores as equal
        self.ONE_GAME_ROW[4][1] = '70'
        self.ONE_GAME_ROW[4][2] = '70'
        game = gameScrape.populate_game(self.ONE_GAME_ROW, self.headers, self.YEAR, 1)
        self.assertEqual(game.home_team, 'carlton-blues')
        self.assertEqual(game.away_team, 'richmond-tigers')
        self.assertEqual(game.home_score, 70)
        self.assertEqual(game.away_score, 70)
        self.assertEqual(game.winner, 'DRAW')

    def test_populate_game_BYE(self):
        game_row = ['', 'Western Bulldogs', 'BYE', '', '', '', '']
        game = gameScrape.populate_game(game_row, self.headers, self.YEAR, 1)
        self.assertIsNone(game)

    def test_populate_game_no_result(self):
        game_row = ['Sun 18 Jul 12:35pm', ['kangaroos', 'essendon-bombers'], 'Metricon Stadium', '', '', '', '']
        game = gameScrape.populate_game(game_row, self.headers, self.YEAR, 1)
        self.assertIsNone(game)

    def test_upsert_game_new(self):
        gameScrape.upsert_games([self.game], TestGameScrape._engine)
        with TestGameScrape.Session() as session:
            game_in_db = session.execute(select(Game).filter_by(id=self.game.id)).first()
            self.assertIsNotNone(game_in_db[0])
            self.assertEqual(game_in_db[0].id, 9721)
            self.assertEqual(game_in_db[0].home_team, 'carlton-blues')
            self.assertEqual(game_in_db[0].away_team, 'richmond-tigers')
            self.assertEqual(game_in_db[0].venue, 'MCG')
            self.assertEqual(game_in_db[0].crowd, 85016)
            self.assertEqual(game_in_db[0].home_score, 64)
            self.assertEqual(game_in_db[0].away_score, 97)
            self.assertEqual(game_in_db[0].winner, 'richmond-tigers')
            self.assertEqual(game_in_db[0].date_time, datetime.datetime(self.YEAR, 3, 21, 19, 25, 0))
            self.assertEqual(game_in_db[0].year, self.YEAR)
            self.assertEqual(game_in_db[0].round_number, 1)

    def test_upsert_game_already_exists(self):
        with TestGameScrape.Session() as test_session:
            game_copy = copy.deepcopy(self.game)
            game_copy.crowd = 99999  # to be overridden when game is added again
            game_copy.venue = 'the moon'  # to be overridden when game is added again
            test_session.add(game_copy)
            test_session.commit()
        gameScrape.upsert_games([self.game], TestGameScrape._engine)
        with TestGameScrape.Session() as session:
            game_in_db = session.execute(select(Game).filter_by(id=self.game.id)).first()
            self.assertIsNotNone(game_in_db[0])
            self.assertEqual(game_in_db[0].id, 9721)
            self.assertEqual(game_in_db[0].home_team, 'carlton-blues')
            self.assertEqual(game_in_db[0].away_team, 'richmond-tigers')
            self.assertEqual(game_in_db[0].venue, 'MCG')  # latest update should overwrite existing game details
            self.assertEqual(game_in_db[0].crowd, 85016)
            self.assertEqual(game_in_db[0].home_score, 64)
            self.assertEqual(game_in_db[0].away_score, 97)
            self.assertEqual(game_in_db[0].winner, 'richmond-tigers')
            self.assertEqual(game_in_db[0].date_time, datetime.datetime(self.YEAR, 3, 21, 19, 25, 0))
            self.assertEqual(game_in_db[0].year, self.YEAR)
            self.assertEqual(game_in_db[0].round_number, 1)

    def test_upsert_game_no_id(self):
        self.game.id = None
        gameScrape.upsert_games([self.game], TestGameScrape._engine)
        with TestGameScrape.Session() as session:
            game_in_db = session.execute(select(Game).filter_by(id=self.game.id)).first()
            self.assertIsNone(game_in_db)

    def test_upsert_game_no_home_away_team(self):
        # home team
        self.game.home_team = None
        gameScrape.upsert_games([self.game], TestGameScrape._engine)
        with TestGameScrape.Session() as session:
            game_in_db = session.execute(select(Game).filter_by(id=self.game.id)).first()
            self.assertIsNone(game_in_db)
        # away team
        self.game.home_team = 'carlton-blues'
        self.game.away_team = None
        gameScrape.upsert_games([self.game], TestGameScrape._engine)
        with TestGameScrape.Session() as session:
            game_in_db = session.execute(select(Game).filter_by(id=self.game.id)).first()
            self.assertIsNone(game_in_db)

    def test_upsert_games_full_year(self):
        gameScrape.upsert_games(self.games, TestGameScrape._engine)
        with TestGameScrape.Session() as session:
            games_in_db = session.execute(select(Game).filter_by(year=self.YEAR)).all()
            self.assertEqual(len(games_in_db), 207)

    def tearDown(self):
        with TestGameScrape.Session() as cleanup_session:
            cleanup_session.query(Game).delete()
            cleanup_session.commit()

    @classmethod
    def tearDownClass(cls):
        base.Base.metadata.drop_all(TestGameScrape._engine, checkfirst=False)
