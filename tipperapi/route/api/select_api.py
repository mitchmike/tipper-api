from flask import (
    Blueprint, request, jsonify
)
from sqlalchemy import or_, desc, and_

from tipperapi.db import new_session
from tipperapi.route.admin.db_mgmt_api import safe_int
from tipperapi.schema.fantasy_schema import FantasySchema
from tipperapi.schema.games.game_schema import GameSchema
from tipperapi.schema.games.game_schema_match_stats import GameMatchStatsSchema
from tipperapi.schema.match_stats_schema import MatchStatsSchema
from tipperapi.schema.player.player_injury import PlayerInjurySchema
from tipperapi.schema.supercoach_schema import SuperCoachSchema
from tipperapi.schema.team_schema import TeamSchema
from model import Game, Player, PlayerFantasy, PlayerSupercoach, MatchStatsPlayer, Team
from predictions.aggregated_match_stats import get_pcnt_diff, ALL_ROUNDS

bp = Blueprint('select_api', __name__, url_prefix='/select')
MAX_GAMES_FOR_STATS = 30


@bp.route('/teams')
def select_teams():
    with new_session() as session:
        data = select_data(session, Team, ('team_identifier', 'id'), request.args).all()
        schema = TeamSchema(many=True)
        return jsonify(schema.dump(data))


@bp.route("/recent_year_rounds")
def recent_year_rounds():
    lastXRounds = request.args.get('lastXRounds')
    tuples = [(t[0], t[1]) for t in get_recent_year_rounds(lastXRounds)]
    return jsonify(tuples)


def get_recent_year_rounds(lastXRounds):
    with new_session() as session:
        year_rounds = session.query(Game).with_entities(Game.year, Game.round_number) \
            .group_by(Game.year, Game.round_number) \
            .order_by(desc(Game.year), desc(Game.round_number)) \
            .limit(lastXRounds).all()
    return year_rounds


@bp.route("/games")
def select_games():
    return jsonify(get_games(request.args))


def get_games(args):
    with new_session() as session:
        data = select_data(session, Game, ('id', 'home_team', 'away_team', 'year'), args)
        # custom filters
        for key in args.keys():
            value = args.get(key)
            if key == 'team':
                data = data.filter(or_(Game.home_team == value, Game.away_team == value))
            if key == 'lastXRounds':
                last_x_games = get_recent_year_rounds(value)
                earliest = last_x_games[-1]
                data = data.filter(
                    or_(Game.year > earliest[0], and_(Game.year == earliest[0], Game.round_number >= earliest[1])))
        data = data.order_by('year', 'round_number').all()
        includeStats = False
        if 'includeStats' in args.keys():
            if len(data) <= MAX_GAMES_FOR_STATS:
                includeStats = True
        schema = GameMatchStatsSchema(many=True) if includeStats else GameSchema(many=True)
        return schema.dump(data)


@bp.route("/players")
def select_players():
    with new_session() as session:
        data = select_data(session, Player, ('id', 'team'), request.args)
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
        data = select_data(session, model, ('id', 'round', 'year'), request.args)
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
        data = select_data(session, MatchStatsPlayer, ('id', 'team', 'game_id'), request.args)
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
    year = safe_int(request.args.get('year'))
    with new_session() as session:
        return jsonify(get_pcnt_diff(session, team, [(year, ALL_ROUNDS)]))


def select_data(session, model, filters, args):
    data = session.query(model)
    for key in args.keys():
        value = args.get(key)
        if key in filters:
            data = data.filter(getattr(model, key) == value)
    return data
