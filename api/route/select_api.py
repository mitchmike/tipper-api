from flask import (
    Blueprint, request, jsonify
)
from sqlalchemy import or_

from api.db import get_db_session_factory
from api.schema.fantasy_schema import FantasySchema
from api.schema.games.game_schema import GameSchema
from api.schema.games.game_schema_match_stats import GameMatchStatsSchema
from api.schema.match_stats_schema import MatchStatsSchema
from api.schema.player.player_injury import PlayerInjurySchema
from api.schema.supercoach_schema import SuperCoachSchema
from model import Game, Player, PlayerFantasy, PlayerSupercoach, MatchStatsPlayer

bp = Blueprint('select_api', __name__, url_prefix='/select')
MAX_GAMES_FOR_STATS = 30

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


def select_data(model, filters):
    Session = get_db_session_factory()
    session = Session()
    data = session.query(model)
    for key in request.args.keys():
        value = request.args.get(key)
        if key in filters:
            data = data.filter(getattr(model, key) == value)
    return data
