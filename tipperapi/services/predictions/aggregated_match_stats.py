from sqlalchemy import or_, func
import logging.config

from datascrape.logging_config import LOGGING_CONFIG
from model import Game, MatchStatsPlayer
logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)

ALL_ROUNDS = -1


def get_pcnt_diff(session, team, year_rounds):
    try:
        games = get_games(session, team, year_rounds)
        game_ids = [game.id for game in games]
        # get matchstats for these game ids
        sum_cols = [func.sum(getattr(MatchStatsPlayer, i)) for i in MatchStatsPlayer.summable_cols()]
        stats_q = session.query(MatchStatsPlayer) \
            .with_entities(MatchStatsPlayer.game_id, MatchStatsPlayer.team, *sum_cols) \
            .filter(MatchStatsPlayer.game_id.in_(game_ids)) \
            .group_by(MatchStatsPlayer.game_id, MatchStatsPlayer.team)
        sums = stats_q.all()
        pcntdiffs = []
        for game_id in game_ids:
            teamsums = [game for game in sums if game[0] == game_id and game[1] == team]
            opponentsums = [game for game in sums if game[0] == game_id and game[1] != team]
            game = [game for game in games if game.id == game_id]
            if len(teamsums) > 0 and len(opponentsums) > 0 and len(game) > 0:
                teamsums = teamsums[0]
                opponentsums = opponentsums[0]
                game = game[0]
                col_offset = 2  # game_id and teamname cols
                goals_i = MatchStatsPlayer.summable_cols().index('goals') + col_offset
                behinds_i = MatchStatsPlayer.summable_cols().index('behinds') + col_offset
                score = None
                if teamsums[goals_i] is not None and teamsums[behinds_i] is not None:
                    score = (teamsums[goals_i] * 6 + teamsums[behinds_i])
                pcntdiff = {'game_id': game_id, 'year': game.year, 'round_number': game.round_number,
                            'team_id': teamsums.team, 'opponent': opponentsums.team,
                            'home_game': 1 if teamsums.team == game.home_team else 0,
                            'win': 1 if teamsums.team == game.winner else 0,
                            'score': score}
                i = 0
                for ts, os in zip(teamsums[2:], opponentsums[2:]):
                    if ts is not None and os is not None:
                        pcntdiff[MatchStatsPlayer.summable_cols()[i]] = 0.0 if os == 0 else (ts - os) / os
                    i += 1
                pcntdiffs.append(pcntdiff)
        pcntdiffs = sorted(pcntdiffs, key=lambda i: int(i['round_number']))
        return pcntdiffs
    except Exception as e:
        LOGGER.error(f'Exception occured while calculating pcnt diff stats: {e}')
        return {}


def get_games(session, team, year_rounds):
    years = set({})
    for yr in year_rounds:
        years.add(yr[0])
    # just one query for all years mentioned, then reduce
    games = session.query(Game).filter(Game.year.in_(years)) \
        .filter(or_(Game.home_team == team, Game.away_team == team)) \
        .with_entities(Game.id, Game.year, Game.round_number, Game.home_team, Game.away_team, Game.winner).all()
    result = []
    for g in games:
        for y, r in year_rounds:
            if g.year == y and (g.round_number == r or r == ALL_ROUNDS):
                result.append(g)
                break
    return result
