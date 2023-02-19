import json

from werkzeug.datastructures import ImmutableMultiDict

from db_test_util import *
from model import MLModel
from tipperapi.route.admin import model_mgmt_api
from tipperapi.services.predictions.ModelBuilder import ModelBuilder
from tipperapi.services.predictions.PcntDiffReader import PcntDiffReader


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
    monkeypatch.setattr(PcntDiffReader, "read", lambda *args, **kwargs: get_json_from_file())
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
        monkeypatch.setattr(PcntDiffReader, "read", lambda *args, **kwargs: get_json_from_file())
        monkeypatch.setattr(ModelBuilder, "get_team_ids", lambda *args, **kwargs: ['kangaroos'])
        monkeypatch.setattr(ModelBuilder, "save_to_file", lambda *args, **kwargs: None)
        model_mgmt_api.rebuild()
        with db.new_session() as db_s:
            models = db_s.query(MLModel).all()
            assert len(models) == 3
            assert not [model for model in models if model.id == 1][0].active
            assert not [model for model in models if model.id == 2][0].active
            assert [model for model in models if model.id == 3][0].active
