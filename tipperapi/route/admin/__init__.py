from flask import Blueprint, render_template

from tipperapi.route.auth import login_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
def index():
    return render_template('admin/admin_home.html')
