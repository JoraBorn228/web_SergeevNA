import sys
import os
import pytest

# Добавляем папку app в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app as flask_app


@pytest.fixture
def app():
    flask_app.config.update({'TESTING': True})
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
