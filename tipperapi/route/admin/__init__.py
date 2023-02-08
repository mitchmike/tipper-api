from flask import Blueprint, render_template

from tipperapi.route.admin import user_admin, scrape_api, db_mgmt_api, model_mgmt_api
from tipperapi.route.auth import login_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
admin_bp.register_blueprint(user_admin.bp)
admin_bp.register_blueprint(scrape_api.bp)
admin_bp.register_blueprint(db_mgmt_api.bp)
admin_bp.register_blueprint(model_mgmt_api.bp, cli_group=None)


@admin_bp.route('/')
@login_required
def index():
    return render_template('admin/admin_home.html')
