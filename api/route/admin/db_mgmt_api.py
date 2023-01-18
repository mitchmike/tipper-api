import datetime

from flask import Blueprint, render_template, request, flash, redirect, url_for

from api.db import get_db_session_factory
from api.route.auth import admin_required
from api.services.utils import safe_int
from model import Injury, PlayerFantasy, Player, PlayerSupercoach, MatchStatsPlayer, Game

bp = Blueprint('db_mgmt_api', __name__, url_prefix='/database')


@bp.route("/")
@admin_required
def db_mgmt_home():
    return render_template("admin/database_management.html")


@bp.route("/update_table_data")
@admin_required
def trigger_table_update():
    # update selected data from a table based on where clause
    return None


@bp.route("/clean_table_data", methods=('POST',))
@admin_required
def trigger_table_clean():
    # delete all or selected data from a table
    table_name = request.form['table_name']
    if table_name in model_map.keys():
        model, filters = model_map[table_name]
        Session = get_db_session_factory()
        session = Session()
        data = session.query(model)
        try:
            for model_filter in filters.keys():
                if model_filter == 'year':
                    from_year = safe_int(request.form['from_year'])
                    to_year = safe_int(request.form['to_year'])
                    data = year_filter(data, model, filters[model_filter], from_year, True)
                    data = year_filter(data, model, filters[model_filter], to_year, False)
                if model_filter == 'round':
                    from_round = safe_int(request.form['from_round'])
                    to_round = safe_int(request.form['to_round'])
                    data = round_filter(data, model, filters[model_filter], from_round, True)
                    data = round_filter(data, model, filters[model_filter], to_round, False)
                if model_filter == 'game_id':
                    game_id = safe_int(request.form['game_id'])
                    data = id_filter(data, model, filters[model_filter], game_id)
        except Exception as e:
            print(e)
            flash(f'Exception occured whilst processing request - no data was deleted')
            return redirect(url_for('admin.db_mgmt_api.db_mgmt_home'))
        rows = data.delete()
        session.commit()
        flash(f'{rows} rows deleted')
    else:
        flash(f'Invalid table selected. Not doing anything')
    return redirect(url_for('admin.db_mgmt_api.db_mgmt_home'))


@bp.route("/backup_table")
@admin_required
def trigger_table_backup():
    # create a backup of a chosen table (or full db)
    return None


@bp.route("/table_restore")
@admin_required
def trigger_table_restore():
    # restore from backup
    return None


def id_filter(data, model, field_name, value):
    if value is not None:
        data = data.filter(getattr(model, field_name) == value)
    return data


def year_filter(data, model, field_name, value, is_lower_bound):
    if value is not None and datetime.datetime.now().year - 10 < value < datetime.datetime.now().year + 10:
        data = apply_range_filter(data, model, field_name, value, is_lower_bound)
    return data


def round_filter(data, model, field_name, value, is_lower_bound):
    if value is not None and 0 < value < 23:
        data = apply_range_filter(data, model, field_name, value, is_lower_bound)
    return data


def apply_range_filter(data, model, field_name, value, is_lower_bound):
    if is_lower_bound:
        return data.filter(getattr(model, field_name) >= value)
    else:
        return data.filter(getattr(model, field_name) <= value)


# [model, {filterType: field_name}]
model_map = {
    'injuries': [Injury, {}],
    'games_footywire': [Game, {'game_id': 'id', 'year': 'year', 'round': 'round_number'}],
    'matchstats_player': [MatchStatsPlayer, {'game_id': 'game_id'}],
    'player_fantasy': [PlayerFantasy, {'year': 'year', 'round': 'round'}],
    'player_supercoach': [PlayerSupercoach, {'year': 'year', 'round': 'round'}],
    'players': [Player, {}]
}
