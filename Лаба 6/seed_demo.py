"""Create a local demo account and course for the reviews feature."""
from pathlib import Path

from app import create_app
from app.models import Category, Course, Image, User, db


app = create_app()

with app.app_context():
    db.create_all()

    user = db.session.execute(db.select(User).filter_by(login='demo')).scalar_one_or_none()
    if user is None:
        user = User(first_name='Демо', last_name='Пользователь', login='demo')
        user.set_password('demo12345')
        db.session.add(user)

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
            'font-size="38">Демо-курс для проверки отзывов</text></svg>',
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
    course = db.session.execute(
        db.select(Course).filter_by(name='Основы Flask')
    ).scalar_one_or_none()
    if course is None:
        course = Course(
            name='Основы Flask',
            short_desc='Практический курс по созданию веб-приложений на Flask.',
            full_desc=(
                'Демонстрационный курс для просмотра реализации отзывов. '
                'Войдите под demo / demo12345, чтобы оставить отзыв и увидеть '
                'обновление рейтинга.'
            ),
            category_id=category.id,
            author_id=user.id,
            background_image_id=image.id,
        )
        db.session.add(course)

    db.session.commit()
    print('Демо-курс готов: /courses/1; логин demo, пароль demo12345.')
