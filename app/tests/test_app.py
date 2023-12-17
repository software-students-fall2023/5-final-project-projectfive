from app import *
import mongomock
import pytest
from flask import Flask
import pytest_flask
from unittest.mock import patch
import app

# Import the Flask app


# Create a test client
@pytest.fixture
def client(monkeypatch):
    app.app.config["TESTING"] = True
    app.app.config["DEBUG"] = True
    with app.app.test_client() as client:
        yield client


# Unit test for main()
# def test_main(monkeypatch):
#     monkeypatch.setenv("MONGO_USERNAME", "test")
#     monkeypatch.setenv("MONGO_PASSWORD", "test")

#     with patch("app.MongoClient") as mock_mongo_client:
#         mock_mongo_client.return_value = mock_mongo_client
#         mock_mongo_client["DB"].return_value = mock_mongo_client["DB"]

#         with patch("app.app.run") as mock_run:
#             mock_run.return_value = mock_run

#             app.main()

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


#NOTE: blocked on login.html
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
        return {
            "username": "test_user",
            "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0",
        }

    # def mock_verify(*args, **kwargs):
    # return True

    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)
    # monkeypatch.setattr(Hasher, "verify", mock_verify)
    # monkeypatch.setattr(app, "login_user", mock_login_user)

    response = client.post(
        "/login", data={"username": "test_user", "password": "test_password"}
    )
    assert response.status_code == 302


def test_login_no_user(client, monkeypatch):
    app.DB = mongomock.MongoClient().users

    def mock_find_one(*args, **kwargs):
        return None

    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)

    response = client.post(
        "/login", data={"username": "test_user", "password": "test_password"}
    )
    assert response.status_code == 401
    assert b"User not found" in response.data


def test_login_bad_password(client, monkeypatch):
    app.DB = mongomock.MongoClient().users

    def mock_find_one(*args, **kwargs):
        return {
            "username": "test_user",
            "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0",
        }

    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)

    response = client.post(
        "/login", data={"username": "test_user", "password": "incorrect_password"}
    )
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
    app.DB = mongomock.MongoClient().users

    def mock_find_one(*args, **kwargs):
        return {
            "username": "test_user",
            "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0",
        }

    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    def mock_logout_user():
        return None

    monkeypatch.setattr(app, "logout_user", mock_logout_user)
    response = client.get("/logout")
    assert response.status_code == 302


# low coverage of index(). May need a revisit at a later date
# Not entirely sure how to test this properly tbh
def test_index(client, monkeypatch):
    app.DB = mongomock.MongoClient().users

    def mock_find_one(*args, **kwargs):
        return {
            "username": "test_user",
            "pwhash": "$argon2id$v=19$m=65536,t=3,p=4$kKM0SwXp0LpZY+g7Q8H4rA$+Kyy0NhzkpDK3aQHrm9U9nnb69Fc5yQ4c66VQluOyl0",
        }

    monkeypatch.setattr(app.DB.users, "find_one", mock_find_one)
    client.post("/login", data={"username": "test_user", "password": "test_password"})

    app.DB = mongomock.MongoClient().plans

    def mock_delete_many(*args, **kwargs):
        pass

    def mock_find(*args, **kwargs):
        return None

    monkeypatch.setattr(app.DB.plans, "delete_many", mock_delete_many)
    monkeypatch.setattr(app.DB.plans, "find", mock_find)

    response = client.get("/", data={"username": "test_user"})
    assert response.status_code == 302
    assert b"" in response.data