from flask import (
    Blueprint, request, jsonify
)
from sqlalchemy import or_, func

from api.db import new_session
from api.schema.fantasy_schema import FantasySchema
from api.schema.games.game_schema import GameSchema
from api.schema.games.game_schema_match_stats import GameMatchStatsSchema
from api.schema.match_stats_schema import MatchStatsSchema
from api.schema.player.player_injury import PlayerInjurySchema
from api.schema.supercoach_schema import SuperCoachSchema
from api.schema.team_schema import TeamSchema
from model import Game, Player, PlayerFantasy, PlayerSupercoach, MatchStatsPlayer, Team

bp = Blueprint('select_api', __name__, url_prefix='/select')
MAX_GAMES_FOR_STATS = 30


@bp.route('/teams')
def select_teams():
    with new_session() as session:
        data = select_data(session, Team, ('team_identifier', 'id')).all()
        schema = TeamSchema(many=True)
        return jsonify(schema.dump(data))


@bp.route("/games")
def select_games():
    with new_session() as session:
        data = select_data(session, Game, ('id', 'home_team', 'away_team', 'year'))
        # custom filters
        for key in request.args.keys():
            value = request.args.get(key)
            if key == 'team':
                data = data.filter(or_(Game.home_team == value, Game.away_team == value))
        data = data.order_by('year', 'round_number').all()
        includeStats = False
        if 'includeStats' in request.args.keys():
            if len(data) <= MAX_GAMES_FOR_STATS:
                includeStats = True
        schema = GameMatchStatsSchema(many=True) if includeStats else GameSchema(many=True)
        dump_data = schema.dump(data)
        return jsonify(dump_data)


@bp.route("/players")
def select_players():
    with new_session() as session:
        data = select_data(session, Player, ('id', 'team'))
        data = data.order_by('team', 'number').all()
        schema = PlayerInjurySchema(many=True)
        dump_data = schema.dump(data)
        return jsonify(dump_data)


@bp.route("/player_points")
def select_player_points():
    available_modes = ['supercoach', 'fantasy']
    mode = request.args.get('mode')
    if mode not in available_modes:
        return f"Required argument 'mode' is not valid. valid values: {available_modes}", 400
    model = PlayerSupercoach if mode == 'supercoach' else PlayerFantasy
    with new_session() as session:
        data = select_data(session, model, ('id', 'round', 'year'))
        for key in request.args.keys():
            value = request.args.get(key)
            if key == 'team':
                data = data.filter(model.player.has(team=value))
            if key == 'name_key':
                data = data.filter(model.player.has(name_key=value))
        data = data.order_by('year', 'round').all()
        schema = SuperCoachSchema(many=True) if mode == 'supercoach' else FantasySchema(many=True)
        dump_data = schema.dump(data)
        return jsonify(dump_data)


@bp.route("/match_stats")
def select_matchstats():
    required_param_opts = ['id', 'game_id']
    accept_request = False
    for opt in required_param_opts:
        if opt in request.args:
            accept_request = True
            break
    if not accept_request:
        return f"Endpoint requires at least one of the following request params: {required_param_opts}"
    with new_session() as session:
        data = select_data(session, MatchStatsPlayer, ('id', 'team', 'game_id'))
        data = data.order_by('id').all()
        schema = MatchStatsSchema(many=True)
        dump_data = schema.dump(data)
        return jsonify(dump_data)


@bp.route('/pcntdiff')
def select_pcnt_diff():
    for opt in ['team', 'year']:
        if opt not in request.args:
            print("required params not supplied")
            return {}
    team = request.args.get('team')
    year = request.args.get('year')
    with new_session() as session:
        return jsonify(get_pcnt_diff(session, team, [year]))


def get_pcnt_diff(session, team, years):
    try:
        # get game ids from games table
        games = session.query(Game).filter(Game.year.in_(years)) \
            .filter(or_(Game.home_team == team, Game.away_team == team)) \
            .with_entities(Game.id, Game.year, Game.round_number, Game.home_team, Game.away_team, Game.winner).all()
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
                score = teamsums[goals_i] * 6 + teamsums[behinds_i]
                pcntdiff = {'game_id': game_id, 'year': game.year, 'round_number': game.round_number,
                            'team_id': teamsums.team, 'opponent': opponentsums.team,
                            'home_game': 1 if teamsums.team == game.home_team else 0,
                            'win': 1 if teamsums.team == game.winner else 0,
                            'score': score}
                i = 0
                for ts, os in zip(teamsums[2:], opponentsums[2:]):
                    pcntdiff[MatchStatsPlayer.summable_cols()[i]] = 0 if os == 0 else (ts - os) / os
                    i += 1
                pcntdiffs.append(pcntdiff)
        pcntdiffs = sorted(pcntdiffs, key=lambda i: int(i['round_number']))
        return pcntdiffs
    except Exception as e:
        print(e)
        return {}


def select_data(session, model, filters):
    data = session.query(model)
    for key in request.args.keys():
        value = request.args.get(key)
        if key in filters:
            data = data.filter(getattr(model, key) == value)
    return data
