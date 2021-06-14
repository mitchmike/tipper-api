import datetime
import unittest
import bs4
import os
from datascrape import playerScrape


class TestPlayerScrape(unittest.TestCase):

    # for testing the entire html document
    HTML_SOURCE_FILE = 'richmond-player-scrape.html'
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    HTML_SOURCE_FILE = os.path.join(DIR_PATH, 'html_files', HTML_SOURCE_FILE)
    TEAM = 'richmond-tigers'

    # for testing an individual row
    HTML_ONE_ROW = '''<tr bgcolor="#f2f4f7" onmouseout="this.bgColor='#f2f4f7';" onmouseover="this.bgColor='#cbcdd0';">
                <td align="center" class="data">16</td>
                <td class="data" height="24"><a href="pp-richmond-tigers--jake-aarts">Aarts, Jake</a>
                <span class="playerflag" title="Rookie">R</span>
                </td>
                <td align="center" class="data">27</td>
                <td class="data">26yr 6mth</td><td class="data">8 Dec 1994</td><td align="center" class="data">177cm</td>
                <td align="center" class="data">75kg</td>
                <td class="data">Richmond Football Club</td>
                <td class="data">
                Forward
                </td></tr>'''

    def setUp(self):
        # Stub html file used - to refresh file run get_html.py with 'players' as first arg
        with open(self.HTML_SOURCE_FILE, 'r') as file:
            soup = bs4.BeautifulSoup(file.read(), 'html.parser')

        # TODO: stub out database connection

        data = soup.select('.data')
        self.first_row = data[0].parent
        self.last_row = data[-1].parent
        self.headers = [x.text for x in self.first_row.findPrevious('tr').find_all('a')]
        self.player_row = playerScrape.scrape_player(self.first_row)
        self.player = playerScrape.populate_player(self.player_row, self.headers, self.TEAM)

    def test_process_row(self):
        players = playerScrape.process_row(self.last_row, self.headers, self.TEAM, [])
        self.assertEqual(len(players), 1)
        player = players[0]
        self.assertEqual(player.first_name, 'Nick')
        self.assertEqual(player.last_name, 'Vlastuin')
        self.assertEqual(player.name_key, 'nick-vlastuin')
        self.assertEqual(player.team, 'richmond-tigers')
        self.assertEqual(player.DOB, datetime.date(1994, 4, 19))

    def test_process_row_multiple(self):
        players = playerScrape.process_row(self.first_row, self.headers, self.TEAM, [])
        self.assertEqual(len(players), 43)
        player_start = players[0]
        self.assertEqual(player_start.first_name, 'Jake')
        self.assertEqual(player_start.last_name, 'Aarts')
        self.assertEqual(player_start.name_key, 'jake-aarts')
        self.assertEqual(player_start.team, 'richmond-tigers')
        self.assertEqual(player_start.DOB, datetime.date(1994, 12, 8))
        player_end = players[-1]
        self.assertEqual(player_end.first_name, 'Nick')
        self.assertEqual(player_end.last_name, 'Vlastuin')
        self.assertEqual(player_end.name_key, 'nick-vlastuin')
        self.assertEqual(player_end.team, 'richmond-tigers')
        self.assertEqual(player_end.DOB, datetime.date(1994, 4, 19))

    def test_scrape_player(self):
        one_row_soup = bs4.BeautifulSoup(self.HTML_ONE_ROW, 'html.parser')
        row = one_row_soup.find('tr')
        player_row = playerScrape.scrape_player(row)
        self.assertEqual(len(player_row), 9)
        self.assertEqual(player_row[0], '16')
        self.assertEqual(player_row[1], 'jake-aarts')
        self.assertEqual(player_row[2], '27')
        self.assertEqual(player_row[3], '26yr 6mth')
        self.assertEqual(player_row[4], '8 Dec 1994')
        self.assertEqual(player_row[5], '177cm')
        self.assertEqual(player_row[6], '75kg')
        self.assertEqual(player_row[7], 'Richmond Football Club')
        self.assertEqual(player_row[8], 'Forward')

    def test_populate_player(self):
        test_player_row = [
            '16', 'jake-aarts', '27', '26yr 6mth', '8 Dec 1994', '177cm', '75kg', 'Richmond Football Club', 'Forward'
        ]
        player = playerScrape.populate_player(test_player_row, self.headers, self.TEAM)
        self.assertIsNotNone(player)
        self.assertEqual(player.team, self.TEAM)
        self.assertEqual(player.name_key, 'jake-aarts')
        self.assertEqual(player.first_name, 'Jake')
        self.assertEqual(player.last_name, 'Aarts')
        self.assertEqual(player.number, 16)
        self.assertEqual(player.games, 27)
        self.assertEqual(player.age, '26yr 6mth')
        self.assertEqual(player.DOB, datetime.date(1994, 12, 8))
        self.assertEqual(player.height, 177)
        self.assertEqual(player.weight, 75)
        self.assertEqual(player.position, 'Forward')

    def test_populate_player_3_names(self):
        test_player_row = [
            '16', 'micky-mick-joe', '27', '26yr 6mth', '8 Dec 1994', '177cm', '75kg', 'Richmond Football Club', 'Forward'
        ]
        player = playerScrape.populate_player(test_player_row, self.headers, self.TEAM)
        self.assertIsNotNone(player)
        self.assertEqual(player.team, self.TEAM)
        self.assertEqual(player.name_key, 'micky-mick-joe')
        self.assertEqual(player.first_name, 'Micky')
        self.assertEqual(player.last_name, 'Mick Joe')

    def test_populate_player_no_name(self):
        test_player_row = [
            '16', '', '27', '26yr 6mth', '8 Dec 1994', '177cm', '75kg', 'Richmond Football Club', 'Forward'
        ]
        with self.assertRaisesRegex(ValueError, 'Player row has no name') as e:
            player = playerScrape.populate_player(test_player_row, self.headers, self.TEAM)
            self.assertIsNone(player)

    def test_populate_player_no_DOB(self):
        test_player_row = [
            '16', 'jake-aarts', '27', '26yr 6mth', '', '177cm', '75kg', 'Richmond Football Club', 'Forward'
        ]
        with self.assertRaisesRegex(ValueError, 'Player row has no DateOfBirth') as e:
            player = playerScrape.populate_player(test_player_row, self.headers, self.TEAM)
            self.assertIsNone(player)

    def test_upsert_team_new_player(self):
        None

    def test_upsert_team_player_already_exists(self):
        None

    def test_upsert_team_exception(self):
        None

    def test_full_player_scrape(self):
        None

    def tearDown(self) -> None:
        None


if __name__ == '__main__':
    unittest.main()
