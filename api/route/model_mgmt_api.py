from flask import Blueprint, render_template

from api.route.auth import admin_required
from api.route.select_api import select_data
from model.ml_model import MLModel

bp = Blueprint('model_mgmt_api', __name__, url_prefix='/model')


@bp.route("/")
def model_mgmt_home():
    # populate a table of existing models and their properties
    models = []
    return render_template("admin/model_management.html", models=models)


@bp.route("/previous_models")
@admin_required
def get_historical_models():
    # get previous models of a given type
    # select by date range, accuracy levels etc.
    models = select_data(MLModel, ()).order_by('updated_time').limit(50).all()
    return render_template("admin/model_management.html", models=models)


@bp.route("/previous_models")
@admin_required
def get_current_models():
    # get previous models of a given type
    # select by date range, accuracy levels etc.
    models = select_data(MLModel, ()).filter('active').order_by('updated_time').all()
    return render_template("admin/model_management.html", models=models)


@bp.route("/previous_models")
@admin_required
def build_model():
    # build custom model for given params
    # TODO
    return render_template("admin/model_management.html")
