from pathlib import Path

import pytest

from app import create_app, db
from app.models import Book, Cover, Genre, Role, User


@pytest.fixture
def app(tmp_path):
    upload_dir = tmp_path / 'covers'
    upload_dir.mkdir()
    application = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-key',
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{tmp_path / 'test.sqlite'}",
        'UPLOAD_FOLDER': str(upload_dir),
    })
    with application.app_context():
        db.create_all()
        admin_role = Role(name='Администратор', description='admin')
        mod_role = Role(name='Модератор', description='moderator')
        reader_role = Role(name='Пользователь', description='reader')
        db.session.add_all([admin_role, mod_role, reader_role])
        db.session.flush()
        users = [
            User(login='admin', first_name='Админ', last_name='Тестов', role=admin_role),
            User(login='moderator', first_name='Модератор', last_name='Тестов', role=mod_role),
            User(login='reader', first_name='Читатель', last_name='Тестов', role=reader_role),
        ]
        for user in users:
            user.set_password('password123')
        genre = Genre(name='Фантастика')
        book = Book(title='Тестовая книга', short_description='Кратко', description='**Текст**',
                    year=2020, publisher='Издательство', author='Автор', page_count=200,
                    genres=[genre])
        db.session.add_all([*users, genre, book])
        db.session.flush()
        cover_file = upload_dir / 'cover.png'
        cover_file.write_bytes(b'cover bytes')
        book.cover = Cover(file_name='cover.png', mime_type='image/png', md5_hash='0123456789abcdef0123456789abcdef')
        db.session.commit()
        application.config['TEST_BOOK_ID'] = book.id
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    def _login(login_name='reader'):
        return client.post('/auth/login', data={'login': login_name, 'password': 'password123'}, follow_redirects=True)
    return _login
