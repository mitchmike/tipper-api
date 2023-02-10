import os

from model import Game, Team
from tipperapi import db


def get_file_resource_path(file_name):
    test_root_dir = os.path.dirname(__file__)
    return os.path.join(test_root_dir, 'resources', file_name)


def create_team(tid=1, city='Richmond', name='Tigers', team_identifier='richmond-tigers', active=True):
    team = Team()
    team.id = tid
    team.team_identifier = team_identifier
    team.name = name
    team.city = city
    team.active_in_competition = active
    return team


def create_game(game_id=1, home_team='richmond-tigers', away_team='geelong-cats', home_score=100, away_score=50,
                winner='richmond-tigers'):
    game = Game(game_id, home_team, away_team, 2021, 1)
    game.home_score = home_score
    game.away_score = away_score
    game.winner = winner
    return game

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
    [obj_keys.discard(key) for key in ignore_fields_from_json]
    if len(json_keys.intersection(obj_keys)) != len(obj_keys):
        return False
    for k in obj_keys:
        if obj[k] != json_obj[k]:
            return False
    return True