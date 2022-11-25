from flask import Blueprint, render_template

from api.route.auth import admin_required

bp = Blueprint('db_mgmt_api', __name__, url_prefix='/database')


@bp.route("/")
def db_mgmt_home():
    return render_template("admin/database_management.html")


@bp.route("/update_table_data")
@admin_required
def trigger_table_update():
    # update selected data from a table based on where clause
    return None


@bp.route("/clean_table_data")
@admin_required
def trigger_table_clean():
    # delete all or selected data from a table
    return None


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
