import datetime
import unittest
import bs4
import os
import copy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datascrape import injuryScrape
from datascrape import base
from datascrape.player import Player
from datascrape.injury import Injury
from datascrape.injuryScrape import TEAMS


class TestInjuryScrape(unittest.TestCase):
    # for testing the entire html document
    HTML_SOURCE_FILE = 'injuries.html'
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    HTML_SOURCE_FILE = os.path.join(DIR_PATH, 'html_files', HTML_SOURCE_FILE)
    TEAM = 'adelaide-crows'

    # for testing an individual row
    HTML_ONE_ROW = '''<tr>
                <td class="lbnorm" height="28" width="258">  Player</td>
                <td class="bnorm" width="280">Injury</td>
                <td class="bnorm" width="150">Returning</td>
                </tr>
                <tr bgcolor="#f2f4f7" onmouseout="this.bgColor='#f2f4f7';" onmouseover="this.bgColor='#cbcdd0';">
                <td align="left" height="24" width="100">  <a href="/afl/footy/pp-adelaide-crows--daniel-talia" rel="nofollow">Daniel Talia</a></td>
                <td align="center">Foot</td>
                <td align="center">TBC</td>
                </tr>'''

    @classmethod
    def setUpClass(cls):
        TestInjuryScrape._engine = create_engine(
            'postgresql://postgres:oscar12!@localhost:5432/tiplos-test?gssencmode=disable'
        )
        base.Base.metadata.create_all(TestInjuryScrape._engine, checkfirst=True)
        TestInjuryScrape.Session = sessionmaker(bind=TestInjuryScrape._engine)

    def setUp(self):
        with TestInjuryScrape.Session() as cleanup_session:
            cleanup_session.query(Injury).delete()
            cleanup_session.query(Player).delete()
            cleanup_session.execute("ALTER SEQUENCE player_id_seq RESTART WITH 1")
            cleanup_session.execute("ALTER SEQUENCE injury_id_seq RESTART WITH 1")
            cleanup_session.commit()
        # Stub html file used - to refresh file run get_html.py with 'players' as first arg
        with open(self.HTML_SOURCE_FILE, 'r') as file:
            soup = bs4.BeautifulSoup(file.read(), 'html.parser')

        data = soup.select('.tbtitle')[0]
        self.team_name = TEAMS[data.text.split('(')[0].strip()]
        self.team_table = data.parent.findNext('tr').findAll('tr')
        self.headers = []
        for header in self.team_table[0].findAll('td'):
            self.headers.append(header.text.strip())
        data_rows = injuryScrape.scrape_rows(self.team_table)
        self.injury = data_rows[0]

    def test_scrape_row(self):
        one_row_soup = bs4.BeautifulSoup(self.HTML_ONE_ROW, 'html.parser')
        test_table = one_row_soup.findAll('tr')
        injury_row = injuryScrape.scrape_rows(test_table)[0]
        self.assertEqual(len(injury_row), 3)
        self.assertEqual(injury_row[0], 'daniel-talia')
        self.assertEqual(injury_row[1], 'Foot')
        self.assertEqual(injury_row[2], 'TBC')

    def test_scrape_row_multiple(self):
        data_rows = injuryScrape.scrape_rows(self.team_table)
        self.assertEqual(len(data_rows), 8)
        injury_row = data_rows[0]
        self.assertEqual(injury_row[0], 'daniel-talia')
        self.assertEqual(injury_row[1], 'Foot')
        self.assertEqual(injury_row[2], 'TBC')

    def test_populate_injury(self):
        test_injury_row = ['daniel-talia', 'Foot', 'TBC']
        injury = injuryScrape.populate_injury(test_injury_row, self.TEAM, self.headers, TestInjuryScrape._engine)
        self.assertIsNotNone(injury)
        self.assertEqual(injury.player_id, None)
        self.assertEqual(injury.injury, 'Foot')
        self.assertEqual(injury.returning, 'TBC')
        self.assertEqual(injury.recovered, False)

    def test_populate_injury_player_exists(self):
        player = Player()
        player.name_key = 'daniel-talia'
        player.id = 5
        player.DOB = datetime.date(1990, 1, 1)
        player.team = 'adelaide-crows'
        with TestInjuryScrape.Session() as player_session:
            player_session.add(player)
            player_session.commit()
        test_injury_row = ['daniel-talia', 'Foot', 'TBC']
        injury = injuryScrape.populate_injury(test_injury_row, self.TEAM, self.headers, TestInjuryScrape._engine)
        self.assertIsNotNone(injury)
        self.assertEqual(injury.player_id, 5)
        self.assertEqual(injury.injury, 'Foot')
        self.assertEqual(injury.returning, 'TBC')
        self.assertEqual(injury.recovered, False)

    def test_upsert_injuries(self):
        None

    def test_upsert_injury_already_exists(self):
        None

    def test_upsert_injury_same_player_already_with_different_injury(self):
        None

    def test_upsert_injury_recovered_if_player_not_in_latest_scrape(self):
        None

    def tearDown(self):
        with TestInjuryScrape.Session() as cleanup_session:
            cleanup_session.query(Player).delete()
            cleanup_session.commit()

    @classmethod
    def tearDownClass(cls):
        base.Base.metadata.drop_all(TestInjuryScrape._engine, checkfirst=False)


if __name__ == '__main__':
    unittest.main()