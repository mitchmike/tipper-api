import requests
import sys
import os
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
HTML_OUTPUT_PATH = os.path.join(DIR_PATH, 'html_files')
PLAYER_FILE_NAME = 'richmond-player-scrape.html'
INJURY_FILE_NAME = 'injuries.html'
FANTASY_FILE_NAME = '2021-r1-fantasy-points.html'
SUPERCOACH_FILE_NAME = '2021-r1-supercoach-points.html'
GAMES_FILE_NAME = '2019-games.html'
MATCH_STATS_FILE_NAME = '2021-r1-rich-carl-match-stats.html'
MATCH_STATS_ADV_FILE_NAME = '2021-r1-rich-carl-match-stats-adv.html'

REQUEST_MAPS = [
    # {'file': 'players',
    #  'file_name': PLAYER_FILE_NAME,
    #  'link': 'https://www.footywire.com/afl/footy/tp-richmond-tigers'},
    # {'file': 'injuries',
    #  'file_name': INJURY_FILE_NAME,
    #  'link': 'https://www.footywire.com/afl/footy/injury_list'},
    # {'file': 'fantasy',
    #  'file_name': FANTASY_FILE_NAME,
    #  'link': 'https://www.footywire.com/afl/footy/dream_team_round?year=2021&round=1&p=&s=T'},
    # {'file': 'supercoach',
    #  'file_name': SUPERCOACH_FILE_NAME,
    #  'link': 'https://www.footywire.com/afl/footy/supercoach_round?year=2021&round=1&p=&s=T'},
    # {'file': 'games',
    #  'file_name': GAMES_FILE_NAME,
    #  'link': 'https://www.footywire.com/afl/footy/ft_match_list?year=2019'},
    # {'file': 'matchStats',
    #  'file_name': MATCH_STATS_FILE_NAME,
    #  'link': 'https://www.footywire.com/afl/footy/ft_match_statistics?mid=10327'},
    # {'file': 'matchStatsAdv',
    #  'file_name': MATCH_STATS_ADV_FILE_NAME,
    #  'link': 'https://www.footywire.com/afl/footy/ft_match_statistics?mid=10327$advv=Y'}
]
AVAILABLE_FILES = [x['file'] for x in REQUEST_MAPS]


def main(file):
    if file_mode == 'all':
        for request in REQUEST_MAPS:
            write_file(request)
    else:
        request = [x for x in REQUEST_MAPS if x['file'] == file][0]
        write_file(request)


def write_file(request):
    print(f"Processing for {request['file']}")
    try:
        filepath = os.path.join(HTML_OUTPUT_PATH, request['file_name'])
        with open(filepath, 'w') as file:
            res = requests.get(request['link'])
            print(f'Writing file to {filepath}')
            file.write(res.text)
    except OSError as e:
        print(f'Caught exception creating file for: {request}')


def usage():
    print(f'Usage: To generate all files: python ./<script>.py default'
          f'\n\tTo generate specific files: python ./<script>.py <file> with file from {AVAILABLE_FILES}')


if __name__ == '__main__':
    if not os.path.exists(HTML_OUTPUT_PATH):
        os.makedirs(HTML_OUTPUT_PATH)
    if len(sys.argv) == 2:
        file_mode = sys.argv[1]
        if file_mode in AVAILABLE_FILES or file_mode == 'all':
            main(file_mode)
        else:
            usage()
    else:
        usage()
