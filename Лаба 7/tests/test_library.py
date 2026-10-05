from datetime import datetime, timedelta
from io import BytesIO

from app import db
from app.models import Book, BookView, Review, User


def test_anonymous_can_view_home_and_book_and_recently_seen(client, app):
    book_url = f"/books/{app.config['TEST_BOOK_ID']}"
    assert client.get('/').status_code == 200
    response = client.get(book_url)
    assert response.status_code == 200
    assert 'Сергеев Никита Андреевич' in response.get_data(as_text=True)
    home = client.get('/').get_data(as_text=True)
    assert 'Недавно просмотренные книги' in home


def test_view_limit_is_ten_per_user_book_per_day(client, app, login):
    login()
    book_url = f"/books/{app.config['TEST_BOOK_ID']}"
    for _ in range(12):
        assert client.get(book_url).status_code == 200
    with app.app_context():
        assert BookView.query.filter_by(book_id=app.config['TEST_BOOK_ID']).count() == 10


def test_recent_view_limit_also_applies_to_anonymous_client(client, app):
    book_url = f"/books/{app.config['TEST_BOOK_ID']}"
    for _ in range(12):
        client.get(book_url)
    with app.app_context():
        assert BookView.query.filter_by(book_id=app.config['TEST_BOOK_ID'], user_id=None).count() == 10


def test_admin_statistics_are_role_protected(client, login):
    response = client.get('/statistics')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']
    login('reader')
    response = client.get('/statistics', follow_redirects=True)
    assert 'недостаточно прав' in response.get_data(as_text=True).lower()


def test_admin_can_view_logs_and_download_csv(client, login, app):
    login('reader')
    client.get(f"/books/{app.config['TEST_BOOK_ID']}")
    client.post('/auth/logout')
    login('admin')
    response = client.get('/statistics?tab=logs')
    assert response.status_code == 200
    assert 'Журнал действий пользователей' in response.get_data(as_text=True)
    csv_response = client.get('/statistics/logs.csv')
    assert csv_response.status_code == 200
    assert 'attachment;' in csv_response.headers['Content-Disposition']
    assert 'Тестовая книга' in csv_response.get_data(as_text=True)


def test_authenticated_view_stats_exclude_anonymous_visits(client, app, login):
    with app.app_context():
        book = db.session.get(Book, app.config['TEST_BOOK_ID'])
        reader = User.query.filter_by(login='reader').first()
        db.session.add_all([
            BookView(book=book, user=reader, viewed_at=datetime.utcnow() - timedelta(days=1)),
            BookView(book=book, visitor_id='anon', viewed_at=datetime.utcnow() - timedelta(days=1)),
        ])
        db.session.commit()
    login('admin')
    response = client.get('/statistics?tab=views')
    assert response.status_code == 200
    assert 'Количество просмотров' in response.get_data(as_text=True)
    csv_response = client.get('/statistics/views.csv')
    assert csv_response.status_code == 200
    assert 'Тестовая книга,1' in csv_response.get_data(as_text=True)


def test_reader_can_leave_only_one_review(client, app, login):
    login('reader')
    review_url = f"/books/{app.config['TEST_BOOK_ID']}/reviews/new"
    response = client.post(review_url, data={'rating': '5', 'text': '**Отличная книга**'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Отличная книга' in response.get_data(as_text=True)
    client.post(review_url, data={'rating': '4', 'text': 'Вторая'}, follow_redirects=True)
    with app.app_context():
        assert Review.query.filter_by(book_id=app.config['TEST_BOOK_ID']).count() == 1


def test_catalog_is_paginated_to_ten_books(client, app):
    with app.app_context():
        genre = db.session.query(Book).first().genres[0]
        for index in range(11):
            db.session.add(Book(title=f'Книга {index}', short_description='Кратко', description='Текст',
                                year=2000 + index, publisher='Издательство', author='Автор',
                                page_count=100, genres=[genre]))
        db.session.commit()
    first_page = client.get('/').get_data(as_text=True)
    assert first_page.count('Просмотр</a>') == 10
    second_page = client.get('/?page=2').get_data(as_text=True)
    assert 'Книга 0' in second_page


def test_admin_can_add_book_with_uploaded_cover(client, app, login):
    login('admin')
    with app.app_context():
        from app.models import Genre
        genre_id = Genre.query.first().id
    response = client.post('/books/new', data={
        'title': 'Новая книга', 'short_description': 'Краткое описание',
        'description': '# Описание', 'year': '2024', 'publisher': 'Политех',
        'author': 'Никита Сергеев', 'page_count': '250', 'genre_ids': str(genre_id),
        'cover': (BytesIO(b'fake png data'), 'cover.png', 'image/png'),
    }, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert 'Новая книга' in response.get_data(as_text=True)
    with app.app_context():
        assert Book.query.filter_by(title='Новая книга').first().cover is not None


def test_moderator_can_edit_book(client, app, login):
    login('moderator')
    response = client.post(f"/books/{app.config['TEST_BOOK_ID']}/edit", data={
        'title': 'Изменённое название', 'short_description': 'Кратко',
        'description': '**Описание**', 'year': '2021', 'publisher': 'Издательство',
        'author': 'Автор', 'page_count': '201', 'genre_ids': '1',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Изменённое название' in response.get_data(as_text=True)


def test_moderator_can_hide_review(client, app, login):
    with app.app_context():
        review = Review(book_id=app.config['TEST_BOOK_ID'], user_id=2, rating=4, text='Проверяемая рецензия')
        db.session.add(review)
        db.session.commit()
        review_id = review.id
    login('moderator')
    client.post(f'/reviews/{review_id}/moderate')
    client.post('/auth/logout')
    response = client.get(f"/books/{app.config['TEST_BOOK_ID']}")
    assert response.status_code == 200
    assert 'Проверяемая рецензия' not in response.get_data(as_text=True)
    with app.app_context():
        assert db.session.get(Review, review_id).approved is False
