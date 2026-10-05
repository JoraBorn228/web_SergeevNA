"""Тесты для Лабораторной работы №5.

Проверяется:
  * отображение кнопок в зависимости от прав;
  * ролевая авторизация через декоратор check_rights;
  * просмотр / редактирование / удаление с учётом прав;
  * журнал посещений (before_request) и его фильтрация по пользователю;
  * пагинация журнала;
  * отчёты по страницам и пользователям и экспорт в CSV;
  * аутентификация из БД и смена пароля.
"""
import pytest

import db
import rights
from app import User

ADMIN_LOGIN = 'admin'
ADMIN_PASSWORD = 'Admin123'
USER_LOGIN = 'user'
USER_PASSWORD = 'User123'
NO_RIGHTS = 'недостаточно прав'


# ═══════════════════════════════════════════════════════════════════
# Отображение кнопок на главной странице
# ═══════════════════════════════════════════════════════════════════

def test_index_anonymous_hides_all_action_buttons(client):
    """Анонимный пользователь не видит кнопок действий и журнала."""
    html = client.get('/').text
    assert '<table' in html
    assert 'Создание пользователя' not in html
    assert 'Редактирование' not in html
    assert 'Удаление' not in html
    assert 'Просмотр' not in html
    assert 'Журнал посещений' not in html


def test_index_admin_sees_all_buttons(admin_client):
    """Администратор видит все кнопки действий и журнал."""
    html = admin_client.get('/').text
    assert 'Создание пользователя' in html
    assert 'Просмотр' in html
    assert 'Редактирование' in html
    assert 'Удаление' in html
    assert 'Журнал посещений' in html
    # Кнопки есть для каждого из двух пользователей (admin, user)
    assert html.count('Редактирование') == 2
    assert html.count('Просмотр') == 2


def test_index_user_sees_only_own_actions(user_client):
    """Обычный пользователь видит действия только для своей строки."""
    html = user_client.get('/').text
    assert 'Создание пользователя' not in html
    assert 'Удаление' not in html
    # Только своя запись: одна кнопка просмотра и одна — редактирования
    assert html.count('Просмотр') == 1
    assert html.count('Редактирование') == 1
    # Журнал доступен обычному пользователю
    assert 'Журнал посещений' in html


# ═══════════════════════════════════════════════════════════════════
# Декоратор check_rights: доступ к действиям
# ═══════════════════════════════════════════════════════════════════

def test_create_anonymous_redirects_to_login(client):
    """Аноним при попытке создания перенаправляется на вход."""
    response = client.get('/users/create')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_create_user_forbidden(user_client):
    """Обычный пользователь не имеет права создавать пользователей."""
    response = user_client.get('/users/create', follow_redirects=True)
    assert response.request.path == '/'
    assert NO_RIGHTS in response.text


def test_create_admin_allowed(admin_client, app):
    """Администратор успешно создаёт пользователя."""
    response = admin_client.post('/users/create', data={
        'login': 'newuser', 'password': 'Newpass1',
        'last_name': 'Сидоров', 'first_name': 'Сидор',
    }, follow_redirects=True)
    assert response.request.path == '/'
    assert 'успешно создан' in response.text.lower()
    with app.app_context():
        assert db.get_user_by_login('newuser') is not None


def test_delete_forbidden_for_user(user_client, app, add_user):
    """Обычный пользователь не может удалять пользователей."""
    victim_id = add_user(login='victim')
    response = user_client.post(
        f'/users/{victim_id}/delete', follow_redirects=True
    )
    assert response.request.path == '/'
    assert NO_RIGHTS in response.text
    with app.app_context():
        assert db.get_user(victim_id) is not None


def test_delete_allowed_for_admin(admin_client, app, add_user):
    """Администратор успешно удаляет пользователя."""
    victim_id = add_user(login='victim')
    response = admin_client.post(
        f'/users/{victim_id}/delete', follow_redirects=True
    )
    assert 'успешно удалён' in response.text.lower()
    with app.app_context():
        assert db.get_user(victim_id) is None


# ═══════════════════════════════════════════════════════════════════
# Просмотр профиля
# ═══════════════════════════════════════════════════════════════════

def test_view_anonymous_redirects_to_login(client, user_id):
    response = client.get(f'/users/{user_id}')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_view_own_profile_allowed(user_client, user_id):
    response = user_client.get(f'/users/{user_id}')
    assert response.status_code == 200
    assert 'user' in response.text


def test_view_other_profile_forbidden_for_user(user_client, admin_id):
    response = user_client.get(f'/users/{admin_id}', follow_redirects=True)
    assert response.request.path == '/'
    assert NO_RIGHTS in response.text


def test_view_any_profile_allowed_for_admin(admin_client, user_id):
    response = admin_client.get(f'/users/{user_id}')
    assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# Редактирование профиля
# ═══════════════════════════════════════════════════════════════════

