import pytest
import main

@pytest.fixture()
def app():
    app = main.app
    app.config["WTF_CSRF_ENABLED"] = False
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()