import datetime
import os

from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash

from api import db
from api.route.auth import login_required
from api.services.utils import safe_int
from model import User, Team

serverEndpoint = os.environ.get('TIPPER_SERVER_ENDPOINT')

bp = Blueprint('profile', __name__, )


@bp.route('/user_profile')
@login_required
def profile():
    db_session = db.new_session()
    user_id = session.get('user_id')
    user_detail = get_current_user(db_session, user_id)
    teams = db_session.query(Team).order_by('city').all()
    return render_template("app/user_profile.html", user_detail=user_detail, teams=teams)


@bp.route('/update', methods=('POST',))
@login_required
def update():
    db_session = db.new_session()
    user_id = session.get('user_id')
    if user_id is not None:
        current_details = get_current_user(db_session, user_id)
        if safe_int(request.form['id']) == user_id:
            # sanitise inputs
            pw = request.form.get('password', '')
            re_pw = request.form.get('re_password', '')
            if not sanitise_pw(pw, re_pw):
                # return early
                return redirect(url_for('app.profile.profile'))
            else:
                if len(pw) > 0:
                    current_details.password = generate_password_hash(pw)
            new_team = safe_int(request.form.get('team'))
            current_details.first_name = request.form.get('first_name', current_details.first_name)
            current_details.last_name = request.form.get('last_name', current_details.last_name)

            # reset team_identifier on session if it has changed
            current_team = current_details.follows_team
            if new_team != current_team:
                current_details.follows_team = new_team
                team = db_session.query(Team).with_entities(Team.id, Team.team_identifier).filter(
                    Team.id == new_team).first()
                session['team_identifier'] = team.team_identifier if team is not None else None
            current_details.updated_at = datetime.datetime.now()
            db_session.commit()

    return redirect(url_for('app.profile.profile'))


def get_current_user(db_session, user_id):
    return db_session.query(User).filter(User.id == user_id).first()


def sanitise_pw(pw, re_pw):
    if len(pw) == 0 and len(re_pw) == 0:
        # not updating pw
        return True
    if pw != re_pw:
        flash('passwords must match')
        return False
    if len(pw) < 3:
        flash('password must be at least 3 chars long')
        return False
    return True
