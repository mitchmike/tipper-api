import itertools
from functools import cmp_to_key
from flask import Blueprint, request

from tipperapi.db import get_db_session_factory
from model import Game

bp = Blueprint('ladder', __name__, url_prefix='/ladder')


@bp.route('/')
def ladder():
    year = request.args['year']
    return get_ladder(year)


def get_ladder(year):
    try:
        Session = get_db_session_factory()
        session = Session()
        games = session.query(Game).filter(Game.year == year)
        games = games.filter(Game.round_number < 25)  # exclude finals rounds
        games = games.with_entities(Game.home_team, Game.away_team, Game.winner, Game.home_score, Game.away_score)

        # distinct teams
        teams_h = games.with_entities(Game.home_team).distinct().all()
        teams_a = games.with_entities(Game.away_team).distinct().all()
        teams = set()
        for team in itertools.chain(teams_a, teams_h):
            teams.add(team[0])
        # create ladder objects
        lad = []
        for team in teams:
            lad.append(LadderRung(team))

        # add scores to ladder
        game_data = games.all()
        for game in game_data:
            update_rung(lad, game.winner, game.home_team, game.home_score, game.away_score)
            update_rung(lad, game.winner, game.away_team, game.away_score, game.home_score)

        sort_l = sorted(lad, key=cmp_to_key(LadderRung.compare))
        return [rung.__dict__ for rung in sort_l]
    except Exception as e:
        print(f'Encountered exception while processing ladder request: {e}')
        return []


def update_rung(l, winner, team, pf, pa):
    rung = [rung for rung in l if rung.teamname == team][0]
    if winner == 'DRAW':
        rung.draws += 1
    elif team == winner:
        rung.wins += 1
    else:
        rung.losses += 1
    rung.pf += pf
    rung.pa += pa


class LadderRung:

    def __init__(self, teamname):
        self.teamname = teamname
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.pf = 0
        self.pa = 0

    def points(self):
        return self.wins * 4 + self.draws * 2

    def pcntage(self):
        return 0 if self.pa == 0 else self.pf / self.pa

    @staticmethod
    def compare(a, b):
        if a.points() > b.points():
            return -1
        elif a.points() == b.points() and a.pcntage() > b.pcntage():
            return -1
        else:
            return 1
