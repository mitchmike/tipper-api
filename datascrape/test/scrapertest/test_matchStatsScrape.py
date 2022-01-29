import os
from datascrape.test import get_html
from datascrape.test.scrapertest.BaseScraperTest import BaseScraperTest, TEST_DB_CONN_STRING
from datascrape.scrapers.match_statsScrape import *


class TestMatchStatsScrape(BaseScraperTest):
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    HTML_SOURCE_FILE = os.path.join(DIR_PATH, '../html_files', get_html.MATCH_STATS_FILE_NAME)
    HTML_SOURCE_FILE_ADV = os.path.join(DIR_PATH, '../html_files', get_html.MATCH_STATS_ADV_FILE_NAME)

    def setUp(self):
        with TestMatchStatsScrape.Session() as cleanup_session:
            cleanup_session.query(Player).delete()
            cleanup_session.query(MatchStatsPlayer).delete()
            cleanup_session.query(Milestone).delete()
            cleanup_session.query(Game).delete()
            cleanup_session.execute("ALTER SEQUENCE player_id_seq RESTART WITH 1")
            cleanup_session.execute("ALTER SEQUENCE match_stat_id_seq RESTART WITH 1")
            cleanup_session.commit()
        # Stub html file used - to refresh file run get_html.py with 'players' as first arg
        with open(self.HTML_SOURCE_FILE, 'r') as file:
            soup = bs4.BeautifulSoup(file.read(), 'lxml')
        self.milestone_recorder = MileStoneRecorder(TestMatchStatsScrape._engine)

    def test_populate_request_queue(self):
        with TestMatchStatsScrape.Session() as add_games_for_test:
            add_games_for_test.add(Game(1, 'a', 'b', 2021, 1))
            add_games_for_test.add(Game(7, 'c', 'd', 2021, 1))
            add_games_for_test.add(Game(10, 'a', 'b', 2021, 5))  # out of round_number range
            add_games_for_test.commit()
        request_q = populate_request_queue(2021, 2021, 1, 4, TestMatchStatsScrape._engine)
        self.assertEqual(request_q.unfinished_tasks, 4)
        first_queue_item = request_q.get()
        self.assertEqual(first_queue_item['year'], 2021)
        self.assertEqual(first_queue_item['round_number'], 1)
        self.assertEqual(first_queue_item['mode'], 'basic')

    def test_process_response(self):
        with TestMatchStatsScrape.Session() as add_games_for_test:
            add_games_for_test.add(Game(10327, 'richmond', 'carlton', 2021, 1))
            add_games_for_test.commit()
        with open(self.HTML_SOURCE_FILE, 'r') as file:
            response = {'year': 2021, 'round_number': 1, 'match_id': 10327, 'mode': 'basic',
                        'url': 'not_required_for_test',
                        'response': file.read()}
        process_response(response, self.milestone_recorder, TestMatchStatsScrape._engine)
        with TestMatchStatsScrape.Session() as check_result:
            match_stats_persisted = check_result.query(MatchStatsPlayer).all()
        self.assertEqual(len(match_stats_persisted), 46)
        match_stats_player = match_stats_persisted[0]
        self.assertEqual(match_stats_player.game_id, 10327)
        self.assertEqual(match_stats_player.team, 'richmond-tigers')
        self.assertEqual(match_stats_player.player_name, 'jack-graham')
        self.assertEqual(match_stats_player.player_id, None)
        self.assertEqual(match_stats_player.kicks, 22)
        self.assertEqual(match_stats_player.handballs, 11)
        self.assertEqual(match_stats_player.disposals, 33)
        self.assertEqual(match_stats_player.marks, 5)
        self.assertEqual(match_stats_player.goals, 0)
        self.assertEqual(match_stats_player.behinds, 1)
        self.assertEqual(match_stats_player.tackles, 3)
        self.assertEqual(match_stats_player.hit_outs, 0)
        self.assertEqual(match_stats_player.goal_assists, 1)
        self.assertEqual(match_stats_player.inside_50s, 11)
        self.assertEqual(match_stats_player.clearances, 5)
        self.assertEqual(match_stats_player.clangers, 4)
        self.assertEqual(match_stats_player.rebound_50s, 1)
        self.assertEqual(match_stats_player.frees_for, 2)
        self.assertEqual(match_stats_player.frees_against, 1)

    def test_process_row(self):
        row_string = (
            '<tr bgcolor="#f2f4f7" onmouseout="this.bgColor=\'#f2f4f7\';" onmouseover="this.bgColor=\'#cbcdd0\';">\n'
            '<td align="left" height="18"><a href="pp-richmond-tigers--jack-graham" title="Jack Graham">Jack Graham</a></td>\n'
            '<td class="statdata">22</td>\n'
            '<td class="statdata">11</td>\n'
            '<td class="statdata">33</td>\n'
            '<td class="statdata">5</td>\n'
            '<td class="statdata">0</td>\n'
            '<td class="statdata">1</td>\n'
            '<td class="statdata">3</td>\n'
            '<td class="statdata">0</td>\n'
            '<td class="statdata">1</td>\n'
            '<td class="statdata">11</td>\n'
            '<td class="statdata">5</td>\n'
            '<td class="statdata">4</td>\n'
            '<td class="statdata">1</td>\n'
            '<td class="statdata">2</td>\n'
            '<td class="statdata">1</td>\n'
            '<td class="statdata">115</td>\n'
            '<td class="statdata">120</td>\n'
            '</tr>')
        row = bs4.BeautifulSoup(row_string, 'lxml')
        headers = ['Player', 'K', 'HB', 'D', 'M', 'G', 'B', 'T', 'HO', 'GA', 'I50', 'CL', 'CG', 'R50', 'FF', 'FA', 'AF', 'SC']
        match_id = 10_000
        match_stats_list = process_row(row, headers, [], match_id, TestMatchStatsScrape._engine)
        self.assertEqual(len(match_stats_list), 1)
        match_stats_player = match_stats_list[0]
        self.assertEqual(match_stats_player.game_id, 10_000)
        self.assertEqual(match_stats_player.team, 'richmond-tigers')
        self.assertEqual(match_stats_player.player_name, 'jack-graham')
        self.assertEqual(match_stats_player.player_id, None)
        self.assertEqual(match_stats_player.kicks, 22)
        self.assertEqual(match_stats_player.handballs, 11)
        self.assertEqual(match_stats_player.disposals, 33)
        self.assertEqual(match_stats_player.marks, 5)
        self.assertEqual(match_stats_player.goals, 0)
        self.assertEqual(match_stats_player.behinds, 1)
        self.assertEqual(match_stats_player.tackles, 3)
        self.assertEqual(match_stats_player.hit_outs, 0)
        self.assertEqual(match_stats_player.goal_assists, 1)
        self.assertEqual(match_stats_player.inside_50s, 11)
        self.assertEqual(match_stats_player.clearances, 5)
        self.assertEqual(match_stats_player.clangers, 4)
        self.assertEqual(match_stats_player.rebound_50s, 1)
        self.assertEqual(match_stats_player.frees_for, 2)
        self.assertEqual(match_stats_player.frees_against, 1)

    def test_scrape_stats(self):
        row_string = (
            '<tr bgcolor="#f2f4f7" onmouseout="this.bgColor=\'#f2f4f7\';" onmouseover="this.bgColor=\'#cbcdd0\';">\n'
            '<td align="left" height="18"><a href="pp-richmond-tigers--jack-graham" title="Jack Graham">Jack Graham</a></td>\n'
            '<td class="statdata">22</td>\n'
            '<td class="statdata">11</td>\n'
            '<td class="statdata">33</td>\n'
            '<td class="statdata">5</td>\n'
            '<td class="statdata">0</td>\n'
            '<td class="statdata">1</td>\n'
            '<td class="statdata">3</td>\n'
            '<td class="statdata">0</td>\n'
            '<td class="statdata">1</td>\n'
            '<td class="statdata">11</td>\n'
            '<td class="statdata">5</td>\n'
            '<td class="statdata">4</td>\n'
            '<td class="statdata">1</td>\n'
            '<td class="statdata">2</td>\n'
            '<td class="statdata">1</td>\n'
            '<td class="statdata">115</td>\n'
            '<td class="statdata">120</td>\n'
            '</tr>')
        row = bs4.BeautifulSoup(row_string, 'lxml')
        stats_row = scrape_stats_one_row(row)
        self.assertEqual(stats_row, [['richmond-tigers', 'jack-graham'], '22', '11', '33', '5', '0', '1', '3', '0', '1',
                                     '11', '5', '4', '1', '2', '1', '115', '120'])

    def test_populate_stats(self):
        player = Player('clayton-oliver', 'melbourne-demons', datetime.date(1, 1, 1))
        player.id = 5
        with TestMatchStatsScrape.Session() as session:
            session.add(player)
            session.commit()
        stat_row = [['melbourne-demons', 'clayton-oliver'], '10', '25', '35', '6', '1', '2', '3', '4', '5', '3', '7',
                    '5', '3', '0', '1', '107', '122']
        headers = ['Player', 'K', 'HB', 'D', 'M', 'G', 'B', 'T', 'HO', 'GA', 'I50', 'CL', 'CG', 'R50', 'FF', 'FA', 'AF',
                   'SC']
        match_id = 10_000
        match_stats_player = populate_stats(stat_row, headers, match_id,
                                            TestMatchStatsScrape._engine)
        self.assertEqual(match_stats_player.game_id, 10_000)
        self.assertEqual(match_stats_player.team, 'melbourne-demons')
        self.assertEqual(match_stats_player.player_name, 'clayton-oliver')
        self.assertEqual(match_stats_player.player_id, 5)
        self.assertEqual(match_stats_player.kicks, 10)
        self.assertEqual(match_stats_player.handballs, 25)
        self.assertEqual(match_stats_player.disposals, 35)
        self.assertEqual(match_stats_player.marks, 6)
        self.assertEqual(match_stats_player.goals, 1)
        self.assertEqual(match_stats_player.behinds, 2)
        self.assertEqual(match_stats_player.tackles, 3)
        self.assertEqual(match_stats_player.hit_outs, 4)
        self.assertEqual(match_stats_player.goal_assists, 5)
        self.assertEqual(match_stats_player.inside_50s, 3)
        self.assertEqual(match_stats_player.clearances, 7)
        self.assertEqual(match_stats_player.clangers, 5)
        self.assertEqual(match_stats_player.rebound_50s, 3)
        self.assertEqual(match_stats_player.frees_for, 0)
        self.assertEqual(match_stats_player.frees_against, 1)

    def test_find_player_id(self):
        player = Player('michael-john', 'richmond', datetime.datetime.strptime('17 May 1993', '%d %b %Y').date())
        player.id = 12
        with TestMatchStatsScrape.Session() as session:
            session.add(player)
            session.commit()
        player_id = find_player_id('richmond', 'michael-john',
                                   TestMatchStatsScrape._engine)
        self.assertEqual(player_id, 12)
        player_id_none = find_player_id('richmond', 'michael-jackson',
                                        TestMatchStatsScrape._engine)
        self.assertEqual(player_id_none, None)

    def test_add_milestone(self):
        add_milestone('1234', 'advanced', 'milestone_1', self.milestone_recorder)
        self.milestone_recorder.commit_milestones()
        with TestMatchStatsScrape.Session() as session:
            persisted_milestone = session.query(Milestone).all()
        self.assertEqual(len(persisted_milestone), 1)
        self.assertEqual(persisted_milestone[0].match_id, 1234)
        self.assertEqual(persisted_milestone[0].mode, 'advanced')
        self.assertEqual(persisted_milestone[0].milestone, 'milestone_1')

