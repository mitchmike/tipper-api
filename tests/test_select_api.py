from model import User, Team
from tipperapi import db

TEAM_COL_NAMES = ['id', 'city', 'name', 'team_identifier', 'active_in_competition']


def test_select_teams(app, client):
    add_data(app, Team, TEAM_COL_NAMES, [49, 'North Melbourne', 'Kangaroos', 'kangaroos', True])
    add_data(app, Team, TEAM_COL_NAMES, [46, 'Greater Western Sydney', 'Giants', 'greater-western-sydney-giants'])
    add_data(app, Team, TEAM_COL_NAMES, [45, 'Gold Coast', 'Suns', 'gold-coast-suns'])
    freo = add_data(app, Team, TEAM_COL_NAMES, [43, 'Fremantle', 'Dockers', 'fremantle-dockers'])
    add_data(app, Team, TEAM_COL_NAMES, [48, 'Melbourne', 'Demons', 'melbourne-demons'])
    with client:
        response = client.get('/api/select/teams')
        json = response.json
        assert len(json) == 5
        json_freo = find_obj_in_json(json, freo.as_dict(), 'id')
        assert dict_equals(json_freo, freo.as_dict(), ['followers'])


def test_get_recent_year_rounds():
    pass


def test_select_data():
    pass


def test_get_games():
    pass


def test_select_player_points():
    pass


def test_select_matchstats():
    pass


def test_select_pcnt_diff():
    pass


def test_select_players(app):
    add_data(app, User, ['id'], [1])
    pass


def add_data(app, model, fields, values):
    with app.app_context():
        obj = model()
        for field, value in zip(fields, values):
            setattr(obj, field, value)
        with db.new_session(expire_on_commit=False) as db_s:
            db_s.add(obj)
            db_s.commit()
        return obj


def find_obj_in_json(json, match_obj, match_field):
    for obj in json:
        if obj[match_field] == match_obj[match_field]:
            return obj


def dict_equals(json_obj, obj, ignore_fields_from_json):
    if obj is None:
        return False
    json_keys = set(json_obj.keys())
    [json_keys.discard(key) for key in ignore_fields_from_json]
    obj_keys = set(obj.keys())
    if len(json_keys.intersection(obj_keys)) != len(obj_keys):
        return False
    for k in obj_keys:
        if obj[k] != json_obj[k]:
            return False
    return True
