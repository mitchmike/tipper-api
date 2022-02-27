import functools

from flask import Blueprint, request, flash, url_for, redirect, session, g, render_template
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from api import db
from model.api_model.user import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


# decorator for views requiring login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        if 'ROOT' not in g.user.roles and 'ADMIN' not in g.user.roles:
            flash("admin rights required")
            return redirect(url_for('admin.index'))
        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        Session = db.get_db_session_factory()
        db_session = Session()
        g.user = db_session.query(User).filter_by(id=user_id).first()


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'GET':
        return render_template('auth/register.html')
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        re_password = request.form['re_password']
        Session = db.get_db_session_factory()
        error = None
        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif not password == re_password:
            error = 'Passwords not matching'
        if error is None:
            try:
                with Session() as session:
                    password = generate_password_hash(password)
                    user = User(first_name, last_name, email, password)
                    roles = {
                        'ADMIN': request.form.get('roles.ADMIN')
                    }
                    for role in roles.keys():
                        if roles[role] == 'on':
                            user.roles.append(role)
                    session.add(user)
                    session.commit()
            except IntegrityError:
                error = f"Email {email} is already registered."
            else:
                flash(f'User created with email: {email}')
                return redirect(url_for('admin.index'))
        flash(error)
    return redirect(request.referrer)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        Session = db.get_db_session_factory()
        db_session = Session()
        error = None
        user = db_session.query(User).filter(User.email == email).first()
        if user is None or not check_password_hash(user.password, password):
            error = 'Login unsuccessful.'
        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('admin.index'))
        flash(error)
    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.index'))


