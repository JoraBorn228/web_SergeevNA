from app.models import Course, Review, db


def test_course_shows_reviews_and_link(client, app):
    with app.app_context():
        db.session.add(Review(rating=4, text='Хороший курс', course_id=app.config['TEST_COURSE_ID'],
                              user_id=app.config['TEST_USER_ID']))
        db.session.commit()
    response = client.get(f"/courses/{app.config['TEST_COURSE_ID']}")
    assert response.status_code == 200
    assert 'Хороший курс' in response.get_data(as_text=True)
    assert 'Все отзывы' in response.get_data(as_text=True)


def test_review_create_updates_course_rating(client, app, login):
    login()
    response = client.post(f"/courses/{app.config['TEST_COURSE_ID']}/reviews",
                           data={'rating': '5', 'text': 'Отлично!'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Отзыв успешно добавлен' in response.get_data(as_text=True)
    with app.app_context():
        course = db.session.get(Course, app.config['TEST_COURSE_ID'])
        assert (course.rating_sum, course.rating_num) == (5, 1)


def test_user_cannot_submit_second_review(client, app, login):
    login()
    endpoint = f"/courses/{app.config['TEST_COURSE_ID']}/reviews"
    client.post(endpoint, data={'rating': '3', 'text': 'Первый'})
    client.post(endpoint, data={'rating': '4', 'text': 'Второй'}, follow_redirects=True)
    with app.app_context():
        assert db.session.query(Review).count() == 1


def test_invalid_review_is_not_saved(client, app, login):
    login()
    response = client.post(f"/courses/{app.config['TEST_COURSE_ID']}/reviews",
                           data={'rating': '8', 'text': ''}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.query(Review).count() == 0


def test_reviews_page_keeps_sort_in_pagination(client, app):
    with app.app_context():
        db.session.add_all([
            Review(rating=i % 6, text=f'Review {i}', course_id=app.config['TEST_COURSE_ID'],
                   user_id=None)
            for i in range(11)
        ])
        db.session.commit()
    response = client.get(f"/courses/{app.config['TEST_COURSE_ID']}/reviews?sort=positive")
    assert response.status_code == 200
    assert 'Сначала положительные' in response.get_data(as_text=True)
    assert 'sort=positive' in response.get_data(as_text=True)
    assert 'page=2' in response.get_data(as_text=True)


def test_missing_course_reviews_returns_404(client):
    assert client.get('/courses/999/reviews').status_code == 404
