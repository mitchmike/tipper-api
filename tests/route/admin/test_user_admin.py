from db_test_util import *
from model import User



def test_admin_required(app, client):
    add_data(app, User, USER_COL_NAMES, [1, 'email', 'p', []])
    add_data(app, User, USER_COL_NAMES, [2, 'email2', 'p', ['ADMIN']])
    with client.session_transaction() as pre_session:
        pre_session['user_id'] = 1
    with client:
        response = client.get("/admin", follow_redirects=True)
        assert response.request.path == "/auth/login"
        assert len(response.history) == 2
        assert '''<title>Tipper - 
    Log In
</title>''' in response.text
        assert response.status_code == 200
        with client.session_transaction() as pre_session:
            pre_session['user_id'] = 2
        response = client.get("/admin", follow_redirects=True)
        assert response.request.path == "/admin/"
        assert "<title>Tipper - Admin Home</title>" in response.text


def test_users(app, client):
    add_data(app, User, USER_COL_NAMES, [1, 'email2', 'p', ['ADMIN']])
    with client:
        with client.session_transaction() as pre_session:
            pre_session['user_id'] = 1
        response = client.get("/admin/users", follow_redirects=True)
        assert response.status_code == 200
        assert '<title>Tipper - User Management</title>' in response.text


def test_detail(app, client):
    add_data(app, User, USER_COL_NAMES, [1, 'email2', 'p', ['ADMIN']])
    with client:
        with client.session_transaction() as pre_session:
            pre_session['user_id'] = 1
        response = client.get("/admin/users/detail?user_edit_id=1", follow_redirects=True)
        assert response.status_code == 200
        assert '<title>Tipper - User Detail</title>' in response.text


def test_create(app, client):
    add_data(app, User, USER_COL_NAMES, [1, 'email2', 'p', ['ADMIN']])
    with client:
        with client.session_transaction() as pre_session:
            pre_session['user_id'] = 1
        response = client.get("/admin/users/create", follow_redirects=True)
        assert response.status_code == 200
        assert '<title>Tipper - User Detail</title>' in response.text

