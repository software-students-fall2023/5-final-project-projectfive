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
    with app.app.test_client() as client:
        yield client


# Unit test for main()
def test_main(monkeypatch):
    monkeypatch.setenv("MONGO_USERNAME", "test")
    monkeypatch.setenv("MONGO_PASSWORD", "test")

    with patch("app.MongoClient") as mock_mongo_client:
        mock_mongo_client.return_value = mock_mongo_client
        mock_mongo_client["DB"].return_value = mock_mongo_client["DB"]

        with patch("app.app.run") as mock_run:
            mock_run.return_value = mock_run

            main()

            mock_mongo_client.assert_called_once_with("mongodb://test:test@mongo")
            # Debugging is optional, but it is always specified.
            try:
                mock_run.assert_called_once_with(host="0.0.0.0", port=443, debug=True)
            except AssertionError:
                mock_run.assert_called_once_with(host="0.0.0.0", port=443, debug=False)


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


# TODO: Need login.html
# def test_login_get(client):
#     response = client.get("/login")
#     assert response.status_code >= 200


def test_login_post_bad_request(client):
    response = client.post("/login", data={})
    assert response.status_code == 400
    assert b"Missing username or password" in response.data


def test_login_post(client):
    pass


def test_logout(client, monkeypatch):
    def mock_logout_user():
        return None

    monkeypatch.setattr(app, "logout_user", mock_logout_user)
    response = client.get("/logout")
    assert response.status_code == 302
