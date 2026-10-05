"""Initialize an example library with users, books, reviews, and view history."""
from datetime import datetime, timedelta
from pathlib import Path

from app import create_app, db
from app.models import Book, BookView, Cover, Genre, Review, Role, User


ROLE_DATA = {
    'Администратор': 'Полный доступ, включая управление каталогом и статистикой.',
    'Модератор': 'Редактирование книг и модерация рецензий.',
    'Пользователь': 'Просмотр каталога и публикация рецензий.',
}
USER_DATA = [
    ('admin', 'Admin123', 'Сергеев', 'Никита', 'Андреевич', 'Администратор'),
    ('moderator', 'Mod12345', 'Иванова', 'Анна', 'Петровна', 'Модератор'),
    ('reader', 'User123', 'Смирнов', 'Илья', 'Олегович', 'Пользователь'),
    ('reader2', 'User234', 'Кузнецова', 'Мария', 'Игоревна', 'Пользователь'),
]
GENRE_NAMES = ['Фантастика', 'Роман', 'Детектив', 'Научная литература', 'Программирование', 'Классика']
BOOK_DATA = [
    ('Мастер и Маргарита', 'Михаил Булгаков', 1967, 'Эксмо', 480, ['Роман', 'Классика']),
    ('Пикник на обочине', 'Аркадий и Борис Стругацкие', 1972, 'АСТ', 256, ['Фантастика']),
    ('Преступление и наказание', 'Фёдор Достоевский', 1866, 'Азбука', 672, ['Роман', 'Классика']),
    ('Убийство в Восточном экспрессе', 'Агата Кристи', 1934, 'Эксмо', 320, ['Детектив']),
    ('Дюна', 'Фрэнк Герберт', 1965, 'АСТ', 704, ['Фантастика']),
    ('Чистый код', 'Роберт Мартин', 2008, 'Питер', 464, ['Программирование']),
    ('Цветы для Элджернона', 'Дэниел Киз', 1966, 'Эксмо', 320, ['Фантастика', 'Роман']),
    ('Краткая история времени', 'Стивен Хокинг', 1988, 'Амфора', 256, ['Научная литература']),
    ('1984', 'Джордж Оруэлл', 1949, 'АСТ', 320, ['Фантастика', 'Классика']),
    ('Введение в алгоритмы', 'Томас Кормен', 1990, 'Вильямс', 1296, ['Научная литература', 'Программирование']),
    ('Шерлок Холмс: Собака Баскервилей', 'Артур Конан Дойл', 1902, 'Азбука', 288, ['Детектив', 'Классика']),
    ('Маленький принц', 'Антуан де Сент-Экзюпери', 1943, 'Эксмо', 128, ['Роман', 'Классика']),
]
REVIEW_DATA = [
    (0, 'reader', 5, 'Сильная книга, к которой хочется возвращаться.'),
    (0, 'reader2', 4, 'Очень понравился язык и атмосфера.'),
    (1, 'reader', 5, 'Одна из лучших историй Стругацких.'),
    (1, 'reader2', 4, 'Интересная фантастика с неоднозначным финалом.'),
    (2, 'reader', 5, 'Классика, которая читается на одном дыхании.'),
    (3, 'reader2', 5, 'Захватывающий детектив, разгадка удивила.'),
    (4, 'reader', 4, 'Большой и подробный мир, рекомендую.'),
    (5, 'reader2', 5, 'Практичная книга для разработчика.'),
    (6, 'reader', 4, 'Эмоциональная и необычная история.'),
    (7, 'reader2', 4, 'Хорошее введение в сложные идеи.'),
    (8, 'reader', 5, 'Важная книга, которая не теряет актуальности.'),
    (9, 'reader2', 3, 'Полезный справочник, но требует внимательного чтения.'),
    (10, 'reader', 5, 'Отличный классический детектив.'),
    (11, 'reader2', 5, 'Небольшая книга с большим смыслом.'),
]