def test_edit_own_profile_allowed(user_client, user_id):
    response = user_client.get(f'/users/{user_id}/edit')
    assert response.status_code == 200
    assert 'name="last_name"' in response.text
    # Поля логина и пароля отсутствуют
    assert 'name="login"' not in response.text
    assert 'name="password"' not in response.text


def test_edit_own_profile_role_disabled(user_client, user_id):
    """На форме редактирования своего профиля роль отключена."""
    html = user_client.get(f'/users/{user_id}/edit').text
    assert 'name="role_id"' in html
    assert 'disabled' in html


def test_edit_other_profile_forbidden_for_user(user_client, admin_id):
    response = user_client.get(f'/users/{admin_id}/edit', follow_redirects=True)
    assert response.request.path == '/'
    assert NO_RIGHTS in response.text


def test_edit_own_profile_saves_without_role_change(user_client, app, user_id):
    """Обычный пользователь меняет свои данные, роль остаётся прежней."""
    with app.app_context():
        role_before = db.get_user(user_id)['role_id']

    response = user_client.post(f'/users/{user_id}/edit', data={
        'last_name': 'Петров', 'first_name': 'Пётр', 'middle_name': 'Петрович',
        'role_id': '',  # попытка сбросить роль игнорируется
    }, follow_redirects=True)
    assert 'успешно сохранены' in response.text.lower()

    with app.app_context():
        updated = db.get_user(user_id)
        assert updated['last_name'] == 'Петров'
        assert updated['first_name'] == 'Пётр'
        assert updated['role_id'] == role_before


def test_edit_role_field_enabled_for_admin(admin_client, user_id):
    """Администратор видит поле роли доступным для изменения."""
    html = admin_client.get(f'/users/{user_id}/edit').text
    assert 'name="role_id"' in html
    assert 'Изменение роли недоступно' not in html


def test_edit_requires_login(client, user_id):
    response = client.get(f'/users/{user_id}/edit')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


# ═══════════════════════════════════════════════════════════════════
# Журнал посещений (before_request)
# ═══════════════════════════════════════════════════════════════════

def test_before_request_logs_anonymous_visit(app, client):
    client.get('/')
    with app.app_context():
        rows = [r for r in db.list_visits() if r['path'] == '/']
    assert rows
    assert rows[0]['user_id'] is None


def test_before_request_logs_authenticated_visit(app, admin_client, admin_id):
    admin_client.get('/')
    with app.app_context():
        rows = [r for r in db.list_visits()
                if r['path'] == '/' and r['user_id'] == admin_id]
    assert rows


