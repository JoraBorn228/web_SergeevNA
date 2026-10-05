"""Лабораторная работа №5.

Доработка CRUD-приложения (ЛР №4): ролевая авторизация (декоратор
``check_rights``), журнал посещений (``visit_logs`` + ``before_request``)
и статистические отчёты в отдельном Blueprint-модуле.
"""
import os
import sqlite3
from datetime import datetime

from flask import (
    Flask, render_template, redirect, url_for, request, flash, abort,
)
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user,
)
from werkzeug.security import check_password_hash

import db
import validation
import rights
import reports

# ─── Flask-Login ──────────────────────────────────────────────────────────────

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = rights.AUTH_REQUIRED_MESSAGE
login_manager.login_message_category = 'warning'


class User(UserMixin):
    """Модель пользователя для Flask-Login (данные из БД)."""

    def __init__(self, row):
        self.id = row['id']
        self.login = row['login']
        self.password_hash = row['password_hash']
        self.last_name = row['last_name']
        self.first_name = row['first_name']
        self.middle_name = row['middle_name']
        self.role_id = row['role_id']
        self.role_name = row['role_name'] if 'role_name' in row.keys() else None

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join(p for p in parts if p) or self.login


@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя из БД по идентификатору (для Flask-Login)."""
    row = db.get_user(user_id)
    return User(row) if row else None


# ─── Фабрика приложения ───────────────────────────────────────────────────────

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'lab5-super-secret-key-2025'),
        DATABASE=os.environ.get(
            'DATABASE',
            os.path.join(app.root_path, 'instance', 'lab5.sqlite'),
        ),
        REMEMBER_COOKIE_DURATION=2592000,  # 30 дней
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    register_template_helpers(app)
    register_routes(app)
    app.register_blueprint(reports.bp)

    # Инициализация схемы и начальных данных
    with app.app_context():
        db.init_db()

    return app


# ─── Шаблонные фильтры и контекст ─────────────────────────────────────────────

def register_template_helpers(app):

    @app.template_filter('dt')
    def format_datetime(value):
        """Форматирует дату БД (ГГГГ-ММ-ДД ЧЧ:ММ:СС) в ДД.ММ.ГГГГ ЧЧ:ММ:СС."""
        if not value:
            return ''
        try:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime(
                '%d.%m.%Y %H:%M:%S'
            )
        except (ValueError, TypeError):
            return value

    @app.context_processor
    def inject_rights():
        return {
            'has_right': lambda r: rights.user_has_right(current_user, r),
            'has_any_right': lambda *rs: rights.user_has_any_right(current_user, rs),
        }


# ─── Вспомогательные функции ──────────────────────────────────────────────────

def _form_values(form):
    """Извлекает данные формы в обычный словарь."""
    return {
        'login': (form.get('login') or '').strip(),
        'password': form.get('password') or '',
        'last_name': (form.get('last_name') or '').strip(),
        'first_name': (form.get('first_name') or '').strip(),
        'middle_name': (form.get('middle_name') or '').strip(),
        'role_id': form.get('role_id') or '',
    }


def _no_rights_redirect():
    flash(rights.NO_RIGHTS_MESSAGE, 'danger')
    return redirect(url_for('index'))


# ─── Маршруты ─────────────────────────────────────────────────────────────────

def register_routes(app):

    @app.before_request
    def log_page_visit():
        """Автоматически пишет посещения страниц в журнал (visit_logs)."""
        if request.endpoint in (None, 'static') or request.path.startswith('/static/'):
            return
        user_id = current_user.id if current_user.is_authenticated else None
        try:
            db.log_visit(request.path, user_id)
        except sqlite3.Error:
            # Журналирование не должно ломать основной запрос
            pass

    @app.route('/')
    def index():
        users = db.list_users()
        return render_template('index.html', title='Пользователи', users=users)

    @app.route('/users/<int:user_id>')
    @rights.check_rights(rights.RIGHT_VIEW_USER, rights.RIGHT_VIEW_OWN_PROFILE)
    def view_user(user_id):
        user = db.get_user(user_id)
        if user is None:
            abort(404)
        # Обычный пользователь может смотреть только свой профиль
        if not rights.user_has_right(current_user, rights.RIGHT_VIEW_USER) \
                and current_user.id != user_id:
            return _no_rights_redirect()
        return render_template('view.html', title='Просмотр пользователя', user=user)

    @app.route('/users/create', methods=['GET', 'POST'])
    @rights.check_rights(rights.RIGHT_CREATE_USER)
    def create_user():
        roles = db.list_roles()
        values = _form_values(request.form)

        if request.method == 'POST':
            errors = validation.validate_user_form(values, is_edit=False)

            if 'login' not in errors and db.get_user_by_login(values['login']):
                errors['login'] = 'Пользователь с таким логином уже существует'

            if errors:
                flash('Исправьте ошибки в форме.', 'danger')
                return render_template(
                    'create.html', title='Создание пользователя',
                    roles=roles, values=values, errors=errors,
                )

            try:
                db.create_user(
                    values['login'], values['password'],
                    values['last_name'], values['first_name'],
                    values['middle_name'], values['role_id'],
                )
            except sqlite3.Error as exc:
                flash(f'Ошибка при сохранении данных: {exc}', 'danger')
                return render_template(
                    'create.html', title='Создание пользователя',
                    roles=roles, values=values, errors={},
                )

            flash('Пользователь успешно создан.', 'success')
            return redirect(url_for('index'))

        return render_template(
            'create.html', title='Создание пользователя',
            roles=roles, values=values, errors={},
        )

    @app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @rights.check_rights(rights.RIGHT_EDIT_USER, rights.RIGHT_EDIT_OWN_PROFILE)
    def edit_user(user_id):
        user = db.get_user(user_id)
        if user is None:
            abort(404)

        # Администратор может редактировать любого, пользователь — только себя
        can_edit_all = rights.user_has_right(current_user, rights.RIGHT_EDIT_USER)
        if not can_edit_all and current_user.id != user_id:
            return _no_rights_redirect()
        is_own = not can_edit_all

        roles = db.list_roles()

        if request.method == 'POST':
            values = _form_values(request.form)
            # Обычный пользователь не может менять роль — сохраняем прежнюю
            if is_own:
                values['role_id'] = user['role_id'] or ''
            errors = validation.validate_user_form(values, is_edit=True)

            if errors:
                flash('Исправьте ошибки в форме.', 'danger')
                return render_template(
                    'edit.html', title='Редактирование пользователя',
                    roles=roles, values=values, errors=errors,
                    user=user, is_own=is_own,
                )

            try:
                db.update_user(
                    user_id, values['last_name'], values['first_name'],
                    values['middle_name'], values['role_id'],
                )
            except sqlite3.Error as exc:
                flash(f'Ошибка при сохранении данных: {exc}', 'danger')
                return render_template(
                    'edit.html', title='Редактирование пользователя',
                    roles=roles, values=values, errors={},
                    user=user, is_own=is_own,
                )

            flash('Данные пользователя успешно сохранены.', 'success')
            return redirect(url_for('index'))

        # GET — предзаполняем форму данными пользователя
        values = {
            'login': user['login'],
            'password': '',
            'last_name': user['last_name'] or '',
            'first_name': user['first_name'] or '',
            'middle_name': user['middle_name'] or '',
            'role_id': user['role_id'] or '',
        }
        return render_template(
            'edit.html', title='Редактирование пользователя',
            roles=roles, values=values, errors={}, user=user, is_own=is_own,
        )

    @app.route('/users/<int:user_id>/delete', methods=['POST'])
    @rights.check_rights(rights.RIGHT_DELETE_USER)
    def delete_user(user_id):
        user = db.get_user(user_id)
        if user is None:
            abort(404)
        try:
            db.delete_user(user_id)
        except sqlite3.Error as exc:
            flash(f'Ошибка при удалении пользователя: {exc}', 'danger')
            return redirect(url_for('index'))
        flash('Пользователь успешно удалён.', 'success')
        return redirect(url_for('index'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            login_value = (request.form.get('login') or '').strip()
            password = request.form.get('password') or ''
            remember = bool(request.form.get('remember'))

            row = db.get_user_by_login(login_value)
            if row and check_password_hash(row['password_hash'], password):
                login_user(User(row), remember=remember)
                flash('Вы успешно вошли в систему!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))

            flash('Неверный логин или пароль.', 'danger')

        return render_template('login.html', title='Вход')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Вы вышли из системы.', 'info')
        return redirect(url_for('index'))

    @app.route('/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        if request.method == 'POST':
            old_password = request.form.get('old_password') or ''
            new_password = request.form.get('new_password') or ''
            confirm_password = request.form.get('confirm_password') or ''

            errors = validation.validate_password_change(
                old_password, new_password, confirm_password
            )

            if 'old_password' not in errors:
                row = db.get_user_by_login(current_user.login)
                if not row or not check_password_hash(row['password_hash'], old_password):
                    errors['old_password'] = 'Неверный старый пароль'

            if errors:
                flash('Исправьте ошибки в форме.', 'danger')
                return render_template(
                    'change_password.html', title='Изменение пароля',
                    errors=errors,
                )

            db.update_password(current_user.id, new_password)
            flash('Пароль успешно изменён.', 'success')
            return redirect(url_for('index'))

        return render_template(
            'change_password.html', title='Изменение пароля', errors={}
        )


# Экземпляр для WSGI-сервера (gunicorn app:app)
app = create_app()
application = app


if __name__ == '__main__':
    app.run(debug=True)
