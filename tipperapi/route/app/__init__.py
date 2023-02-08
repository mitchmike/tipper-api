from flask import Blueprint

from tipperapi.route import auth
from tipperapi.route.app import ladder, teamdetail, odds, profile, predict

app_bp = Blueprint('app', __name__, url_prefix='/')
app_bp.register_blueprint(auth.bp)
app_bp.register_blueprint(ladder.bp)
app_bp.register_blueprint(teamdetail.bp)
app_bp.register_blueprint(odds.bp)
app_bp.register_blueprint(profile.bp)
app_bp.register_blueprint(predict.bp)
