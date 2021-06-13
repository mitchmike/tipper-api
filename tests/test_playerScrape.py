import unittest
import bs4
import requests

from datascrape import playerScrape


class TestPlayerScrape(unittest.TestCase):

    def setUp(self):
        print('setting up tests')
        # TODO: Stub out all of this sample data
        self.team = 'richmond-tigers'
        res = requests.get(f'https://www.footywire.com/afl/footy/tp-{self.team}')
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        data = soup.select('.data')
        self.first_row = data[0].parent
        self.headers = [x.text for x in self.first_row.findPrevious('tr').find_all('a')]
        self.player_row = playerScrape.scrape_player(self.first_row)
        self.player = playerScrape.populate_player(self.player_row,self.headers,self.team)

    def test_scrape_player(self):
        player_row = playerScrape.scrape_player(self.first_row)
        print(player_row)
        self.assertEqual(len(player_row), 9)
        self.assertEqual(int(player_row[0]), 16)

    def test_populate_player(self):
        player = playerScrape.populate_player(self.player_row,self.headers,self.team)
        self.assertIsNotNone(player)
        self.assertEqual(player.team, self.team)
        self.assertEqual(player.name_key, 'jake-aarts')
        self.assertEqual(int(player.number), 16)


if __name__ == '__main__':
    unittest.main()
