import unittest
import bs4
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datascrape import gameScrape
from datascrape.repositories import base
from datascrape.repositories.game import Game


class TestGameScrape(unittest.TestCase):

    # for testing the entire html document
    HTML_SOURCE_FILE = '2019-games.html'
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    HTML_SOURCE_FILE = os.path.join(DIR_PATH, 'html_files', HTML_SOURCE_FILE)

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

    @classmethod
    def setUpClass(cls):
        TestGameScrape._engine = create_engine(
            'postgresql://postgres:oscar12!@localhost:5432/tiplos-test?gssencmode=disable'
        )
        base.Base.metadata.create_all(TestGameScrape._engine, checkfirst=True)
        TestGameScrape.Session = sessionmaker(bind=TestGameScrape._engine)

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

    def test_process_row(self):
        None

    def test_process_row_multiple(self):
        None

    def test_process_row_multiple_finals_round(self):
        None

    def test_scrape_game(self):
        one_row_soup = bs4.BeautifulSoup(self.HTML_ONE_ROW, 'html.parser')
        row = one_row_soup.find('tr')
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
        None

    def test_scrape_game_bad_links(self):
        None

    def test_populate_game(self):
        None

    def test_populate_game_BYE(self):
        None

    def test_populate_game_no_result(self):
        None

    def test_upsert_game_new(self):
        None

    def test_upsert_game_already_exists(self):
        None

    def test_upsert_game_no_id(self):
        None

    def test_upsert_game_no_home_away_team(self):
        None

    def test_upsert_games_full_year(self):
        None

    def tearDown(self):
        with TestGameScrape.Session() as cleanup_session:
            cleanup_session.query(Game).delete()
            cleanup_session.commit()

    @classmethod
    def tearDownClass(cls):
        base.Base.metadata.drop_all(TestGameScrape._engine, checkfirst=False)


if __name__ == '__main__':
    unittest.main()
