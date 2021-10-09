import datetime
import bs4
import os
import copy

from datascrape.scrapers import fantasyScrape
from datascrape.repositories import base
from datascrape.repositories.player import Player
from datascrape.repositories.player_fantasy import PlayerFantasy
from test import get_html
from test.BaseScraperTest import BaseScraperTest


class TestFantasyScrape(BaseScraperTest):
    # for testing the entire html document
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    HTML_SOURCE_FILE = os.path.join(DIR_PATH, 'html_files', get_html.FANTASY_FILE_NAME)

    # for testing an individual row
    HTML_ONE_ROW = '''<table width="688" border="0" cellspacing="0" cellpadding="0">
                <tr>
                <td class="bnorm" width="60">Rank</td>
                <td height="44" class="lbnorm">Player</td>
                <td class="lbnorm" width="90">Team</td>
                <td class="bnorm" width="90">Current<br/>Salary</td>
                <td class="bnorm" width="90"><a href="dream_team_round?p=&s=S">2021 R1<br/>Salary</a></td>
                <td class="bnorm" width="90"><a href="dream_team_round?p=&s=T">2021 R1<br/>Score</a></td>
                <td class="bnorm" width="90"><a href="dream_team_round?p=&s=V">*2021 R1<br/>Value</a></td>
                </tr>
                <tr bgcolor="#f2f4f7" onMouseOver="this.bgColor='#cbcdd0';" onMouseOut="this.bgColor='#f2f4f7';">
                <td height="24" align="center">1</td>
                <td align="left"><a href="pr-essendon-bombers--andrew-mcgrath">Andrew McGrath</a>
                 <i>Injured</i>
                </td>
                <td align="left"><a href="th-essendon-bombers?year=2021">Bombers</a></td>
                <td align="center">$607,000</td>
                <td align="center">$738,000</td>
                <td align="center">141</td>
                <td align="center">19.1</td>
                </tr>
                </table>'''

    def setUp(self):
        with TestFantasyScrape.Session() as cleanup_session:
            cleanup_session.query(PlayerFantasy).delete()
            cleanup_session.query(Player).delete()
            cleanup_session.execute("ALTER SEQUENCE player_id_seq RESTART WITH 1")
            cleanup_session.execute("ALTER SEQUENCE fantasy_id_seq RESTART WITH 1")
            cleanup_session.commit()

        # add player2 to put fantasy against
        add_player_to_db(1, 'andrew-mcgrath', 'essendon-bombers')
        add_player_to_db(2, 'dominic-sheed', 'west-coast-eagles')

        # Set up one-row table
        one_row_soup = bs4.BeautifulSoup(self.HTML_ONE_ROW, 'html.parser')
        self.one_row_table, self.one_row_headers = fantasyScrape.get_data_table(one_row_soup)
        self.one_data_row = fantasyScrape.scrape_rows(self.one_row_table)[0]
        self.one_fantasy = fantasyScrape.populate_fantasy('dream_team', self.one_data_row,
                                                          self.one_row_headers, 2021, 1, TestFantasyScrape._engine)

        # Stub html file used - to refresh file run get_html.py with 'players' as first arg
        with open(self.HTML_SOURCE_FILE, 'r') as file:
            soup = bs4.BeautifulSoup(file.read(), 'html.parser')
        self.table, self.headers = fantasyScrape.get_data_table(soup)
        self.data_rows = fantasyScrape.scrape_rows(self.table)
        self.fantasies = []
        for row in self.data_rows[0:2]:
            self.fantasies.append(fantasyScrape.populate_fantasy('dream_team', row,
                                                                 self.headers, 2021, 1, TestFantasyScrape._engine))

    def test_scrape_row(self):
        row = fantasyScrape.scrape_rows(self.one_row_table)
        data_row = row[0]
        self.assertEqual(len(data_row), 7)
        self.assertEqual(data_row[0], '1')
        self.assertEqual(data_row[1], 'andrew-mcgrath')
        self.assertEqual(data_row[2], 'essendon-bombers')
        self.assertEqual(data_row[3], '$607,000')
        self.assertEqual(data_row[4], '$738,000')
        self.assertEqual(data_row[5], '141')
        self.assertEqual(data_row[6], '19.1')

    def test_scrape_row_multiple(self):
        data_rows = fantasyScrape.scrape_rows(self.table)
        self.assertEqual(len(data_rows), 404)
        data_row = data_rows[0]
        self.assertEqual(data_row[0], '1')
        self.assertEqual(data_row[1], 'andrew-mcgrath')
        self.assertEqual(data_row[2], 'essendon-bombers')
        self.assertEqual(data_row[3], '$515,000')
        self.assertEqual(data_row[4], '$738,000')
        self.assertEqual(data_row[5], '141')
        self.assertEqual(data_row[6], '19.1')
        data_row_last = data_rows[-1]
        self.assertEqual(data_row_last[0], '404')
        self.assertEqual(data_row_last[1], 'alex-pearce')
        self.assertEqual(data_row_last[2], 'fremantle-dockers')
        self.assertEqual(data_row_last[3], '$259,000')
        self.assertEqual(data_row_last[4], '$232,000')
        self.assertEqual(data_row_last[5], '7')
        self.assertEqual(data_row_last[6], '3.0')

    def test_populate_fantasy_player_doesnt_exist(self):
        self.one_data_row[1] = 'NO_NAME'
        fantasy = fantasyScrape.populate_fantasy('dream_team', self.one_data_row, self.one_row_headers,
                                                 2021, 1, TestFantasyScrape._engine)
        self.assertIsNotNone(fantasy)
        self.assertEqual(fantasy.player_id, None)
        self.assertEqual(fantasy.year, 2021)
        self.assertEqual(fantasy.round, 1)
        self.assertEqual(fantasy.round_ranking, '1')
        self.assertEqual(fantasy.round_salary, '$738,000')
        self.assertEqual(fantasy.round_score, '141')
        self.assertEqual(fantasy.round_value, '19.1')

    def test_populate_fantasy_player_exists(self):
        fantasy = fantasyScrape.populate_fantasy('dream_team', self.one_data_row, self.one_row_headers,
                                                 2021, 1, TestFantasyScrape._engine)
        self.assertIsNotNone(fantasy)
        self.assertEqual(fantasy.player_id, 1)
        self.assertEqual(fantasy.year, 2021)
        self.assertEqual(fantasy.round, 1)
        self.assertEqual(fantasy.round_ranking, '1')
        self.assertEqual(fantasy.round_salary, '$738,000')
        self.assertEqual(fantasy.round_score, '141')
        self.assertEqual(fantasy.round_value, '19.1')

    def test_insert_fantasies_already_exists(self):
        one_fantasy_copy = copy.deepcopy(self.one_fantasy)
        # insert first fantasy
        fantasyScrape.insert_fantasies('dream_team', [self.one_fantasy], 2021, 1, TestFantasyScrape._engine)
        # try to insert same fantasy again
        fantasyScrape.insert_fantasies('dream_team', [one_fantasy_copy], 2021, 1, TestFantasyScrape._engine)
        with TestFantasyScrape.Session() as session:
            fantasy_persisted = session.query(PlayerFantasy).all()
        self.assertEqual(len(fantasy_persisted), 1)

    def test_insert_fantasies_new_fantasy(self):
        fantasyScrape.insert_fantasies('dream_team', [self.one_fantasy], 2021, 1, TestFantasyScrape._engine)
        with TestFantasyScrape.Session() as session:
            fantasy_persisted = session.query(PlayerFantasy).all()
        self.assertEqual(len(fantasy_persisted), 1)
        fantasy = fantasy_persisted[0]
        self.assertIsNotNone(fantasy)
        self.assertEqual(fantasy.player_id, 1)
        self.assertEqual(fantasy.year, 2021)
        self.assertEqual(fantasy.round, 1)
        self.assertEqual(fantasy.round_ranking, 1)
        self.assertEqual(fantasy.round_salary, '$738,000.00')
        self.assertEqual(fantasy.round_score, 141)
        self.assertEqual(fantasy.round_value, 19.1)

    def test_insert_fantasies_multiple(self):
        fantasyScrape.insert_fantasies('dream_team', self.fantasies, 2021, 1, TestFantasyScrape._engine)
        with TestFantasyScrape.Session() as session:
            fantasy_persisted = session.query(PlayerFantasy).all()
        self.assertEqual(len(fantasy_persisted), 2)
        fantasy1 = fantasy_persisted[0]
        self.assertIsNotNone(fantasy1)
        self.assertEqual(fantasy1.player_id, 1)
        self.assertEqual(fantasy1.year, 2021)
        self.assertEqual(fantasy1.round, 1)
        self.assertEqual(fantasy1.round_ranking, 1)
        self.assertEqual(fantasy1.round_salary, '$738,000.00')
        self.assertEqual(fantasy1.round_score, 141)
        self.assertEqual(fantasy1.round_value, 19.1)

        fantasy2 = fantasy_persisted[1]
        self.assertIsNotNone(fantasy2)
        self.assertEqual(fantasy2.player_id, 2)
        self.assertEqual(fantasy2.year, 2021)
        self.assertEqual(fantasy2.round, 1)
        self.assertEqual(fantasy2.round_ranking, 2)
        self.assertEqual(fantasy2.round_salary, '$675,000.00')
        self.assertEqual(fantasy2.round_score, 138)
        self.assertEqual(fantasy2.round_value, 20.4)

    def test_insert_fantasies_no_player_id_in_fantasy(self):
        # insert two good and one bad and assert that 2 are successfully inserted.
        invalid_fantasy_row = ['3', 'fake_player_name_not_in_db', 'essendon-bombers', '$607,000', '$738,000', '141', '19.1']
        self.fantasies.insert(1, (fantasyScrape.populate_fantasy('dream_team', invalid_fantasy_row, self.headers,
                                                                 2021, 1, TestFantasyScrape._engine)))
        fantasyScrape.insert_fantasies('dream_team', self.fantasies, 2021, 1, TestFantasyScrape._engine)
        with TestFantasyScrape.Session() as session:
            fantasy_persisted = session.query(PlayerFantasy).all()
        self.assertEqual(len(fantasy_persisted), 2)
        fantasy1 = fantasy_persisted[0]
        self.assertIsNotNone(fantasy1)
        self.assertEqual(fantasy1.player_id, 1)
        self.assertEqual(fantasy1.year, 2021)
        self.assertEqual(fantasy1.round, 1)
        self.assertEqual(fantasy1.round_ranking, 1)
        self.assertEqual(fantasy1.round_salary, '$738,000.00')
        self.assertEqual(fantasy1.round_score, 141)
        self.assertEqual(fantasy1.round_value, 19.1)

        fantasy2 = fantasy_persisted[1]
        self.assertIsNotNone(fantasy2)
        self.assertEqual(fantasy2.player_id, 2)
        self.assertEqual(fantasy2.year, 2021)
        self.assertEqual(fantasy2.round, 1)
        self.assertEqual(fantasy2.round_ranking, 2)
        self.assertEqual(fantasy2.round_salary, '$675,000.00')
        self.assertEqual(fantasy2.round_score, 138)
        self.assertEqual(fantasy2.round_value, 20.4)

    def tearDown(self):
        with TestFantasyScrape.Session() as cleanup_session:
            cleanup_session.query(PlayerFantasy).delete()
            cleanup_session.query(Player).delete()
            cleanup_session.commit()

    @classmethod
    def tearDownClass(cls):
        base.Base.metadata.drop_all(TestFantasyScrape._engine, checkfirst=False)


def add_player_to_db(player_id, name, team):
    # add player to put injury against
    player = Player()
    player.name_key = name
    player.id = player_id
    player.DOB = datetime.date(1990, 1, 1)
    player.team = team
    with TestFantasyScrape.Session() as player_session:
        player_session.add(player)
        player_session.commit()

