from flask import Blueprint, render_template, request, flash, redirect, url_for

from api import db
from model.api_model.user import User

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
def index():
    return render_template('admin/admin_home.html')


@bp.route('/users')
def users():
    Session = db.get_db_session_factory()
    db_session = Session()
    users = db_session.query(User).all()
    return render_template('/admin/users.html', user_list=users)


@bp.route('/user_detail')
def user_detail():
    user_id = request.args.get('user_id')
    if user_id is None:
        flash('User not found')
        return redirect(url_for('admin/users'))
    Session = db.get_db_session_factory()
    db_session = Session()
    user = db_session.query(User).filter_by(id=user_id).first()
    return render_template('admin/user_detail.html', user=user)
