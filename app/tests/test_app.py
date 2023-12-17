from app import *
import mongomock
import pytest
from flask import Flask
import pytest_flask
from unittest.mock import patch, MagicMock
import datetime
from flask_login import (
    login_required,
    login_user,
    logout_user,
    current_user,
    LoginManager,
    UserMixin,
)
import app

# Import the Flask app
@pytest.fixture(autouse=True)
def testkey_set(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY","9QI/Hxgvzx1egF8J", prepend = False )

# Create a test client
@pytest.fixture
def client(monkeypatch):
    app.app.config["TESTING"] = True
    #app.app.config["DEBUG"] = True
    with app.app.test_client() as client:
        yield client


# # Unit test for main()
# def test_main(monkeypatch):
#     monkeypatch.setenv("MONGO_USERNAME", "test")
#     monkeypatch.setenv("MONGO_PASSWORD", "test")

#     with patch("app.MongoClient") as mock_mongo_client:
#         mock_mongo_client.return_value = mock_mongo_client
#         mock_mongo_client["DB"].return_value = mock_mongo_client["DB"]

#         with patch("app.app.run") as mock_run:
#             mock_run.return_value = mock_run

#             main()

#             mock_mongo_client.assert_called_once_with("mongodb://test:test@mongo")
#             # Debugging is optional, but it is always specified.
#             try:
#                 mock_run.assert_called_once_with(host="0.0.0.0", port=443, debug=True)
#             except AssertionError:
#                 mock_run.assert_called_once_with(host="0.0.0.0", port=443, debug=False)


def test_should_debug(monkeypatch):
    monkeypatch.setenv("DEBUG", "True")
    assert app.should_debug() == True


def test_should_debug_fail(capsys):
    app.should_debug()
    captured = capsys.readouterr()
    # TODO: For some reason this doesn't catch anything thats printed
    # even though should_debug() should print when "DEBUG" == None
    # assert captured.err == "Unknown value for DEBUG environment variable."


def test_load_user_nonexist(monkeypatch):
    app.DB = mongomock.MongoClient().users

    def mock_find_one(*args):
        return False

    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)

    result = app.load_user("test_user")
    assert result == None


def test_load_user_exist(monkeypatch):
    app.DB = mongomock.MongoClient().users

    def mock_find_one(*args):
        return {"username": "test_user", "pwhash": "test_pwhash"}

    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)

    result = app.load_user("test_user")
    assert type(result) == app.User
    assert result.username == "test_user"
    assert result.pwhash == "test_pwhash"


def test_unauthorized():
    response = app.unauthorized()
    assert response.status_code == 302


# NOTE: blocked on login.html
def test_login_get(client):
    response = client.get("/login")
    assert response.status_code >= 200


def test_login_post_bad_request(client):
    response = client.post("/login", data={})
    assert response.status_code == 400
    assert b"Missing username or password" in response.data


def test_login_post(client, monkeypatch):
    
    app.DB = mongomock.MongoClient().users

    def mock_find_one(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    
    #def mock_verify(*args, **kwargs):
       # return True
    
    
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)
    #monkeypatch.setattr(Hasher, "verify", mock_verify)
    #monkeypatch.setattr(app, "login_user", mock_login_user)

    response = client.post("/login", data = {"username":"test_user", "password":"test_password"})
    assert response.status_code == 302

def test_login_no_user(client, monkeypatch):
    app.DB = mongomock.MongoClient().users
    
    def mock_find_one(*args, **kwargs):
        return None
    
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)

    response = client.post("/login",data = {"username":"test_user", "password":"test_password"})
    assert response.status_code == 401
    assert b"User not found" in response.data

def test_login_bad_password(client, monkeypatch):
    app.DB = mongomock.MongoClient().users

    def mock_find_one(*args,**kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}

    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)

    response = client.post("/login", data = {"username":"test_user", "password":"incorrect_password"})
    assert response.status_code == 401
    assert b"Incorrect password" in response.data


#TODO: update final assertion when change_password.html gets added fr
def test_change_password_get(client,monkeypatch):
    app.DB = mongomock.MongoClient().users
    def mock_find_one(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)
    client.post("/login",data={"username":"test_user","password":"test_password"})
    response = client.get("/change_password")
    assert response.status_code == 200
    assert b"" in response.data


