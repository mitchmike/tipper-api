import logging

import click
from dotenv import load_dotenv
from flask import Blueprint, render_template, request, flash, url_for, redirect
from sqlalchemy import desc

from datascrape.logging_config import LOGGING_CONFIG
from model.ml_model import MLModel
from tipperapi.services.predictions.ModelBuilder import ModelBuilder

from tipperapi import db
from tipperapi.db import new_session
from tipperapi.route.auth import admin_required
from tipperapi.services.predictions.PcntDiffReader import PcntDiffReader
from tipperapi.services.predictions.scripts.cleanup_model_files import cleanup

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)

bp = Blueprint('model_mgmt_api', __name__, url_prefix='/model')


@bp.route("/")
@admin_required
def model_mgmt_home():
    # populate a table of existing models and their properties
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
        features = ModelBuilder.available_features()
        return render_template('admin/model_build.html', features=features)
    # build custom model for given params
    model_type = request.form.get('model_type')
    model_strategy = request.form.get('model_strategy')
    model_features = request.form.getlist('feature')
    target_variable = request.form.get('target_variable')
    model = ModelBuilder(new_session(), model_type, model_strategy, model_features, target_variable)
    model.build(PcntDiffReader())
    if model is None:
        flash(f'model not built due to unexpected error. see logs for details')
    return redirect(url_for('admin.model_mgmt_api.get_historical_models'))


@bp.route("/set_active_model", methods=('POST',))
@admin_required
def set_active_model():
    model_id = request.form.get('model_id')
    session = db.new_session()
    model = session.query(MLModel).filter(MLModel.id == model_id).first()
    if model is not None and model.file_name is not None:
        # if there is another active model for the same set of params, set it to inactive
        existing_models = session.query(MLModel).filter(MLModel.active == True,
                                                        MLModel.model_type == model.model_type,
                                                        MLModel.model_strategy == model.model_strategy,
                                                        MLModel.features == model.features,
                                                        MLModel.target_variable == model.target_variable).all()  # TODO equals method on the db model
        for existing in existing_models:
            existing.active = False
        model.active = True # set this after disabling others otherwise the above query will pick it up
        session.commit()
    else:
        flash('Could not set active model')
    return redirect(url_for('admin.model_mgmt_api.get_historical_models'))


@bp.route("/rebuild_active_models", methods=('GET', ))
@admin_required
def rebuild_active_models():
    rebuild()
    return redirect(url_for('admin.model_mgmt_api.get_current_models'))


@bp.cli.command('rebuild-active-models')
def rebuild_active_models_cli():
    rebuild()
    click.echo('Rebuilt active models.')


def rebuild():
    load_dotenv()
    session = db.new_session()
    active_models = session.query(MLModel).filter(MLModel.active == True).all()

    for model in active_models:
        builder = ModelBuilder(session, model.model_type, model.model_strategy, model.features, model.target_variable)
        builder.build()
    session.close()


@bp.route("/clean_model_files", methods=('GET', ))
@admin_required
def clean_model_files():
    cleanup()
    return redirect(url_for('admin.model_mgmt_api.get_historical_models'))


@bp.cli.command('clean-model-files')
def clean_model_files_cli():
    cleanup()
    click.echo('Cleaned model files.')