def test_visits_page_anonymous_redirects_to_login(client):
    response = client.get('/visits/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_visits_page_admin_shows_all(admin_client):
    """Администратор видит в журнале и анонимные записи."""
    html = admin_client.get('/visits/').text
    assert '/login' in html
    assert 'Неаутентифицированный пользователь' in html


def test_visits_page_user_hides_others(user_client):
    """Обычный пользователь не видит чужие/анонимные записи."""
    html = user_client.get('/visits/').text
    # Запись о странице входа сделана анонимно и не должна отображаться
    assert '/login' not in html
    assert 'Неаутентифицированный пользователь' not in html
    assert 'Иванов' in html


def test_visits_pagination(admin_client, app):
    """Журнал разбивается на страницы."""
    with app.app_context():
        for i in range(15):
            db.log_visit(f'/page-{i}', None)

    page1 = admin_client.get('/visits/?page=1').text
    page2 = admin_client.get('/visits/?page=2').text
    assert 'page=2' in page1
    assert 'Страница 1 из 2' in page1
    assert 'Страница 2 из 2' in page2


# ═══════════════════════════════════════════════════════════════════
# Отчёты (уровень БД)
# ═══════════════════════════════════════════════════════════════════

def test_report_by_pages_counts_and_order(app):
    with app.app_context():
        db.log_visit('/a', None)
        db.log_visit('/a', None)
        db.log_visit('/b', None)
        rows = db.report_by_pages()
        counts = {r['path']: r['cnt'] for r in rows}
    assert counts['/a'] == 2
    assert counts['/b'] == 1
    assert rows[0]['path'] == '/a'


def test_report_by_users_counts(app, admin_id):
    with app.app_context():
        db.log_visit('/x', admin_id)
        db.log_visit('/x', admin_id)
        db.log_visit('/y', None)
        rows = db.report_by_users()
        by_user = {r['user_id']: r['cnt'] for r in rows}
    assert by_user[admin_id] == 2
    assert by_user[None] == 1


# ═══════════════════════════════════════════════════════════════════
# Страницы отчётов и права на них
# ═══════════════════════════════════════════════════════════════════

def test_report_pages_forbidden_for_user(user_client):
    response = user_client.get('/visits/pages', follow_redirects=True)
    assert response.request.path == '/'
    assert NO_RIGHTS in response.text


def test_report_users_forbidden_for_user(user_client):
    response = user_client.get('/visits/users', follow_redirects=True)
    assert response.request.path == '/'
    assert NO_RIGHTS in response.text


def test_report_pages_page_for_admin(admin_client, app):
    with app.app_context():
        db.log_visit('/a', None)
    response = admin_client.get('/visits/pages')
    assert response.status_code == 200
    assert 'Количество посещений' in response.text
    assert '/a' in response.text
    assert 'Экспорт в CSV' in response.text


def test_report_users_page_for_admin(admin_client, app):
    with app.app_context():
        db.log_visit('/a', None)
    response = admin_client.get('/visits/users')
    assert response.status_code == 200
    assert 'Неаутентифицированный пользователь' in response.text


# ═══════════════════════════════════════════════════════════════════
# Экспорт в CSV
# ═══════════════════════════════════════════════════════════════════

def test_export_pages_csv(admin_client, app):
    with app.app_context():
        db.log_visit('/a', None)
        db.log_visit('/a', None)
    response = admin_client.get('/visits/pages/export')
    assert response.status_code == 200
    assert 'text/csv' in response.headers['Content-Type']
    assert 'attachment' in response.headers['Content-Disposition']
    body = response.data.decode('utf-8-sig')
    assert 'Страница' in body
    assert 'Количество посещений' in body
    assert '/a' in body


def test_export_users_csv(admin_client, app):
    with app.app_context():
        db.log_visit('/a', None)
    response = admin_client.get('/visits/users/export')
    assert response.status_code == 200
    assert 'text/csv' in response.headers['Content-Type']
    body = response.data.decode('utf-8-sig')
    assert 'Пользователь' in body
    assert 'Неаутентифицированный пользователь' in body


def test_export_forbidden_for_user(user_client):
    response = user_client.get('/visits/pages/export', follow_redirects=True)
    assert response.request.path == '/'
    assert NO_RIGHTS in response.text


# ═══════════════════════════════════════════════════════════════════
# Модуль прав (unit-тесты)
# ═══════════════════════════════════════════════════════════════════

def test_rights_admin(app):
    with app.app_context():
        admin = User(db.get_user_by_login(ADMIN_LOGIN))
    assert rights.user_has_right(admin, rights.RIGHT_CREATE_USER)
    assert rights.user_has_right(admin, rights.RIGHT_DELETE_USER)
    assert rights.user_has_right(admin, rights.RIGHT_VIEW_VISITS_ALL)
    assert not rights.user_has_right(admin, rights.RIGHT_EDIT_OWN_PROFILE)


def test_rights_user(app):
    with app.app_context():
        user = User(db.get_user_by_login(USER_LOGIN))
    assert rights.user_has_right(user, rights.RIGHT_EDIT_OWN_PROFILE)
    assert rights.user_has_right(user, rights.RIGHT_VIEW_OWN_PROFILE)
    assert rights.user_has_right(user, rights.RIGHT_VIEW_VISITS_OWN)
    assert not rights.user_has_right(user, rights.RIGHT_CREATE_USER)
    assert not rights.user_has_right(user, rights.RIGHT_VIEW_VISITS_ALL)


def test_rights_anonymous():
    assert rights.get_user_rights(None) == set()


# ═══════════════════════════════════════════════════════════════════
# Аутентификация и смена пароля
# ═══════════════════════════════════════════════════════════════════

def test_login_user_from_db(client):
    response = client.post('/login', data={
        'login': USER_LOGIN, 'password': USER_PASSWORD,
    }, follow_redirects=True)
    assert response.request.path == '/'
    assert 'успешно вошли' in response.text.lower()


def test_login_failure(client):
    response = client.post('/login', data={
        'login': USER_LOGIN, 'password': 'wrong',
    }, follow_redirects=True)
    assert response.request.path == '/login'
    assert 'неверный логин или пароль' in response.text.lower()


def test_change_password_success(user_client, app):
    response = user_client.post('/change-password', data={
        'old_password': USER_PASSWORD,
        'new_password': 'Newsecret1',
        'confirm_password': 'Newsecret1',
    }, follow_redirects=True)
    assert response.request.path == '/'
    assert 'пароль успешно изменён' in response.text.lower()

    fresh = app.test_client()
    login = fresh.post('/login', data={
        'login': USER_LOGIN, 'password': 'Newsecret1',
    }, follow_redirects=True)
    assert login.request.path == '/'


def test_change_password_wrong_old(user_client):
    response = user_client.post('/change-password', data={
        'old_password': 'WrongOld1',
        'new_password': 'Newsecret1',
        'confirm_password': 'Newsecret1',
    })
    assert 'Неверный старый пароль' in response.text


def test_change_password_mismatch(user_client):
    response = user_client.post('/change-password', data={
        'old_password': USER_PASSWORD,
        'new_password': 'Newsecret1',
        'confirm_password': 'Different1',
    })
    assert 'Пароли не совпадают' in response.text