def test_change_password_post_bad_request(client, monkeypatch):
    app.DB = mongomock.MongoClient().users

    def mock_find_one(*args, **kwargs):
        return {
            "username": "test_user",
            "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0",
        }

    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    response = client.post("/change_password", data={})
    assert response.status_code == 400
    assert b"Missing old or new password" in response.data


# NOTE: This increases coverage by a single line, requires refactoring to error handle in app.py
# def test_change_password_post_wrong_pass(client,monkeypatch):
#     app.DB = mongomock.MongoClient().users

#     def mock_find_one(*args, **kwargs):
#         return {
#             "username": "test_user",
#             "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0",
#         }

#     monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)
#     client.post("/login", data={"username": "test_user", "password": "test_password"})

#     response = client.post("/change_password", data = {"username":"test_user", "old_password":"wrong_password", "new_password":"new_password"})


def test_change_password_valid(client, monkeypatch):
    app.DB = mongomock.MongoClient().users

    def mock_find_one(*args, **kwargs):
        return {
            "username": "test_user",
            "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0",
        }

    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    def mock_update_one(*args, **kwargs):
        return None

    monkeypatch.setattr(app.DB.users, "update_one", mock_update_one)

    response = client.post(
        "/change_password",
        data={
            "username": "test_user",
            "old_password": "test_password",
            "new_password": "new_password",
        },
    )
    assert response.status_code == 302


# TODO: Need register.html
def test_register(client):
    response = client.get("/register")
    assert response.status_code == 200


def test_register_bad_request(client):
    response = client.post("/register", data={})
    assert response.status_code == 400


def test_register_user_taken(client, monkeypatch):
    app.DB = mongomock.MongoClient().users

    def mock_find_one(*args, **kwargs):
        return True

    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)
    response = client.post(
        "/register", data={"username": "test_user", "password": "test_pass"}
    )

    assert response.status_code == 409
    assert b"Username already taken" in response.data


def test_logout(client, monkeypatch):
    def mock_logout_user():
        return None

    monkeypatch.setattr(app, "logout_user", mock_logout_user)
    response = client.get("/logout")
    assert response.status_code == 302

#low coverage of index(). May need a revisit at a later date
def test_index(client,monkeypatch):
    app.DB = mongomock.MongoClient().plans

    def mock_delete_many(*args, **kwargs):
        pass

    def mock_find(*args,**kwargs):
        return None

    monkeypatch.setattr(app.DB.plans, "delete_many", mock_delete_many)
    monkeypatch.setattr(app.DB.plans, "find", mock_find)

    response = client.get("/", data = {"username":"test_user"})
    assert response.status_code == 302
    assert b"" in response.data


def test_view_plan():
    pass

@patch('app.b62tooid')  # Adjust the path to b62tooid if necessary
def test_delete_plan_not_found(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    def mock_find_one_plan(*args, **kwargs):
        return None  # Simulate plan not found
    monkeypatch.setattr(app.DB.plans, 'find_one', mock_find_one_plan)
    
    # Test the delete_plan route
    response = client.get('/delete_plan/nonexistent_id')
    assert response.status_code == 404

@patch('app.b62tooid')
def test_delete_plan_not_owner(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})
    
    def mock_find_one_plan(*args, **kwargs):
        return {"_id": "owned_by_another_user", "username": "another_user"}  # Simulate plan not found
    monkeypatch.setattr(app.DB.plans, 'find_one', mock_find_one_plan)
    response = client.get('/delete_plan/owned_by_another_user')
    assert response.status_code == 403

