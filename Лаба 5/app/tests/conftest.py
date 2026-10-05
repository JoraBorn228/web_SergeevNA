"""Общие фикстуры для тестов Лабораторной работы №5."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app  # noqa: E402
import db as db_module  # noqa: E402

ADMIN_LOGIN = 'admin'
ADMIN_PASSWORD = 'Admin123'
USER_LOGIN = 'user'
USER_PASSWORD = 'User123'


@pytest.fixture
def app(tmp_path):
    """Приложение с изолированной временной БД для каждого теста."""
    database = str(tmp_path / 'test.sqlite')
    flask_app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'DATABASE': database,
    })
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    """Клиент, аутентифицированный как администратор."""
    client.post('/login', data={'login': ADMIN_LOGIN, 'password': ADMIN_PASSWORD})
    return client


@pytest.fixture
def user_client(client):
    """Клиент, аутентифицированный как обычный пользователь."""
    client.post('/login', data={'login': USER_LOGIN, 'password': USER_PASSWORD})
    return client


@pytest.fixture
def add_user(app):
    """Фабрика: создаёт пользователя в БД и возвращает его id."""
    def _add_user(login='testuser', password='Testpass1',
                  last_name='Иванов', first_name='Иван',
                  middle_name='Иванович', role_id=None):
        with app.app_context():
            return db_module.create_user(
                login, password, last_name, first_name, middle_name, role_id
            )
    return _add_user


@pytest.fixture
def user_id(app):
    """id обычного пользователя 'user'."""
    with app.app_context():
        return db_module.get_user_by_login(USER_LOGIN)['id']


@pytest.fixture
def admin_id(app):
    """id администратора 'admin'."""
    with app.app_context():
        return db_module.get_user_by_login(ADMIN_LOGIN)['id']
