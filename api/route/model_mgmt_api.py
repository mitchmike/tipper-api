import logging

from flask import Blueprint, render_template, request, flash, url_for, redirect
from sqlalchemy import desc

from api.db import new_session
from api.route import predict
from api.route.auth import admin_required
from datascrape.logging_config import LOGGING_CONFIG
from model.ml_model import MLModel
from predictions.ModelBuilder import ModelBuilder

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)

bp = Blueprint('model_mgmt_api', __name__, url_prefix='/model')


@bp.route("/")
@admin_required
def model_mgmt_home():
    # populate a table of existing models and their properties
    # TODO add button to set model as active
    models = []
    return render_template("admin/model_management.html", models=models)


# TODO add an endpoint to trigger manual rebuild of all major models

@bp.route("/previous_models")
@admin_required
def get_historical_models():
    # get previous models of a given type
    # TODO select by date range, accuracy levels etc.
    with new_session() as session:
        models = session.query(MLModel).order_by(desc(MLModel.created_at)).limit(50).all()
    return render_template("admin/model_management.html", models=models)


@bp.route("/current_models")
@admin_required
def get_current_models():
    # get previous models of a given type
    # select by date range, accuracy levels etc.
    with new_session() as session:
        models = session.query(MLModel).filter(MLModel.active == True).order_by(desc(MLModel.created_at)).limit(
            50).all()
    return render_template("admin/model_management.html", models=models)


@bp.route("/build_model", methods=('GET', 'POST'))
@admin_required
def build_model():
    if request.method == 'GET':
        features = predict.available_features()
        return render_template('admin/model_build.html', features=features)
    # build custom model for given params
    model_type = request.form.get('model_type')
    model_strategy = request.form.get('model_strategy')
    model_features = request.form.getlist('feature')
    target_variable = request.form.get('target_variable')
    model = ModelBuilder(new_session(), model_type, model_strategy, model_features, target_variable).build()
    if model is None:
        flash(f'model not built due to unexpected error. see logs for details')
    return redirect(url_for('model_mgmt_api.get_historical_models'))
