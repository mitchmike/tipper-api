from datetime import datetime
import logging.config
from datascrape.logging_config import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)

CURRENT_DATE = datetime.now()
CURRENT_YEAR = CURRENT_DATE.year
CALENDAR_DICT = {
    1: 'March 18',
    2: 'March 25',
    3: 'April 1',
    4: 'April 8',
    5: 'April 15',
    6: 'April 23',
    7: 'April 30',
    8: 'May 7',
    9: 'May 14',
    10: 'May 21',
    11: 'May 28',
    12: 'June 4',
    13: 'June 10',
    14: 'June 17',
    15: 'June 24',
    16: 'July 1',
    17: 'July 9',
    18: 'July 16',
    19: 'July 23',
    20: 'July 30',
    21: 'August 6',
    22: 'August 13',
    23: 'August 20',
}


def main():
    find_latest_round(CALENDAR_DICT, CURRENT_DATE)


def find_latest_round(calendar, current_date):
    round_start_date_dict = build_round_date_dict_from_calendar_dict(calendar)
    last_round = find_current_round(round_start_date_dict, current_date)
    return last_round


def build_round_date_dict_from_calendar_dict(calendar):
    round_start_date_dict = {}
    for round_number in calendar:
        round_start_date = datetime.strptime(calendar[round_number] + str(CURRENT_YEAR), '%B %d%Y')
        round_start_date_dict[round_number] = round_start_date
    return round_start_date_dict


def find_current_round(round_start_date_dict, current_date):
    last_round = 0
    next_round = None
    for round_number in round_start_date_dict:
        if current_date > round_start_date_dict[round_number]:
            last_round = round_number
            continue
        next_round = round_number
        break
    LOGGER.info("Current / Previous round is %s", last_round)
    if next_round is not None:
        LOGGER.info("Next round is %s", next_round)
    return last_round


if __name__ == '__main__':
    main()

