import copy
import datetime
import bs4
import os

from scrapers import injuryScrape
from model import base
from model import Player
from model.injury import Injury
from scrapers.injuryScrape import TEAMS
from test import get_html
from test.scrapertest.BaseScraperTest import BaseScraperTest


class TestInjuryScrape(BaseScraperTest):
    # for testing the entire html document
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    HTML_SOURCE_FILE = os.path.join(DIR_PATH, '../html_files', get_html.INJURY_FILE_NAME)
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

        # add player to put injury against
        add_player_to_db(5, 'daniel-talia', 'adelaide-crows')

        data = soup.select('.tbtitle')[0]
        self.team_name = TEAMS[data.text.split('(')[0].strip()]
        self.team_table = data.parent.findNext('tr').findAll('tr')
        self.headers = []
        for header in self.team_table[0].findAll('td'):
            self.headers.append(header.text.strip())
        data_rows = injuryScrape.scrape_rows(self.team_table)
        self.injury_row = data_rows[0]
        self.injury = injuryScrape.populate_injury(self.injury_row, self.TEAM, self.headers, TestInjuryScrape._engine)
        self.injury.player_id = 5

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
        self.assertEqual(len(data_rows), 6)
        injury_row = data_rows[0]
        self.assertEqual(injury_row[0], 'aaron-nietschke')
        self.assertEqual(injury_row[1], 'Knee')
        self.assertEqual(injury_row[2], 'Season')

    def test_populate_injury_player_doesnt_exist(self):
        with TestInjuryScrape.Session() as cleanup_session:
            cleanup_session.query(Player).delete()
            cleanup_session.commit()
        test_injury_row = ['daniel-talia', 'Foot', 'TBC']
        injury = injuryScrape.populate_injury(test_injury_row, self.TEAM, self.headers, TestInjuryScrape._engine)
        self.assertIsNotNone(injury)
        self.assertEqual(injury.player_id, None)
        self.assertEqual(injury.injury, 'Foot')
        self.assertEqual(injury.returning, 'TBC')
        self.assertEqual(injury.recovered, False)

    def test_populate_injury_player_exists(self):
        # player is defined in setup function
        test_injury_row = ['daniel-talia', 'Foot', 'TBC']
        injury = injuryScrape.populate_injury(test_injury_row, self.TEAM, self.headers, TestInjuryScrape._engine)
        self.assertIsNotNone(injury)
        self.assertEqual(injury.player_id, 5)
        self.assertEqual(injury.injury, 'Foot')
        self.assertEqual(injury.returning, 'TBC')
        self.assertEqual(injury.recovered, False)

    def test_upsert_injuries(self):
        injury_list = [self.injury]
        injuryScrape.upsert_injuries(injury_list, TestInjuryScrape._engine)
        with TestInjuryScrape.Session() as session:
            injuries_in_db = session.query(Injury).all()
            self.assertEqual(len(injuries_in_db), 1)
            db_injury = injuries_in_db[0]
            self.assertEqual(db_injury.player_id, 5)
            self.assertEqual(db_injury.injury, 'Knee')
            self.assertEqual(db_injury.returning, 'Season')
            self.assertEqual(db_injury.recovered, False)

    def test_upsert_injury_already_exists(self):
        # insert copy of injury with different details into db
        with TestInjuryScrape.Session() as test_session:
            injury_copy = copy.deepcopy(self.injury)
            injury_copy.injury = 'Hand'
            injury_copy.recovered = True
            test_session.add(injury_copy)
            test_session.commit()

        injury_list = [self.injury]
        injuryScrape.upsert_injuries(injury_list, TestInjuryScrape._engine)
        with TestInjuryScrape.Session() as session:
            injuries_in_db = session.query(Injury).all()
            self.assertEqual(len(injuries_in_db), 1)
            db_injury = injuries_in_db[0]
            self.assertEqual(db_injury.player_id, 5)
            self.assertEqual(db_injury.injury, 'Knee')
            self.assertEqual(db_injury.returning, 'Season')
            self.assertEqual(db_injury.recovered, False)

    def test_upsert_injury_recovered_if_player_not_in_latest_scrape(self):
        add_player_to_db(3, 'mikky-mo', 'adelaide-crows')
        with TestInjuryScrape.Session() as test_session:
            injury2 = Injury()
            injury2.player_id = 3  # different to the id in the scraped injury list
            injury2.injury = 'Hand'
            injury2.recovered = False  # this should change after we run the upsert function
            test_session.add(injury2)
            test_session.commit()

        injury_list = [self.injury]
        injuryScrape.upsert_injuries(injury_list, TestInjuryScrape._engine)
        with TestInjuryScrape.Session() as session:
            injuries_in_db = session.query(Injury).all()
            self.assertEqual(len(injuries_in_db), 2)
            recovered_injury = injuries_in_db[0]
            self.assertEqual(recovered_injury.player_id, 3)
            self.assertEqual(recovered_injury.injury, 'Hand')
            self.assertEqual(recovered_injury.recovered, True)

    def tearDown(self):
        with TestInjuryScrape.Session() as cleanup_session:
            cleanup_session.query(Injury).delete()
            cleanup_session.query(Player).delete()
            cleanup_session.commit()

    @classmethod
    def tearDownClass(cls):
        base.Base.metadata.drop_all(TestInjuryScrape._engine, checkfirst=False)


def add_player_to_db(player_id, name, team):
    # add player to put injury against
    player = Player(name, team, datetime.date(1990, 1, 1))
    player.id = player_id
    with TestInjuryScrape.Session() as player_session:
        player_session.add(player)
        player_session.commit()
