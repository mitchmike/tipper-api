import copy
import datetime

from flask import Blueprint, render_template, request, flash, redirect, url_for, g
from werkzeug.security import generate_password_hash

from tipperapi import db
from tipperapi.route.auth import admin_required
from tipperapi.route.admin.db_mgmt_api import safe_int
from model import Team
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
    user_id = request.args.get('user_edit_id')
    if user_id is None:
        flash('User not found')
        return redirect(url_for('admin.users.users'))
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
    user_id = request.form['user_delete_id']
    if user_id is None:
        flash('User not found')
        return redirect(url_for('admin.users.users'))
    Session = db.get_db_session_factory()
    db_session = Session()
    user = db_session.query(User).filter_by(id=user_id).first()
    roles = user.roles or []
    if 'ROOT' in roles:
        flash('Cannot delete master root account')
        return redirect(url_for('admin.users.detail', user_id=user.id))
    db_session.delete(user)
    db_session.commit()
    db_session.close()
    flash('User deleted')
    return redirect(url_for('admin.users.users'))


@bp.route('/update', methods=('POST',))
@admin_required
def update():
    user_id = request.form.get('id')
    if user_id == 'None':  # TODO remove hack - separate create and update forms...
        user_id = None
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    password = request.form.get('password')
    re_password = request.form.get('re_password')
    follows_team = request.form.get('follows_team', None)
    if not password == re_password:
        flash('Passwords must match')
        return redirect(url_for('admin.users.detail', user_id=user_id))
    roles = {
        'ADMIN': request.form.get('roles.ADMIN'),
    }
    db_session = db.new_session()
    user = User()
    if user_id is not None:
        user = db_session.query(User).filter_by(id=user_id).first()
    user.first_name = first_name
    user.last_name = last_name
    if user_id is None:  # only for creates
        existing = db_session.query(User).filter_by(email=email).first()
        if existing is not None:
            flash('Email already exists')
            return redirect(request.referrer)
        user.email = email
    if len(password) > 0:
        if g.user.id == user_id or 'ROOT' in g.user.roles or user_id is None:
            user.password = generate_password_hash(password)
        else:
            flash('Not authorised to change password')
            return redirect(url_for('admin.users.detail', user_id=user_id))
    user_roles = copy.deepcopy(user.roles)
    for role in roles.keys():
        # remove role from user object
        if role in user_roles:
            user_roles.remove(role)
        # add if checked
        if roles[role] == 'on':
            user_roles.append(role)
    user.roles = user_roles
    if follows_team is not None:
        team = db_session.query(Team).filter(Team.id == safe_int(follows_team)).first()
        if team is not None:
            user.follows_team = team.id
    if user_id is None:
        user.created_at = datetime.datetime.now()
    user.updated_at = datetime.datetime.now()
    db_session.add(user)
    db_session.commit()
    db_session.close()
    flash('User updated')
    return redirect(url_for('admin.users.users'))
