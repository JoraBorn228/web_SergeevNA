"""Create repeatable local demo data for the course reviews feature."""
from pathlib import Path

from app import create_app
from app.models import Category, Course, Image, Review, User, db


DEMO_USERS = {
    'demo': ('Демо', 'Пользователь', 'demo12345'),
    'maria': ('Мария', 'Соколова', 'maria12345'),
    'alex': ('Алексей', 'Петров', 'alex12345'),
    'irina': ('Ирина', 'Кузнецова', 'irina12345'),
}

DEMO_COURSES = {
    'Основы Flask': (
        'Практический курс по созданию веб-приложений на Flask.',
        'Демонстрационный курс по Flask. Оставьте отзыв и проверьте обновление рейтинга.',
        'demo',
    ),
    'Python для начинающих': (
        'Переменные, функции, коллекции и первые программы на Python.',
        'Курс знакомит с основами Python на практических примерах.',
        'maria',
    ),
    'SQL и базы данных': (
        'Запросы SQL, таблицы и связи между данными.',
        'Практика чтения и изменения данных в реляционных базах.',
        'alex',
    ),
}

DEMO_REVIEWS = [
    ('Основы Flask', 'demo', 5, 'Понятные примеры, получилось собрать первое приложение.'),
    ('Основы Flask', 'maria', 4, 'Хороший курс, хотелось бы ещё пару занятий про формы.'),
    ('Основы Flask', 'alex', 5, 'Материал изложен последовательно и без лишнего.'),
    ('Основы Flask', 'irina', 3, 'Полезно для старта, некоторые темы пришлось повторить.'),
    ('Python для начинающих', 'demo', 5, 'Отличный вводный курс, задания помогают закрепить материал.'),
    ('Python для начинающих', 'maria', 5, 'Много практики и хорошие объяснения.'),
    ('Python для начинающих', 'alex', 3, 'Неплохо, но хотелось бы больше задач посложнее.'),
    ('SQL и базы данных', 'demo', 4, 'Понравились примеры запросов и работа с таблицами.'),
    ('SQL и базы данных', 'maria', 2, 'Некоторые темы раскрыты слишком кратко.'),
    ('SQL и базы данных', 'irina', 5, 'После курса стало намного понятнее, как строить запросы.'),
]


app = create_app()

with app.app_context():
    # create_all makes this helper convenient for a fresh local checkout too.
    db.create_all()

    users = {}
    for login, (first_name, last_name, password) in DEMO_USERS.items():
        user = db.session.execute(
            db.select(User).filter_by(login=login)
        ).scalar_one_or_none()
        if user is None:
            user = User(first_name=first_name, last_name=last_name, login=login)
            user.set_password(password)
            db.session.add(user)
        else:
            user.first_name = first_name
            user.last_name = last_name
        users[login] = user

    category = db.session.execute(
        db.select(Category).filter_by(name='Программирование')
    ).scalar_one_or_none()
    if category is None:
        category = Category(name='Программирование')
        db.session.add(category)

    image = db.session.get(Image, 'demo-course-bg')
    if image is None:
        upload_folder = Path(app.config['UPLOAD_FOLDER'])
        upload_folder.mkdir(parents=True, exist_ok=True)
        (upload_folder / 'demo-course-bg.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="500" '
            'viewBox="0 0 1400 500"><defs><linearGradient id="g">'
            '<stop stop-color="#111827"/><stop offset="1" stop-color="#4f46e5"/>'
            '</linearGradient></defs><rect width="1400" height="500" fill="url(#g)"/>'
            '<circle cx="1120" cy="130" r="260" fill="#818cf8" opacity=".22"/>'
            '<text x="100" y="280" fill="white" font-family="Arial,sans-serif" '
            'font-size="92" font-weight="700">FLASK / PYTHON</text>'
            '<text x="105" y="355" fill="#c7d2fe" font-family="Arial,sans-serif" '
            'font-size="38">Демо-курсы и отзывы</text></svg>',
            encoding='utf-8',
        )
        image = Image(
            id='demo-course-bg',
            file_name='demo-course-bg.svg',
            mime_type='image/svg+xml',
            md5_hash='demo-course-bg-hash',
        )
        db.session.add(image)

    db.session.flush()

    courses = {}
    for name, (short_desc, full_desc, author_login) in DEMO_COURSES.items():
        course = db.session.execute(
            db.select(Course).filter_by(name=name)
        ).scalar_one_or_none()
        if course is None:
            course = Course(
                name=name,
                short_desc=short_desc,
                full_desc=full_desc,
                category_id=category.id,
                author_id=users[author_login].id,
                background_image_id=image.id,
            )
            db.session.add(course)
        else:
            course.short_desc = short_desc
            course.full_desc = full_desc
        courses[name] = course

    db.session.flush()

    for course_name, login, rating, review_text in DEMO_REVIEWS:
        review = db.session.execute(
            db.select(Review).filter_by(
                course_id=courses[course_name].id,
                user_id=users[login].id,
            )
        ).scalar_one_or_none()
        if review is None:
            review = Review(
                course_id=courses[course_name].id,
                user_id=users[login].id,
                rating=rating,
                text=review_text,
            )
            db.session.add(review)
        else:
            review.rating = rating
            review.text = review_text

    db.session.flush()
    for course in courses.values():
        course_reviews = db.session.execute(
            db.select(Review).filter_by(course_id=course.id)
        ).scalars().all()
        course.rating_sum = sum(review.rating for review in course_reviews)
        course.rating_num = len(course_reviews)

    db.session.commit()

    print('Демо-данные созданы. Тестовые аккаунты:')
    for login, (_, _, password) in DEMO_USERS.items():
        print(f'  {login} / {password}')
    print('Курсы: Основы Flask, Python для начинающих, SQL и базы данных.')
