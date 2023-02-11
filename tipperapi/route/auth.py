import functools
import logging.config

from flask import Blueprint, request, flash, url_for, redirect, session, g, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from datascrape.logging_config import LOGGING_CONFIG
from tipperapi import db
from model import Team, User

bp = Blueprint('auth', __name__, url_prefix='/auth')

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)


# decorator for views requiring login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('auth.login', next=request.url))
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('auth.login', next=request.url))
        if 'ROOT' not in g.user.roles and 'ADMIN' not in g.user.roles:
            flash("admin rights required")
            return redirect(url_for('auth.login', next=request.url))
        return view(*args, **kwargs)
    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db_session = db.new_session()
        g.user = db_session.query(User).filter_by(id=user_id).first()
        db_session.close()


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        error = None
        try:
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            password = request.form.get('password')
            re_password = request.form.get('re_password')
            if not email:
                error = 'Email is required.'
            elif not password:
                error = 'Password is required.'
            elif not password == re_password:
                error = 'Passwords not matching'
            if error is None:
                try:
                    user_session = db.new_session()
                    existing = user_session.query(User).filter(User.email == email).first()
                    if existing is not None:
                        error = f"Email {email} is already registered."
                    else:
                        password = generate_password_hash(password)
                        user = User(first_name, last_name, email, password)
                        user_session.add(user)
                        user_session.commit()
                        print(f'User created with email: {email}')
                        flash('Registration successful')
                        if user.id is not None:
                            session["user_id"] = user.id
                        return redirect(request.args.get('next', url_for('index')))
                except Exception as e:
                    LOGGER.error(f'Unexpected error occured while registering user: {e}')
                    error = 'Unexpected error occured while registering'
            if error is not None:
                LOGGER.error(f'Failed to register user. error is {error}')
                flash(error)
        except Exception as e:
            LOGGER.error(f'Encountered exception while processing register request: {e}')

    return render_template('app/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == "GET":
        session['next'] = request.args.get('next', None)
        return render_template("app/login.html")
    email = request.form['email']
    password = request.form['password']
    next_url = session.pop('next', None)
    db_session = db.new_session()
    user = db_session.query(User).filter(User.email == email).first()
    db_session.close()
    if user is not None and check_password_hash(user.password, password):
        session.clear()
        session['user_id'] = user.id
        teams = db.new_session().query(Team).all()
        team_id = [team.team_identifier for team in teams if team.id == user.follows_team]
        if len(team_id) > 0:
            session['team_identifier'] = team_id[0]
        return redirect(next_url if next_url is not None else '/')
    else:
        session['next'] = next_url  # remember in case login fails
        return render_template('app/login.html', next=request.args.get('next'), error='Login failed')


@bp.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('index'))

