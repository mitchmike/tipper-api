import pytest

from db_test_util import *
from model import MLModel
from tipperapi.services.predictions.ModelBuilder import ModelBuilder
from tipperapi.services.predictions.PcntDiffReader import PcntDiffReader


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr(ModelBuilder, "get_team_ids",
                        lambda *args, **kwargs: ['richmond-tigers', 'geelong-cats', 'melbourne-demons', 'kangaroos'])
    monkeypatch.setattr(ModelBuilder, "save_to_file", lambda *args, **kwargs: None)


def test_build_model(app, setup, monkeypatch):
    monkeypatch.setattr(PcntDiffReader, "read", lambda *args, **kwargs: get_json_from_file())
    with app.app_context():
        with db.new_session(expire_on_commit=False) as db_s:
            model = ModelBuilder(db_s, 'LinearRegression', 'pcntdiff', ['kicks', 'handballs'], 'win').build()
            assert model is not None


def test_new_model_deactivates_old_with_same_params(app, setup, monkeypatch):
    monkeypatch.setattr(PcntDiffReader, "read", lambda *args, **kwargs: get_json_from_file())
    with app.app_context():
        # add a model to the database
        add_data(app, MLModel, ['id', 'model_type', 'model_strategy', 'features', 'target_variable'],
                 [99, 'LinearRegression', 'pcntdiff', sorted(['kicks', 'handballs']), 'win'])
        with db.new_session(expire_on_commit=False) as db_s:
            model = ModelBuilder(db_s, 'LinearRegression', 'pcntdiff', ['kicks', 'handballs'], 'win').build()
            assert model is not None
            models = db_s.query(MLModel).all()
            assert models[0].id == 99
            assert models[0].active is False
            assert models[1].active is True


def test_target_variable_has_nans(app, setup, monkeypatch):
    # some games have scores but others dont
    monkeypatch.setattr(PcntDiffReader, "read",
                        lambda *args, **kwargs: get_json_from_file('pcnt_diff_data_no_score.json'))
    with app.app_context():
        with db.new_session(expire_on_commit=False) as db_s:
            model = ModelBuilder(db_s, 'LinearRegression', 'pcntdiff', ['kicks', 'handballs'], 'score').build()
            assert model is None


def test_requested_model_feature_has_no_data(app, setup, monkeypatch):
    monkeypatch.setattr(PcntDiffReader, "read",
                        lambda *args, **kwargs: get_json_from_file('pcnt_diff_data.json'))
    with app.app_context():
        with db.new_session(expire_on_commit=False) as db_s:
            # tackles not in any game
            model = ModelBuilder(db_s, 'LinearRegression', 'pcntdiff', ['kicks', 'tackles'], 'score').build()
            assert model is None


def test_no_stat_data_available(app, setup, monkeypatch):
    # return empty
    monkeypatch.setattr(PcntDiffReader, "read", lambda *args, **kwargs: {})
    with app.app_context():
        with db.new_session(expire_on_commit=False) as db_s:
            # tackles not in any game
            model = ModelBuilder(db_s, 'LinearRegression', 'pcntdiff', ['kicks', 'tackles'], 'score').build()
            assert model is None


def test_no_teams_available(app, setup, monkeypatch):
    monkeypatch.setattr(ModelBuilder, "get_team_ids", lambda *args, **kwargs: None)
    monkeypatch.setattr(PcntDiffReader, "read", lambda *args, **kwargs: get_json_from_file())
    with app.app_context():
        with db.new_session(expire_on_commit=False) as db_s:
            model = ModelBuilder(db_s, 'LinearRegression', 'pcntdiff', ['kicks', 'handballs'], 'win').build()
            assert model is None
