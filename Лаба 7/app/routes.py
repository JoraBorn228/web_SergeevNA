import csv
import hashlib
import io
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path

import bleach
import markdown
from dateutil.relativedelta import relativedelta
from flask import (Blueprint, abort, current_app, flash, make_response, redirect,
                   render_template, request, send_from_directory, session, url_for)
from flask_login import current_user, login_required
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app import db
from app.models import Book, BookView, Cover, Genre, Review, User
from app.permissions import roles_required

bp = Blueprint('main', __name__)
PAGE_SIZE = 10
ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS) | {
    'p', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'pre', 'code',
    'ul', 'ol', 'li', 'strong', 'em', 'del', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
}
ALLOWED_ATTRIBUTES = {'a': ['href', 'title'], 'th': ['align'], 'td': ['align']}


class RowsPagination:
    def __init__(self, query, page, per_page):
        self.page = page
        self.per_page = per_page
        self.total = query.count()
        self.pages = (self.total + per_page - 1) // per_page
        self.items = query.offset((page - 1) * per_page).limit(per_page).all()
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1
        self.next_num = page + 1

    def iter_pages(self):
        return range(1, self.pages + 1)


def clean_markdown_source(value):
    return bleach.clean(value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def markdown_html(value):
    rendered = markdown.markdown(value or '', extensions=['tables', 'fenced_code'])
    return bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def current_visitor_id():
    if current_user.is_authenticated:
        return None
    if 'visitor_id' not in session:
        session['visitor_id'] = str(uuid.uuid4())
    return session['visitor_id']


def record_book_view(book):
    now = datetime.utcnow()
    midnight = datetime.combine(now.date(), time.min)
    query = BookView.query.filter(BookView.book_id == book.id, BookView.viewed_at >= midnight)
    if current_user.is_authenticated:
        query = query.filter(BookView.user_id == current_user.id)
        user_id, visitor_id = current_user.id, None
    else:
        visitor_id = current_visitor_id()
        user_id = None
        query = query.filter(BookView.visitor_id == visitor_id)
    if query.count() < 10:
        db.session.add(BookView(book_id=book.id, user_id=user_id, visitor_id=visitor_id, viewed_at=now))
        db.session.commit()


def recent_books():
    query = BookView.query
    if current_user.is_authenticated:
        query = query.filter(BookView.user_id == current_user.id)
    else:
        visitor_id = session.get('visitor_id')
        if not visitor_id:
            return []
        query = query.filter(BookView.visitor_id == visitor_id)
    views = query.order_by(BookView.viewed_at.desc(), BookView.id.desc()).limit(100).all()
    books, seen = [], set()
    for view in views:
        if view.book_id not in seen:
            books.append(view.book)
            seen.add(view.book_id)
            if len(books) == 5:
                break
    return books


def filtered_view_stats():
    query = (db.session.query(Book, func.count(BookView.id).label('views'))
             .join(BookView, BookView.book_id == Book.id)
             .filter(BookView.user_id.isnot(None)))
    start_text = request.args.get('date_from', '')
    end_text = request.args.get('date_to', '')
    try:
        start_date = date.fromisoformat(start_text) if start_text else None
        end_date = date.fromisoformat(end_text) if end_text else None
        if start_text:
            query = query.filter(BookView.viewed_at >= datetime.combine(start_date, time.min))
        if end_text:
            query = query.filter(BookView.viewed_at < datetime.combine(end_date + timedelta(days=1), time.min))
    except ValueError:
        flash('Укажите даты в корректном формате.', 'warning')
        return query.group_by(Book.id).order_by(func.count(BookView.id).desc(), Book.title.asc()), '', ''
    return query.group_by(Book.id).order_by(func.count(BookView.id).desc(), Book.title.asc()), start_text, end_text


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Book.query.order_by(Book.year.desc(), Book.id.desc()).paginate(
        page=max(1, page), per_page=PAGE_SIZE, error_out=False
    )
    cutoff = datetime.utcnow() - relativedelta(months=3)
    popular_rows = (db.session.query(Book, func.count(BookView.id).label('views'))
                    .join(BookView, BookView.book_id == Book.id)
                    .filter(BookView.viewed_at >= cutoff)
                    .group_by(Book.id).order_by(func.count(BookView.id).desc(), Book.title.asc())
                    .limit(5).all())
    return render_template('index.html', pagination=pagination,
                           popular=[(book, count) for book, count in popular_rows],
                           recently_viewed=recent_books())


@bp.route('/books/<int:book_id>')
def book_detail(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        abort(404)
    record_book_view(book)
    own_review = None
    if current_user.is_authenticated:
        own_review = Review.query.filter_by(book_id=book.id, user_id=current_user.id).first()
    review_query = Review.query.filter_by(book_id=book.id)
    if not (current_user.is_authenticated and current_user.has_role('Администратор', 'Модератор')):
        review_query = review_query.filter_by(approved=True)
    reviews = review_query.order_by(Review.created_at.desc()).all()
    return render_template('book_detail.html', book=book, reviews=reviews,
                           own_review=own_review, description_html=markdown_html(book.description),
                           review_texts={review.id: markdown_html(review.text) for review in reviews})


@bp.route('/covers/<int:cover_id>')
def cover_file(cover_id):
    cover = db.session.get(Cover, cover_id)
    if cover is None or not cover.path.is_file():
        abort(404)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], cover.file_name,
                               mimetype=cover.mime_type)


