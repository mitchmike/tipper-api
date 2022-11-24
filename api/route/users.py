import copy
import datetime

from flask import Blueprint, render_template, request, flash, redirect, url_for, g
from werkzeug.security import generate_password_hash

from api import db
from api.route.auth import admin_required
from model.api_model.user import User

bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('/')
@admin_required
def users():
    Session = db.get_db_session_factory()
    db_session = Session()
    users = db_session.query(User).order_by('id').all()
    db_session.close()
    return render_template('admin/users/users.html', user_list=users)


@bp.route('/detail')
@admin_required
def detail():
    user_id = request.args.get('user_id')
    if user_id is None:
        flash('User not found')
        return redirect(url_for('users.users'))
    Session = db.get_db_session_factory()
    db_session = Session()
    user = db_session.query(User).filter_by(id=user_id).first()
    db_session.close()
    return render_template('admin/users/user_detail.html', user=user)


@bp.route('/create')
@admin_required
def create():
    return render_template('admin/users/user_detail.html', user=User('', '', '', ''))


@bp.route('/delete', methods=('POST',))
@admin_required
def delete():
    user_id = request.form['id']
    if user_id is None:
        flash('User not found')
        return redirect(url_for('users.users'))
    Session = db.get_db_session_factory()
    db_session = Session()
    user = db_session.query(User).filter_by(id=user_id).first()
    roles = user.roles or []
    if 'ROOT' in roles:
        flash('Cannot delete master root account')
        return redirect(url_for('users.detail', user_id=user.id))
    db_session.delete(user)
    db_session.commit()
    db_session.close()
    flash('User deleted')
    return redirect(url_for('users.users'))


@bp.route('/update', methods=('POST',))
@admin_required
def update():
    user_id = request.form['id']
    if user_id is None:
        flash('User not found')
        return redirect(url_for('users'))
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    password = request.form.get('password')
    re_password = request.form.get('re_password')
    if not password == re_password:
        flash('Passwords must match')
        return redirect(url_for('users.detail', user_id=user_id))
    roles = {
        'ADMIN': request.form.get('roles.ADMIN'),
    }
    Session = db.get_db_session_factory()
    db_session = Session()
    user = db_session.query(User).filter_by(id=user_id).first()
    user.first_name = first_name
    user.last_name = last_name
    if len(password) > 0:
        if g.user.id == user_id or 'ROOT' in g.user.roles:
            user.password = generate_password_hash(password)
        else:
            flash('Not authorised to change password')
            return redirect(url_for('users.detail', user_id=user_id))
    user_roles = copy.deepcopy(user.roles)
    for role in roles.keys():
        # remove role from user object
        if role in user_roles:
            user_roles.remove(role)
        # add if checked
        if roles[role] == 'on':
            user_roles.append(role)
    user.roles = user_roles
    user.updated_at = datetime.datetime.now()
    db_session.add(user)
    db_session.commit()
    db_session.close()
    flash('User updated')
    return redirect(url_for('users.users'))
