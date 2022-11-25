from flask import Blueprint, render_template

from api.route.auth import admin_required

bp = Blueprint('model_mgmt_api', __name__, url_prefix='/model')


@bp.route("/")
def model_mgmt_home():
    # populate a table of existing models and their properties
    models = None
    return render_template("admin/model_management.html", existing_models=models)


@bp.route("/previous_models")
@admin_required
def get_historical_models():
    # get previous models of a given type
    # select by date range, accuracy levels etc.
    return None