def make_cover_svg(title, destination):
    safe_title = (title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))[:30]
    destination.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="680">'
        '<defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#172554"/>'
        '<stop offset="1" stop-color="#7c3aed"/></linearGradient></defs>'
        '<rect width="480" height="680" fill="url(#g)"/>'
        '<circle cx="390" cy="130" r="170" fill="#fff" opacity=".08"/>'
        f'<text x="40" y="340" fill="white" font-family="Georgia,serif" '
        f'font-size="32">{safe_title}</text>'
        '<text x="40" y="620" fill="#ddd6fe" font-family="Arial,sans-serif" '
        'font-size="18">ЭЛЕКТРОННАЯ БИБЛИОТЕКА</text></svg>',
        encoding='utf-8',
    )


app = create_app()
with app.app_context():
    db.create_all()
    roles = {}
    for name, description in ROLE_DATA.items():
        role = Role.query.filter_by(name=name).first()
        if role is None:
            role = Role(name=name, description=description)
            db.session.add(role)
        roles[name] = role
    db.session.flush()

    users = {}
    for login, password, last, first, middle, role_name in USER_DATA:
        user = User.query.filter_by(login=login).first()
        if user is None:
            user = User(login=login, last_name=last, first_name=first,
                        middle_name=middle, role=roles[role_name])
            user.set_password(password)
            db.session.add(user)
        else:
            user.last_name, user.first_name, user.middle_name = last, first, middle
            user.role = roles[role_name]
        users[login] = user

    genres = {}
    for name in GENRE_NAMES:
        genre = Genre.query.filter_by(name=name).first()
        if genre is None:
            genre = Genre(name=name)
            db.session.add(genre)
        genres[name] = genre

    db.session.flush()
    books = []
    cover_dir = Path(app.config['UPLOAD_FOLDER'])
    cover_dir.mkdir(parents=True, exist_ok=True)
    for index, (title, author, year, publisher, page_count, genre_names) in enumerate(BOOK_DATA):
        book = Book.query.filter_by(title=title).first()
        if book is None:
            book = Book(title=title, short_description=f'Книга «{title}» — {author}.',
                        description=f'## О книге\n\nКнига **«{title}»** написана автором {author}.\n\nДемо-описание для каталога библиотеки.',
                        year=year, publisher=publisher, author=author, page_count=page_count)
            db.session.add(book)
        else:
            book.author, book.year, book.publisher, book.page_count = author, year, publisher, page_count
        book.genres = [genres[name] for name in genre_names]
        db.session.flush()
        if book.cover is None:
            cover_name = f'demo-book-{book.id}.svg'
            cover_path = cover_dir / cover_name
            if not cover_path.exists():
                make_cover_svg(title, cover_path)
            book.cover = Cover(file_name=cover_name, mime_type='image/svg+xml',
                               md5_hash=f'demo-cover-{book.id}', book_id=book.id)
        books.append(book)

    db.session.flush()
    for book_index, login, rating, text in REVIEW_DATA:
        book, user = books[book_index], users[login]
        review = Review.query.filter_by(book_id=book.id, user_id=user.id).first()
        if review is None:
            review = Review(book=book, user=user, rating=rating, text=text, approved=True)
            db.session.add(review)
        else:
            review.rating, review.text, review.approved = rating, text, True

    db.session.flush()
    # Seed realistic, recent visit history. Re-running this script does not add duplicate demo rows.
    today = datetime.utcnow().date()
    for index, (book, visits) in enumerate(zip(books[:5], [15, 12, 9, 7, 5])):
        for offset in range(visits):
            viewed_at = datetime.combine(
                today - timedelta(days=(index * 3 + offset)),
                datetime.min.time().replace(hour=9 + offset % 8, minute=offset % 60),
            )
            existing = BookView.query.filter_by(book_id=book.id, user_id=users['reader'].id).filter(
                BookView.viewed_at == viewed_at
            ).first()
            if existing is None:
                db.session.add(BookView(book=book, user=users['reader'], viewed_at=viewed_at))
    recent_visitor = 'demo-anonymous-browser'
    for book in books[5:8]:
        if not BookView.query.filter_by(book_id=book.id, visitor_id=recent_visitor).first():
            db.session.add(BookView(book=book, visitor_id=recent_visitor,
                                    viewed_at=datetime.utcnow() - timedelta(minutes=book.id)))

    db.session.commit()
    print('Тестовые аккаунты:')
    for login, password, *_rest in USER_DATA:
        print(f'  {login} / {password}')
    print(f'Создано демо-книг: {len(books)}, жанров: {len(genres)}, рецензий: {len(REVIEW_DATA)}.')
