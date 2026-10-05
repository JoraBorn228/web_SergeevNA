from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app.models import db
from app.repositories import CourseRepository, UserRepository, CategoryRepository, ImageRepository, ReviewRepository

user_repository = UserRepository(db)
course_repository = CourseRepository(db)
category_repository = CategoryRepository(db)
image_repository = ImageRepository(db)
review_repository = ReviewRepository(db)

bp = Blueprint('courses', __name__, url_prefix='/courses')

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]

def params():
    return { p: request.form.get(p) or None for p in COURSE_PARAMS }

def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }

@bp.route('/')
def index():
    pagination = course_repository.get_pagination_info(**search_params())
    courses = course_repository.get_all_courses(pagination=pagination)
    categories = category_repository.get_all_categories()
    return render_template('courses/index.html',
                           courses=courses,
                           categories=categories,
                           pagination=pagination,
                           search_params=search_params())

@bp.route('/new')
@login_required
def new():
    course = course_repository.new_course()
    categories = category_repository.get_all_categories()
    users = user_repository.get_all_users()
    return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course)

@bp.route('/create', methods=['POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = None

    try:
        if f and f.filename:
            img = image_repository.add_image(f)

        image_id = img.id if img else None
        course = course_repository.add_course(**params(), background_image_id=image_id)
    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        categories = category_repository.get_all_categories()
        users = user_repository.get_all_users()
        return render_template('courses/new.html',
                            categories=categories,
                            users=users,
                            course=course)

    flash(f'Курс {course.name} был успешно добавлен!', 'success')

    return redirect(url_for('courses.index'))

@bp.route('/<int:course_id>')
def show(course_id):
    course = course_repository.get_course_by_id(course_id)
    if course is None:
        abort(404)
    own_review = (review_repository.get_by_course_and_user(course_id, current_user.id)
                  if current_user.is_authenticated else None)
    recent_reviews = review_repository.get_last_five(course_id)
    return render_template('courses/show.html', course=course,
                           recent_reviews=recent_reviews, own_review=own_review)

@bp.route('/<int:course_id>/reviews', methods=['GET', 'POST'])
def reviews(course_id):
    course = course_repository.get_course_by_id(course_id)
    if course is None:
        abort(404)

    own_review = (review_repository.get_by_course_and_user(course_id, current_user.id)
                  if current_user.is_authenticated else None)
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.path))
        if own_review:
            flash('Вы уже оставили отзыв на этот курс.', 'warning')
            return redirect(url_for('courses.reviews', course_id=course_id))
        try:
            rating = int(request.form.get('rating', ''))
        except (TypeError, ValueError):
            rating = -1
        review_text = (request.form.get('text') or '').strip()
        if rating not in range(6) or not review_text:
            flash('Укажите оценку от 0 до 5 и заполните текст отзыва.', 'danger')
        else:
            review_repository.create(rating, review_text, course_id, current_user.id)
            flash('Отзыв успешно добавлен.', 'success')
            return redirect(url_for('courses.reviews', course_id=course_id))

    sort_order = request.args.get('sort', 'newest')
    if sort_order not in ('newest', 'positive', 'negative'):
        sort_order = 'newest'
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    pagination = review_repository.get_pagination_info(course_id, sort_order, page)
    return render_template('courses/reviews.html', course=course, own_review=own_review,
                           pagination=pagination, sort_order=sort_order)
