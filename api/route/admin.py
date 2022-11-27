from flask import Blueprint, render_template

from api.route.auth import login_required

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
@login_required
def index():
    return render_template('admin/admin_home.html')
