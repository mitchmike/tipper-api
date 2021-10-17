from unittest import TestCase
from datetime import datetime
from util.latest_round import find_latest_round


class TestLatestRound(TestCase):
    START_DATES = {
        1: 'March 18',
        2: 'March 25',
        3: 'April 1',
        4: 'April 8'
    }

    def test_current_date_before_calendar_start(self):
        current_date = datetime.strptime('March 17' + str(2021), '%B %d%Y')
        self.runTest(current_date, 0)

    def test_current_date_after_calendar_end(self):
        current_date = datetime.strptime('April 9' + str(2021), '%B %d%Y')
        self.runTest(current_date, 4)

    def test_current_date_on_specific_calendar_date(self):
        current_date = datetime.strptime('March 25' + str(2021), '%B %d%Y')
        self.runTest(current_date, 1)

    def test_current_date_between_calendar_dates(self):
        current_date = datetime.strptime('March 26' + str(2021), '%B %d%Y')
        self.runTest(current_date, 2)

    def runTest(self, current_date, expected_round):
        latest_round = find_latest_round(self.START_DATES, current_date)
        self.assertEqual(latest_round, expected_round)
