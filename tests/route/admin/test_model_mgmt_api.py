import pytest
from werkzeug.datastructures import ImmutableMultiDict

from db_test_util import *
from model import User, MLModel
from tipperapi.route.admin import model_mgmt_api
from tipperapi.services.predictions.ModelBuilder import ModelBuilder
from tipperapi.services.predictions.PcntDiffReader import PcntDiffReader


@pytest.fixture()
def admin_user(app, client):
    admin_user = add_data(app, User, USER_COL_NAMES, [1, 'email', 'p', ['ADMIN']])
    with client.session_transaction() as pre_session:
        pre_session['user_id'] = admin_user.id
    return admin_user


def test_model_mgmt_home(app, client, admin_user):
    with client:
        response = client.get("/admin/model", follow_redirects=True)
        assert response.status_code == 200
        assert '<title>Tipper - Model Management</title>' in response.text


def test_get_historical_models(app, client, admin_user):
    add_data_array(app, MLModel, ['id', 'model_type', 'model_strategy', 'active'],
                   [
                       [1, 'LM', 'pcntdiff', False],
                       [2, 'LM', 'pcntdiff', True]
                   ]
                   )
    with client:
        response = client.get("/admin/model/previous_models")
        assert response.status_code == 200
        assert '<title>Tipper - Model Management</title>' in response.text
        # both models shown
        assert '''<tr>
                <td style="text-align: end;">2</td>
                <td>LM</td>
                <td>pcntdiff</td>''' in response.text
        assert '''<tr>
                <td style="text-align: end;">1</td>
                <td>LM</td>
                <td>pcntdiff</td>''' in response.text


def test_get_current_models(app, client, admin_user):
    add_data_array(app, MLModel, ['id', 'model_type', 'model_strategy', 'active'],
                   [
                       [1, 'LM', 'pcntdiff', False],
                       [2, 'LM', 'pcntdiff', True]
                   ]
                   )
    with client:
        response = client.get("/admin/model/current_models")
        assert response.status_code == 200
        assert '<title>Tipper - Model Management</title>' in response.text
        # only active model shown
        assert '''<tr>
                <td style="text-align: end;">2</td>
                <td>LM</td>
                <td>pcntdiff</td>''' in response.text
        assert '''<tr>
                <td style="text-align: end;">1</td>
                <td>LM</td>
                <td>pcntdiff</td>''' not in response.text


def test_get_build_model(app, client, admin_user):
    with client:
        response = client.get("/admin/model/build_model")
        assert response.status_code == 200


def test_post_build_model(app, client, admin_user, monkeypatch):
    data = ImmutableMultiDict(
        [('hidden', ''), ('model_type', 'LinearRegression'), ('model_strategy', 'pcnt_diff'), ('feature', 'kicks'),
         ('feature', 'handballs'), ('target_variable', 'score')])
    monkeypatch.setattr(PcntDiffReader, "read", lambda *args, **kwargs: JSON_PCNT_DIFF)
    monkeypatch.setattr(ModelBuilder, "get_team_ids", lambda *args, **kwargs: ['kangaroos'])
    monkeypatch.setattr(ModelBuilder, "save_to_file", lambda *args, **kwargs: None)  # TODO - should stop this method from running in all tests
    with client:
        response = client.post("/admin/model/build_model", data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'unexpected error' not in response.data
        assert '''<tr>
                <td style="text-align: end;">1</td>
                <td>LinearRegression</td>
                <td>pcnt_diff</td>
                <td>[&#39;handballs&#39;, &#39;kicks&#39;]</td>
                <td>score</td>
                <td>nan</td>
                <td>True</td>''' in response.text


def test_set_active_model(app, client, admin_user):
    add_data_array(app, MLModel, ['id', 'model_type', 'model_strategy', 'file_name', 'active'],
                   [
                       [1, 'LM', 'pcntdiff', 'file1', False],
                       [2, 'LM', 'pcntdiff', 'file2', True]
                   ]
                   )
    with client:
        response = client.post("/admin/model/set_active_model", data={'model_id': 1}, follow_redirects=True)
        assert response.status_code == 200
        assert '<title>Tipper - Model Management</title>' in response.text
        assert '''<tr>
                <td style="text-align: end;">2</td>
                <td>LM</td>
                <td>pcntdiff</td>
                <td>[]</td>
                <td>None</td>
                <td>None</td>
                <td>False</td>''' in response.text
        assert '''<tr>
                <td style="text-align: end;">1</td>
                <td>LM</td>
                <td>pcntdiff</td>
                <td>[]</td>
                <td>None</td>
                <td>None</td>
                <td>True</td>''' in response.text


def test_rebuild(app, monkeypatch):
    with app.app_context():
        add_data_array(app, MLModel, ['model_type', 'model_strategy', 'features', 'target_variable', 'active'],
                   [
                       ['LM', 'pcntdiff', ['kicks'], 'score', False],
                       ['LM', 'pcntdiff', ['kicks'], 'score', True]
                   ]
                   )

        monkeypatch.setattr(PcntDiffReader, "read", lambda *args, **kwargs: JSON_PCNT_DIFF)
        monkeypatch.setattr(ModelBuilder, "get_team_ids", lambda *args, **kwargs: ['kangaroos'])
        monkeypatch.setattr(ModelBuilder, "save_to_file", lambda *args, **kwargs: None)
        model_mgmt_api.rebuild()
        with db.new_session() as db_s:
            models = db_s.query(MLModel).all()
            assert len(models) == 3
            assert not [model for model in models if model.id == 1][0].active
            assert not [model for model in models if model.id == 2][0].active
            assert [model for model in models if model.id == 3][0].active


JSON_PCNT_DIFF = [
    {
        "game_id": 10333,
        "year": 2021,
        "round_number": 1,
        "team_id": "kangaroos",
        "opponent": "port-adelaide-power",
        "home_game": 1,
        "win": 0,
        "score": 63,
        "kicks": -0.1572052401746725,
        "handballs": 0.07534246575342465,
        "disposals": -0.06666666666666667,
        "marks": -0.11494252873563218,
        "goals": -0.47058823529411764,
        "behinds": -0.3076923076923077
    },
    {
        "game_id": 10550,
        "year": 2022,
        "round_number": 1,
        "team_id": "kangaroos",
        "opponent": "hawthorn-hawks",
        "home_game": 0,
        "win": 0,
        "score": 56,
        "kicks": 0.018779342723004695,
        "handballs": -0.19480519480519481,
        "disposals": -0.07084468664850137,
        "marks": 0.052083333333333336,
        "goals": -0.2727272727272727,
        "behinds": -0.1111111111111111
    },
    {
        "game_id": 10341,
        "year": 2021,
        "round_number": 2,
        "team_id": "kangaroos",
        "opponent": "gold-coast-suns",
        "home_game": 0,
        "win": 0,
        "score": 37,
        "kicks": -0.3047945205479452,
        "handballs": 0.11486486486486487,
        "disposals": -0.16363636363636364,
        "marks": -0.2956521739130435,
        "goals": -0.6428571428571429,
        "behinds": -0.46153846153846156
    }
]
