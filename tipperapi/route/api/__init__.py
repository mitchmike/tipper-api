from flask import Blueprint

from tipperapi.route.api import ladder_api, predict_api, select_api

api_bp = Blueprint('api', __name__, url_prefix='/api')
api_bp.register_blueprint(ladder_api.bp)
api_bp.register_blueprint(predict_api.bp)
api_bp.register_blueprint(select_api.bp)
