from flask import (
    Blueprint, request, jsonify
)
from sqlalchemy import or_, func

from api.db import get_db_session_factory
from api.schema.fantasy_schema import FantasySchema
from api.schema.games.game_schema import GameSchema
from api.schema.games.game_schema_match_stats import GameMatchStatsSchema
from api.schema.match_stats_schema import MatchStatsSchema
from api.schema.player.player_injury import PlayerInjurySchema
from api.schema.supercoach_schema import SuperCoachSchema
from api.schema.team_schema import TeamSchema
from model import Game, Player, PlayerFantasy, PlayerSupercoach, MatchStatsPlayer
from model.team import Team

bp = Blueprint('select_api', __name__, url_prefix='/select')
MAX_GAMES_FOR_STATS = 30


@bp.route('/teams')
def select_teams():
    data = select_data(Team, ('team_identifier', )).all()
    schema = TeamSchema(many=True)
    return jsonify(schema.dump(data))


@bp.route("/games")
def select_games():
    data = select_data(Game, ('id', 'home_team', 'away_team', 'year'))
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
    data = select_data(Player, ('id', 'team'))
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
    data = select_data(model, ('id', 'round', 'year'))
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
    data = select_data(MatchStatsPlayer, ('id', 'team', 'game_id'))
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
    try:
        team = request.args.get('team')
        year = request.args.get('year')
        Session = get_db_session_factory()
        session = Session()
        # get game ids from games table
        games = session.query(Game).filter(Game.year == year)\
            .filter(or_(Game.home_team == team, Game.away_team == team)) \
            .with_entities(Game.id, Game.year, Game.round_number).all()
        game_ids = [game.id for game in games]
        # get matchstats for these game ids
        sum_cols = [func.sum(getattr(MatchStatsPlayer, i)) for i in MatchStatsPlayer.summable_cols()]
        q = session.query(MatchStatsPlayer)\
            .with_entities(MatchStatsPlayer.game_id, MatchStatsPlayer.team, *sum_cols) \
            .filter(MatchStatsPlayer.game_id.in_(game_ids)) \
            .group_by(MatchStatsPlayer.game_id, MatchStatsPlayer.team)
        sums = q.all()
        pcntdiffs = []
        for game_id in game_ids:
            teamsums = [game for game in sums if game[0] == game_id and game[1] == team]
            opponentsums = [game for game in sums if game[0] == game_id and game[1] != team]
            game = [game for game in games if game.id == game_id]
            if len(teamsums) > 0 and len(opponentsums) > 0 and len(game) > 0:
                teamsums = teamsums[0]
                opponentsums = opponentsums[0]
                game = game[0]
                pcntdiff = {'game_id': game_id, 'year': game.year, 'round_number': game.round_number,
                            'team_id': teamsums[1], 'opponent': opponentsums[1]}
                i = 0
                for ts, os in zip(teamsums[2:], opponentsums[2:]):
                    pcntdiff[MatchStatsPlayer.summable_cols()[i]] = 0 if os == 0 else (ts - os) / os
                    i += 1
                pcntdiffs.append(pcntdiff)
        pcntdiffs = sorted(pcntdiffs, key=lambda i: int(i['round_number']))
        return jsonify(pcntdiffs)
    except Exception as e:
        print(e)
        return {}


def select_data(model, filters):
    Session = get_db_session_factory()
    session = Session()
    data = session.query(model)
    for key in request.args.keys():
        value = request.args.get(key)
        if key in filters:
            data = data.filter(getattr(model, key) == value)
    return data
