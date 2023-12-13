from app import main, app
import mongomock
import pytest
from flask import Flask
import pytest_flask
from unittest.mock import patch

# Import the Flask app


# Create a test client
@pytest.fixture
def client(monkeypatch):
    app.config["TESTING"] = True
    with app.test_client() as client:
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