def book_form_values():
    try:
        year = int(request.form.get('year', ''))
        page_count = int(request.form.get('page_count', ''))
    except (TypeError, ValueError):
        raise ValueError('Год и количество страниц должны быть целыми числами.')
    values = {
        'title': (request.form.get('title') or '').strip(),
        'short_description': (request.form.get('short_description') or '').strip(),
        'description': clean_markdown_source((request.form.get('description') or '').strip()),
        'year': year,
        'publisher': (request.form.get('publisher') or '').strip(),
        'author': (request.form.get('author') or '').strip(),
        'page_count': page_count,
    }
    if not all((values['title'], values['short_description'], values['description'],
                values['publisher'], values['author'])) or not (0 < year <= datetime.utcnow().year + 1) or page_count < 1:
        raise ValueError('Заполните все обязательные поля корректными значениями.')
    genre_ids = [int(value) for value in request.form.getlist('genre_ids') if value.isdigit()]
    if not genre_ids:
        raise ValueError('Выберите хотя бы один жанр.')
    values['genres'] = Genre.query.filter(Genre.id.in_(genre_ids)).all()
    if len(values['genres']) != len(set(genre_ids)):
        raise ValueError('Выбран неизвестный жанр.')
    return values


def upload_cover(book):
    upload = request.files.get('cover')
    if upload is None or not upload.filename:
        raise ValueError('Загрузите обложку книги.')
    raw = upload.read()
    mime_type = upload.mimetype or 'application/octet-stream'
    if not raw or mime_type not in {'image/jpeg', 'image/png', 'image/webp'}:
        raise ValueError('Поддерживаются изображения JPEG, PNG и WebP.')
    digest = hashlib.md5(raw).hexdigest()
    extension = Path(secure_filename(upload.filename)).suffix.lower()
    if extension not in {'.jpg', '.jpeg', '.png', '.webp'}:
        extension = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}[mime_type]
    file_name = f'{digest}{extension}'
    book.cover = Cover(file_name=file_name, mime_type=mime_type, md5_hash=digest)
    return raw, file_name


@bp.route('/books/new', methods=['GET', 'POST'])
@roles_required('Администратор')
def book_create():
    genres = Genre.query.order_by(Genre.name).all()
    if request.method == 'POST':
        try:
            values = book_form_values()
            book = Book(**{key: value for key, value in values.items() if key != 'genres'})
            book.genres = values['genres']
            db.session.add(book)
            db.session.flush()
            raw, file_name = upload_cover(book)
            db.session.commit()
            cover_path = Path(current_app.config['UPLOAD_FOLDER']) / file_name
            if not cover_path.exists():
                cover_path.write_bytes(raw)
            flash('Книга успешно добавлена.', 'success')
            return redirect(url_for('main.book_detail', book_id=book.id))
        except (ValueError, OSError) as error:
            db.session.rollback()
            flash(str(error) if isinstance(error, ValueError) else 'Не удалось сохранить обложку.', 'danger')
        except Exception:
            db.session.rollback()
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
    return render_template('book_form.html', book=None, genres=genres, mode='create')


