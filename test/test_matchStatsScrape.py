import os
import bs4
import get_html
from datascrape.repositories.player import Player
from test.BaseScraperTest import BaseScraperTest


class TestMatchStatsScrape(BaseScraperTest):
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    HTML_SOURCE_FILE = os.path.join(DIR_PATH, 'html_files', get_html.MATCH_STATS_FILE_NAME)
    HTML_SOURCE_FILE_ADV = os.path.join(DIR_PATH, 'html_files', get_html.MATCH_STATS_ADV_FILE_NAME)

    def setUp(self):
        with TestMatchStatsScrape.Session() as cleanup_session:
            cleanup_session.query(Player).delete()
            cleanup_session.execute("ALTER SEQUENCE player_id_seq RESTART WITH 1")
            cleanup_session.commit()
        # Stub html file used - to refresh file run get_html.py with 'players' as first arg
        with open(self.HTML_SOURCE_FILE, 'r') as file:
            soup = bs4.BeautifulSoup(file.read(), 'html.parser')

    def test_main(self):
        self.fail()

    def test_create_request_queue(self):
        self.fail()

    def test_send_request(self):
        self.fail()

    def test_process_response(self):
        self.fail()

    def test_process_row(self):
        self.fail()

    def test_scrape_stats(self):
        self.fail()

    def test_populate_stats(self):
        self.fail()

    def test_find_player_id(self):
        self.fail()

    def test_add_milestone(self):
        self.fail()

    def test_upsert_match_stats(self):
        self.fail()
