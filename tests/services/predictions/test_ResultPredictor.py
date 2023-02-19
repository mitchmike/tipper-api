import joblib
import pytest

from db_test_util import *
from model import MLModel, User
from tipperapi import cache
from tipperapi.services.predictions.ModelBuilder import ModelBuilder
from tipperapi.services.predictions.PcntDiffReader import PcntDiffReader
from tipperapi.services.predictions.ResultPredictor import ResultPredictor
from tipperapi.services.predictions.aggregated_match_stats import ALL_ROUNDS

USER_ID = 1


@pytest.fixture
def lin_reg_model(app):
    return joblib.load(get_file_resource_path('LinearRegression_test.sav'))


@pytest.fixture
def model_record(app):
    return add_data(app, MLModel,
                    ['id', 'model_type', 'model_strategy', 'features', 'target_variable', 'file_name'],
                    [99, 'LinearRegression', 'pcntdiff', sorted(['handballs']), 'score',
                     get_file_resource_path('LinearRegression_test.sav')])


@pytest.fixture
def predictor(app):
    return ResultPredictor(USER_ID, 'richmond', 'geelong', 'LinearRegression', 'pcntdiff', ['handballs'],
                               'score')


def test_get_prediction_data(app, predictor, monkeypatch):
    monkeypatch.setattr(PcntDiffReader, "read", lambda *args, **kwargs: get_json_from_file())
    X_team, X_opp = predictor.get_prediction_data([], [])
    assert X_team['handballs'].size == 1
    assert X_opp['handballs'].size == 1


def test_get_prediction_data_no_data_for_year_rounds(app, predictor, monkeypatch):
    monkeypatch.setattr(PcntDiffReader, "read", lambda *args, **kwargs: {})
    X_team, X_opp = predictor.get_prediction_data([], [])
    assert X_team is None
    assert X_opp is None


def test_get_model_from_cache(app, lin_reg_model, model_record, predictor, monkeypatch):
    monkeypatch.setattr(cache, "get", lambda *args, **kwargs: lin_reg_model)
    model, model_record, new_model = predictor.get_model(model_record)
    model_record.file_name = None  # set so that the test wont fall back to loading the file
    assert model is not None
    assert new_model is False


def test_get_model_from_file(app, lin_reg_model, model_record, predictor, monkeypatch):
    monkeypatch.setattr(cache, "get", lambda *args, **kwargs: None)
    model, model_record, new_model = predictor.get_model(model_record)
    assert model is not None
    assert new_model is False


def test_get_model_build_new(app, lin_reg_model, model_record, predictor, monkeypatch):
    monkeypatch.setattr(cache, "get", lambda *args, **kwargs: None)
    monkeypatch.setattr(ModelBuilder, "build", lambda *args, **kwargs: lin_reg_model)
    model_record.file_name = None  # set so that the test wont fall back to loading the file
    with app.app_context():
        with db.new_session() as db_s:
            predictor.session = db_s
            model, model_record, new_model = predictor.get_model(model_record)
            assert model is not None
            assert new_model is True


def test_do_prediction(app, lin_reg_model, model_record, predictor, monkeypatch):
    X_team = pandas.DataFrame(data={'handballs': [0.5]})
    X_opp = pandas.DataFrame(data={'handballs': [0.6]})
    add_data(app, User, ['id', 'email', 'password'], [USER_ID, 'a', 'a'])
    with app.app_context():
        with db.new_session() as db_s:
            predictor.session = db_s
            prediction = predictor.do_prediction(X_team, X_opp, lin_reg_model, model_record, True)
            assert prediction.team_score > 0
            assert prediction.opponent_score > 0
            assert prediction.user_id == 1
            assert prediction.team == 'richmond'
            assert prediction.opponent == 'geelong'


def test_get_prediction_full_e2e(app, lin_reg_model, model_record, predictor, monkeypatch):
    monkeypatch.setattr(cache, "get", lambda *args, **kwargs: None)
    monkeypatch.setattr(PcntDiffReader, "read", lambda *args, **kwargs: get_json_from_file())
    monkeypatch.setattr(ModelBuilder, "build", lambda *args, **kwargs: lin_reg_model)
    add_data(app, User, ['id', 'email', 'password'], [USER_ID, 'a', 'a'])
    with app.app_context():
        all_yrs = [(2021, ALL_ROUNDS), (2022, ALL_ROUNDS)]
        with db.new_session() as db_s:
            predictor.session = db_s
            prediction = predictor.get_prediction(all_yrs, all_yrs)
            assert prediction['team_score'] > 0
            assert prediction['opponent_score'] > 0
            assert prediction['team'] == 'richmond'
            assert prediction['opponent'] == 'geelong'
            assert prediction['new_model'] is False
            assert prediction['prediction_for_model'] is not None

