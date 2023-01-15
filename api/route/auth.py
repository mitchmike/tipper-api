import functools

from flask import Blueprint, request, flash, url_for, redirect, session, g, render_template
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from api import db
from model import Team, User

bp = Blueprint('auth', __name__, url_prefix='/auth')


# decorator for views requiring login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('auth.admin_login', next=request.url))

        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('auth.admin_login', next=request.url))
        if 'ROOT' not in g.user.roles and 'ADMIN' not in g.user.roles:
            flash("admin rights required")
            return redirect(request.referrer)
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


@bp.route('/admin_register', methods=('GET', 'POST'))
def admin_register():
    if request.method == 'GET':
        return render_template('auth/register.html')
    if request.method == 'POST':
        user = register(admin=True)
        if 'id' in user:
            flash(f'User created with email: {user["email"]}')
            return redirect(url_for('admin.index'))
        else:
            flash(f'Failed to register. see logs for detail')
            return redirect(request.referrer)


@bp.route('/register', methods=('POST',))
def register(admin=False):
    error = None
    try:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        re_password = request.form['re_password']
        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif not password == re_password:
            error = 'Passwords not matching'
        if error is None:
            try:
                Session = db.get_db_session_factory()
                user_session = Session()
                password = generate_password_hash(password)
                user = User(first_name, last_name, email, password)
                if admin:
                    roles = {
                        'ADMIN': request.form.get('roles.ADMIN')
                    }
                    for role in roles.keys():
                        if roles[role] == 'on':
                            user.roles.append(role)
                user_session.add(user)
                user_session.commit()
                user_session.close()
            except IntegrityError:
                error = f"Email {email} is already registered."
            else:
                print(f'User created with email: {email}')
                return user.as_dict()
    except Exception as e:
        print(f'Encountered exception while processing register request: {e}')
    print(f'Failed to register user. error is {error}')
    return {}


@bp.route('/admin_login', methods=('GET', 'POST'))
def admin_login():
    if request.method == 'GET':
        session['next'] = request.args.get('next', None)
    if request.method == 'POST':
        next_url = session.get('next')
        user = login()
        if 'id' in user:
            if next_url is not None:
                return redirect(next_url)
            return redirect(url_for('admin.index'))
        flash('Login failed')
    return render_template('auth/login.html')


@bp.route('/login', methods=('POST',))
def login():
    email = request.form['email']
    password = request.form['password']
    Session = db.get_db_session_factory()
    db_session = Session()
    user = db_session.query(User).filter(User.email == email).first()
    db_session.close()
    if user is not None and check_password_hash(user.password, password):
        session.clear()
        session['user_id'] = user.id
        return user.as_dict()
    else:
        return {}


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.index'))


@bp.route("/user_profile", methods=('POST',))
def user_profile():
    user_id = request.form.get('user_id')
    Session = db.get_db_session_factory()
    db_session = Session()
    user = db_session.query(User).filter_by(id=user_id).first()
    db_session.merge(user)
    db_session.commit()
    # give some details about the users team preference and activity history
    team = db_session.query(Team).filter(Team.id == user.follows_team).first()
    db_session.close()
    profile = {}
    if user:
        profile = user.as_dict()
        profile['follows_team'] = team.team_identifier
    return profile
