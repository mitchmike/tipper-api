import json

from werkzeug.datastructures import ImmutableMultiDict

from db_test_util import *
from tipperapi.route.app import teamdetail


def test_get_team_detail_no_team(app, client, standard_user):
    with client:
        response = client.get('/teamdetail')
        assert response.status_code == 200
        assert b'<h1 class="display-4">Choose Team</h1>' in response.data


def test_get_team_detail(app, client, standard_user, monkeypatch):
    monkeypatch.setattr(teamdetail, "get_team", lambda *args, **kwargs: create_team())
    monkeypatch.setattr(teamdetail, "get_games", lambda *args, **kwargs: [create_game(), create_game()])
    monkeypatch.setattr(teamdetail, "get_pcnt_diff_for_chart", lambda *args, **kwargs: get_json_from_file())
    with client:
        response = client.get('/teamdetail?team=richmond-tigers')
        assert response.status_code == 200
        assert b'<td>Richmond Tigers</td>' in response.data
        assert '''<td>1</td>
                                <td>2021</td>
                                <td>richmond-tigers</td>
                                <td>100</td>
                                <td>geelong-cats</td>
                                <td>50</td>
                                
                                    <td class='table-success'>richmond-tigers</td>''' in response.text


def test_post_team_detail(app, client, standard_user, monkeypatch):
    monkeypatch.setattr(teamdetail, "get_team", lambda *args, **kwargs: create_team())
    monkeypatch.setattr(teamdetail, "get_games", lambda *args, **kwargs: [create_game(), create_game()])
    monkeypatch.setattr(teamdetail, "get_pcnt_diff_for_chart", lambda *args, **kwargs: get_json_from_file())
    with client:
        data = ImmutableMultiDict([('team', 'richmond-tigers'), ('stat', 'kicks'), ('stat', 'handballs')])
        response = client.post('/teamdetail', data=data)
        assert response.status_code == 200
        assert b'<td>Richmond Tigers</td>' in response.data
        assert '''<td>1</td>
                                <td>2021</td>
                                <td>richmond-tigers</td>
                                <td>100</td>
                                <td>geelong-cats</td>
                                <td>50</td>''' in response.text


def get_pcnt_diff_json():
    with open(get_file_resource_path('pcnt_diff_data.json')) as json_file:
        json_pcnt_diff = json.load(json_file)
        return json_pcnt_diff
