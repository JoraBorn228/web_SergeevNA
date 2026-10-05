import pytest
from app import create_app
from app.models import Category, Course, Image, User, db


@pytest.fixture
def app(tmp_path):
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{tmp_path / 'test.sqlite'}",
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
    })
    with application.app_context():
        db.create_all()
        user = User(first_name='Иван', last_name='Иванов', login='user')
        user.set_password('password')
        category = Category(name='Программирование')
        image = Image(id='test-image', file_name='test.jpg', mime_type='image/jpeg', md5_hash='test-hash')
        db.session.add_all([user, category, image])
        db.session.flush()
        course = Course(name='Flask', short_desc='Коротко', full_desc='Описание', category_id=category.id,
                        author_id=user.id, background_image_id=image.id)
        db.session.add(course)
        db.session.commit()
        application.config['TEST_COURSE_ID'] = course.id
        application.config['TEST_USER_ID'] = user.id
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    def _login():
        return client.post('/auth/login', data={'login': 'user', 'password': 'password'}, follow_redirects=True)
    return _login