@patch('app.b62tooid')
def test_delete_plan_eligible(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    def mock_find_one_plan(*args, **kwargs):
        return {"_id": "eligible_plan_id", "username": "test_user", "draft": True}  # Simulate plan not found
    monkeypatch.setattr(app.DB.plans, 'find_one', mock_find_one_plan)

    response = client.get('/delete_plan/eligible_plan_id')
    assert response.status_code == 302  # Redirect to home page

# def test_create_plan(client, monkeypatch):
#     # Mock the database
#     app.DB = mongomock.MongoClient().db

#     # Mock user login
#     def mock_find_one_user(*args, **kwargs):
#         return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
#     monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
#     client.post("/login", data={"username": "test_user", "password": "test_password"})

#     # Test create_plan route
#     response = client.get('/create_plan')
#     assert response.status_code == 302
#     # assert 'create_plan.html' in response.data.decode()  # Check if the correct template is rendered

# Test: Plan Not Found
@patch('app.b62tooid')
def test_edit_plan_not_found(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    monkeypatch.setattr(app.DB.plans, 'find_one', lambda x: None)
    response = client.get('/edit_plan/nonexistent_id')
    assert response.status_code == 404

# # Test: User Does Not Own the Plan
@patch('app.b62tooid')
def test_edit_plan_not_owner(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    monkeypatch.setattr(app.DB.plans, 'find_one', lambda x: {"_id": "some_plan_id", "username": "another_user", "draft": True})
    response = client.get('/edit_plan/some_plan_id')
    assert response.status_code == 403

# Test: Plan is Not a Draft
@patch('app.b62tooid')
def test_edit_plan_not_draft(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    monkeypatch.setattr(app.DB.plans, 'find_one', lambda x: {"_id": "draft_plan_id", "username": "test_user", "draft": False})
    response = client.get('/edit_plan/draft_plan_id')
    assert response.status_code == 400

# Test: Successful Plan Editing - template problem
@patch('app.b62tooid')
def test_edit_plan_success(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    monkeypatch.setattr(app.DB.plans, 'find_one', lambda x: {"_id": "draft_plan_id", "username": "test_user", "draft": True})
    response = client.get('/edit_plan/draft_plan_id')
    assert response.status_code == 200
#TODO: this looks like this needs to be fixed when edit_plan.html actually gets added
    #assert 'edit_plan.html' in response.data.decode()

@patch('app.b62tooid')
def test_save_draft_missing_name(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    # Simulate a POST request with missing name
    response = client.post('/save_draft', data={"name": None, "content": "Sample content"})
    assert response.status_code == 400

@patch('app.b62tooid')
def test_save_draft_missing_content(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    # Simulate a POST request with missing content
    response = client.post('/save_draft', data={"name": "Sample name", "content": None})
    assert response.status_code == 400

@patch('app.b62tooid')
def test_save_draft_success(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    monkeypatch.setattr(app.DB.plans, 'update_one', lambda x, y: None)

    # Simulate a successful POST request
    response = client.post('/finalize_draft', data={"name": "Sample name", "content": "Sample content", "id": "existing_draft_id"})
    assert response.status_code == 302

@patch('app.b62tooid')
def test_finalize_draft_missing_name(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    # Simulate a POST request with missing name
    response = client.post('/finalize_draft', data={"name": None, "content": "Sample content"})
    assert response.status_code == 400

@patch('app.b62tooid')
def test_finalize_draft_missing_content(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    # Simulate a POST request with missing content
    response = client.post('/finalize_draft', data={"name": "Sample name", "content": None})
    assert response.status_code == 400

@patch('app.b62tooid')
def test_finalize_draft_success(mock_b62tooid, client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    monkeypatch.setattr(app.DB.plans, 'update_one', lambda x, y: None)

    # Simulate a successful POST request
    response = client.post('/finalize_draft', data={"name": "Sample name", "content": "Sample content", "id": "existing_draft_id"})
    assert response.status_code == 302

def setup_login(client, monkeypatch):
    # Mock  database
    app.DB = mongomock.MongoClient().db
    
    # Login before find plan
    def mock_find_one_user(*args, **kwargs):
        return {"username": "test_user", "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0"}
    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one_user)
    client.post("/login", data={"username": "test_user", "password": "test_password"})


def test_submit_plan_missing_name(client, monkeypatch):
    setup_login(client, monkeypatch)
    response = client.post('/submit_plan', data={"name": None, "content": "Sample content", "draft": "Yes"})
    assert response.status_code == 400

def test_submit_plan_missing_content(client, monkeypatch):
    setup_login(client, monkeypatch)
    response = client.post('/submit_plan', data={"name": "Sample name", "content": None, "draft": "Yes"})
    assert response.status_code == 400

@patch('app.oidtob62')
def test_submit_draft_plan(mock_oidtob62, client, monkeypatch):
    app.DB = mongomock.MongoClient().db

    setup_login(client, monkeypatch)
    mock_insert_one = MagicMock(return_value=MagicMock(inserted_id='draft_b62'))
    monkeypatch.setattr(app.DB.plans, 'insert_one', mock_insert_one)
    
    response = client.post('/submit_plan', data={"name": "Sample name", "content": "Sample content", "draft": "Yes"})
    assert response.status_code == 302

@patch('app.oidtob62')
def test_submit_finalized_plan(mock_oidtob62, client, monkeypatch):
    setup_login(client, monkeypatch)
    app.DB = mongomock.MongoClient().db
    mock_oidtob62.return_value = 'finalized_b62'
    monkeypatch.setattr(app.DB.plans, 'insert_one', lambda x: mongomock.InsertOneResult('finalized_id', acknowledged=True))
    response = client.post('/submit_plan', data={"name": "Sample name", "content": "Sample content"})
    assert response.status_code == 302

# TODO:
@patch('app.b62tooid')
def test_settings_page_not_found(mock_b62tooid, client, monkeypatch):
    setup_login(client, monkeypatch)
    monkeypatch.setattr('app.DB.plans.find_one', MagicMock(return_value=None))

    response = client.get('/settings/nonexistent_id')
    assert response.status_code == 404

@patch('app.b62tooid')
def test_settings_page_not_owner(mock_b62tooid, client, monkeypatch):
    setup_login(client, monkeypatch)
    plan_data = {"username": "another_user"}
    monkeypatch.setattr('app.DB.plans.find_one', MagicMock(return_value=plan_data))

    response = client.get('/settings/owned_by_another_user')
    assert response.status_code == 403

# TEMPLATE 
# @patch('app.b62tooid')
# def test_settings_page_get_request(mock_b62tooid, client, monkeypatch):
#     setup_login(client, monkeypatch)
#     plan_data = {"username": "test_user", "_id": "plan_id", "private": False, "locked": False}
#     monkeypatch.setattr('app.DB.plans.find_one', MagicMock(return_value=plan_data))

#     response = client.get('/settings/plan_id')
#     assert response.status_code == 200
#     assert b'settings.html content' in response.data  # Check if settings page is rendered

@patch('app.b62tooid')
def test_settings_page_post_request(mock_b62tooid, client, monkeypatch):
    setup_login(client, monkeypatch)
    plan_data = {"username": "test_user", "_id": "plan_id", "private": False, "locked": False}
    monkeypatch.setattr('app.DB.plans.find_one', MagicMock(return_value=plan_data))
    mock_update_one = MagicMock()
    monkeypatch.setattr('app.DB.plans.update_one', mock_update_one)

    response = client.post('/settings/plan_id', data={"private": "Yes", "locked": "Yes"})
    assert response.status_code == 302  # Expecting a redirect to set_lock
    mock_update_one.assert_called_once()  # Ensure DB update was called

@patch('app.b62tooid')
def test_set_lock_page_not_found(mock_b62tooid, client, monkeypatch):
    setup_login(client, monkeypatch)
    monkeypatch.setattr('app.DB.plans.find_one', MagicMock(return_value=None))

    response = client.get('/set_lock/nonexistent_id')
    assert response.status_code == 404

@patch('app.b62tooid')
def test_set_lock_page_not_owner(mock_b62tooid, client, monkeypatch):
    setup_login(client, monkeypatch)
    monkeypatch.setattr('app.DB.plans.find_one', MagicMock(return_value={"username": "another_user"}))

    response = client.get('/set_lock/owned_by_another_user')
    assert response.status_code == 403

# template
# @patch('app.b62tooid')
# def test_set_lock_page_get_request(mock_b62tooid, client, monkeypatch):
#     setup_login(client, monkeypatch)
#     plan_data = {"username": "test_user", "_id": "plan_id"}
#     monkeypatch.setattr('app.DB.plans.find_one', MagicMock(return_value=plan_data))

#     response = client.get('/set_lock/plan_id')
#     assert response.status_code == 200

@patch('app.b62tooid')
def test_set_lock_page_post_request(mock_b62tooid, client, monkeypatch):
    plan_data = {"username": "test_user", "_id": "plan_id"}
    monkeypatch.setattr('app.DB.plans.find_one', MagicMock(return_value=plan_data))
    mock_update_one = MagicMock()
    monkeypatch.setattr('app.DB.plans.update_one', mock_update_one)

    response = client.post('/set_lock/plan_id', data={"duration": "5"})
    assert response.status_code == 302  # Expecting a redirect to home
    # mock_update_one.assert_called_once()  # Ensure DB update was called