@bp.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@roles_required('Администратор', 'Модератор')
def book_edit(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        abort(404)
    genres = Genre.query.order_by(Genre.name).all()
    if request.method == 'POST':
        try:
            values = book_form_values()
            for key, value in values.items():
                if key != 'genres':
                    setattr(book, key, value)
            book.genres = values['genres']
            db.session.commit()
            flash('Данные книги обновлены.', 'success')
            return redirect(url_for('main.book_detail', book_id=book.id))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), 'danger')
        except Exception:
            db.session.rollback()
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
    return render_template('book_form.html', book=book, genres=genres, mode='edit')


@bp.route('/books/<int:book_id>/delete', methods=['POST'])
@roles_required('Администратор')
def book_delete(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        abort(404)
    title = book.title
    old_cover = book.cover
    old_file = old_cover.file_name if old_cover else None
    db.session.delete(book)
    db.session.commit()
    if old_file and not Cover.query.filter_by(file_name=old_file).first():
        (Path(current_app.config['UPLOAD_FOLDER']) / old_file).unlink(missing_ok=True)
    flash(f'Книга «{title}» удалена.', 'success')
    return redirect(url_for('main.index'))


@bp.route('/books/<int:book_id>/reviews/new', methods=['GET', 'POST'])
@login_required
def review_create(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        abort(404)
    existing = Review.query.filter_by(book_id=book.id, user_id=current_user.id).first()
    if existing:
        flash('Вы уже оставляли рецензию на эту книгу.', 'info')
        return redirect(url_for('main.book_detail', book_id=book.id))
    if request.method == 'POST':
        try:
            rating = int(request.form.get('rating', ''))
        except (TypeError, ValueError):
            rating = -1
        text = clean_markdown_source((request.form.get('text') or '').strip())
        if rating not in range(6) or not text:
            flash('Выберите оценку от 0 до 5 и заполните текст рецензии.', 'danger')
        else:
            db.session.add(Review(book_id=book.id, user_id=current_user.id,
                                  rating=rating, text=text))
            db.session.commit()
            flash('Рецензия добавлена.', 'success')
            return redirect(url_for('main.book_detail', book_id=book.id))
    return render_template('review_form.html', book=book)


@bp.route('/reviews/<int:review_id>/moderate', methods=['POST'])
@roles_required('Администратор', 'Модератор')
def review_moderate(review_id):
    review = db.session.get(Review, review_id)
    if review is None:
        abort(404)
    review.approved = not review.approved
    book_id = review.book_id
    db.session.commit()
    flash('Статус рецензии изменён.', 'success')
    return redirect(url_for('main.book_detail', book_id=book_id))


@bp.route('/statistics')
@roles_required('Администратор')
def statistics():
    tab = request.args.get('tab', 'logs')
    page = max(1, request.args.get('page', 1, type=int))
    if tab == 'views':
        query, date_from, date_to = filtered_view_stats()
        pagination = RowsPagination(query, page, PAGE_SIZE)
    else:
        tab = 'logs'
        date_from = date_to = ''
        query = db.select(BookView).order_by(BookView.viewed_at.desc(), BookView.id.desc())
        pagination = db.paginate(query, page=page, per_page=PAGE_SIZE, error_out=False)
    return render_template('statistics.html', tab=tab, pagination=pagination,
                           date_from=date_from, date_to=date_to)


@bp.route('/statistics/logs.csv')
@roles_required('Администратор')
def export_logs():
    rows = db.session.execute(
        db.select(BookView).order_by(BookView.viewed_at.desc(), BookView.id.desc())
    ).scalars().all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['№', 'Пользователь', 'Книга', 'Дата и время'])
    for index, view in enumerate(rows, 1):
        writer.writerow([index, view.user.full_name if view.user else 'Неаутентифицированный пользователь',
                         view.book.title, view.viewed_at.strftime('%d.%m.%Y %H:%M:%S')])
    return csv_response(output.getvalue(), 'book_view_log')


@bp.route('/statistics/views.csv')
@roles_required('Администратор')
def export_view_stats():
    query, _, _ = filtered_view_stats()
    rows = query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['№', 'Книга', 'Количество просмотров'])
    for index, (book, count) in enumerate(rows, 1):
        writer.writerow([index, book.title, count])
    return csv_response(output.getvalue(), 'book_view_statistics')


def csv_response(content, prefix):
    response = make_response('\ufeff' + content)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = (
        f'attachment; filename={prefix}_{datetime.utcnow():%Y%m%d}.csv'
    )
    return response
