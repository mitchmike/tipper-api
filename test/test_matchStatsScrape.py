import os
import bs4
import datascrape.scrapers.match_statsScrape
import get_html
from datascrape.MilestoneRecorder import MileStoneRecorder
from datascrape.repositories.milestone import Milestone
from datascrape.repositories.player import Player
from test.BaseScraperTest import BaseScraperTest, TEST_DB_CONN_STRING


class TestMatchStatsScrape(BaseScraperTest):
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    HTML_SOURCE_FILE = os.path.join(DIR_PATH, 'html_files', get_html.MATCH_STATS_FILE_NAME)
    HTML_SOURCE_FILE_ADV = os.path.join(DIR_PATH, 'html_files', get_html.MATCH_STATS_ADV_FILE_NAME)

    def setUp(self):
        with TestMatchStatsScrape.Session() as cleanup_session:
            cleanup_session.query(Player).delete()
            cleanup_session.query(Milestone).delete()
            cleanup_session.execute("ALTER SEQUENCE player_id_seq RESTART WITH 1")
            cleanup_session.commit()
        # Stub html file used - to refresh file run get_html.py with 'players' as first arg
        with open(self.HTML_SOURCE_FILE, 'r') as file:
            soup = bs4.BeautifulSoup(file.read(), 'html.parser')
        self.milestone_recorder = MileStoneRecorder(TEST_DB_CONN_STRING)

    def test_populate_request_queue(self):
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
        datascrape.scrapers.match_statsScrape.add_milestone('1234', 'advanced', 'milestone_1', self.milestone_recorder)
        self.milestone_recorder.commit_milestones()
        with TestMatchStatsScrape.Session() as session:
            persisted_milestone = session.query(Milestone).all()
        self.assertEqual(len(persisted_milestone), 1)
        self.assertEqual(persisted_milestone[0].match_id, 1234)
        self.assertEqual(persisted_milestone[0].mode, 'advanced')
        self.assertEqual(persisted_milestone[0].milestone, 'milestone_1')

    def test_upsert_match_stats(self):
        self.fail()
