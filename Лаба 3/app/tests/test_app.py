"""
Тесты для Лабораторной работы №3:
- Счётчик посещений (session)
- Аутентификация (Flask-Login)
- Секретная страница (@login_required)
- Remember me
- Навбар (условные ссылки)
"""
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def get_navbar(html):
    """Возвращает HTML-фрагмент навбара (тег <nav>...</nav>)."""
    match = re.search(r'<nav.*?</nav>', html, re.DOTALL)
    assert match is not None, 'Навбар не найден на странице'
    return match.group(0)


def get_cookies(response):
    """Возвращает список заголовков Set-Cookie из ответа."""
    return response.headers.getlist('Set-Cookie')


# ═══════════════════════════════════════════════════════════════════
# 1-3. Счётчик посещений
# ═══════════════════════════════════════════════════════════════════

def test_counter_starts_at_one(client):
    """Первое посещение — счётчик равен 1."""
    response = client.get('/counter')
    assert response.status_code == 200
    assert b'1' in response.data


def test_counter_increments_on_each_visit(client):
    """Счётчик увеличивается с каждым посещением в рамках одной сессии."""
    client.get('/counter')
    client.get('/counter')
    response = client.get('/counter')
    assert b'3' in response.data


def test_counter_is_independent_per_session(app):
    """Разные клиенты (сессии) имеют независимые счётчики."""
    client1 = app.test_client()
    client2 = app.test_client()

    # Клиент 1 посещает 3 раза
    client1.get('/counter')
    client1.get('/counter')
    resp1 = client1.get('/counter')

    # Клиент 2 посещает 1 раз
    resp2 = client2.get('/counter')

    # У клиента 2 счётчик должен быть 1, не 4
    assert b'3' in resp1.data
    assert b'1' in resp2.data


# ═══════════════════════════════════════════════════════════════════
# 4-6. Успешная аутентификация
# ═══════════════════════════════════════════════════════════════════

def test_login_success_redirects_to_index(client):
    """После успешного входа пользователь перенаправляется на главную."""
    response = client.post(
        '/login',
        data={'username': 'user', 'password': 'qwerty'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert response.request.path == '/'


def test_login_success_shows_flash_message(client):
    """После успешного входа показывается сообщение об успехе."""
    response = client.post(
        '/login',
        data={'username': 'user', 'password': 'qwerty'},
        follow_redirects=True
    )
    assert 'успешно' in response.text.lower() or 'вошли' in response.text.lower()


def test_login_success_shows_username_in_navbar(client):
    """После входа в навбаре отображается имя пользователя."""
    response = client.post(
        '/login',
        data={'username': 'user', 'password': 'qwerty'},
        follow_redirects=True
    )
    assert b'user' in response.data


# ═══════════════════════════════════════════════════════════════════
# 7-8. Неудачная аутентификация
# ═══════════════════════════════════════════════════════════════════

def test_login_failure_stays_on_login_page(client):
    """При неверных данных пользователь остаётся на странице входа."""
    response = client.post(
        '/login',
        data={'username': 'user', 'password': 'wrong'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert response.request.path == '/login'


def test_login_failure_shows_error_message(client):
    """При неверных данных отображается сообщение об ошибке."""
    response = client.post(
        '/login',
        data={'username': 'user', 'password': 'wrong'},
        follow_redirects=True
    )
    assert 'неверный' in response.text.lower() or 'пароль' in response.text.lower()


# ═══════════════════════════════════════════════════════════════════
# 9. Секретная страница — аутентифицированный пользователь
# ═══════════════════════════════════════════════════════════════════

def test_secret_page_accessible_when_authenticated(auth_client):
    """Аутентифицированный пользователь получает доступ к секретной странице."""
    response = auth_client.get('/secret')
    assert response.status_code == 200
    assert 'секрет' in response.text.lower() or 'user' in response.text.lower()


# ═══════════════════════════════════════════════════════════════════
# 10-11. Секретная страница — анонимный пользователь
# ═══════════════════════════════════════════════════════════════════

def test_secret_page_redirects_anonymous_to_login(client):
    """Анонимный пользователь перенаправляется на страницу входа."""
    response = client.get('/secret')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_secret_page_anonymous_sees_auth_message(client):
    """Анонимному пользователю показывается сообщение о необходимости входа."""
    response = client.get('/secret', follow_redirects=True)
    assert response.status_code == 200
    assert 'аутентификац' in response.text.lower() or 'войд' in response.text.lower() or 'необходимо' in response.text.lower()


# ═══════════════════════════════════════════════════════════════════
# 12. Редирект на секретную страницу после входа
# ═══════════════════════════════════════════════════════════════════

def test_redirect_to_secret_after_login(client):
    """После входа (через /login?next=/secret) пользователь попадает на /secret."""
    response = client.post(
        '/login?next=/secret',
        data={'username': 'user', 'password': 'qwerty'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert response.request.path == '/secret'


# ═══════════════════════════════════════════════════════════════════
# 13. Remember me
# ═══════════════════════════════════════════════════════════════════

def test_remember_me_sets_token(client):
    """При чекбоксе 'Запомнить меня' устанавливается remember_token в cookie."""
    response = client.post(
        '/login',
        data={'username': 'user', 'password': 'qwerty', 'remember': 'on'},
    )
    cookies = get_cookies(response)
    assert any(c.startswith('remember_token=') for c in cookies)


def test_no_remember_token_without_checkbox(client):
    """Без чекбокса 'Запомнить меня' remember_token не устанавливается."""
    response = client.post(
        '/login',
        data={'username': 'user', 'password': 'qwerty'},
    )
    cookies = get_cookies(response)
    assert not any(c.startswith('remember_token=') for c in cookies)


def test_remember_me_token_has_expiration(client, app):
    """remember_token устанавливается с заданным сроком хранения (30 дней)."""
    response = client.post(
        '/login',
        data={'username': 'user', 'password': 'qwerty', 'remember': 'on'},
    )
    token_cookie = next(
        c for c in get_cookies(response) if c.startswith('remember_token=')
    )
    # Flask-Login проставляет Expires, соответствующий REMEMBER_COOKIE_DURATION
    expires_raw = re.search(r'Expires=([^;]+)', token_cookie).group(1)
    expires = parsedate_to_datetime(expires_raw)
    delta = expires - datetime.now(timezone.utc)
    expected_days = app.config['REMEMBER_COOKIE_DURATION'] / 86400  # секунды -> дни
    assert abs(delta.days - expected_days) <= 1


# ═══════════════════════════════════════════════════════════════════
# 14-15. Навбар — условные ссылки
# ═══════════════════════════════════════════════════════════════════

def test_navbar_hides_secret_link_for_anonymous(client):
    """Анонимный пользователь не видит ссылку на секретную страницу в навбаре."""
    navbar = get_navbar(client.get('/').text)
    assert '/secret' not in navbar
    assert 'Секретная страница' not in navbar


def test_navbar_shows_secret_link_for_authenticated(auth_client):
    """Аутентифицированный пользователь видит ссылку на секретную страницу."""
    navbar = get_navbar(auth_client.get('/').text)
    assert '/secret' in navbar
    assert 'Секретная страница' in navbar


def test_navbar_shows_login_link_for_anonymous(client):
    """Анонимному пользователю показывается ссылка 'Войти'."""
    navbar = get_navbar(client.get('/').text)
    assert '/login' in navbar
    assert 'Войти' in navbar


def test_navbar_shows_logout_for_authenticated(auth_client):
    """Аутентифицированному пользователю показывается ссылка 'Выйти'."""
    navbar = get_navbar(auth_client.get('/').text)
    assert '/logout' in navbar
    assert 'Выйти' in navbar


def test_navbar_shows_all_pages_for_authenticated(auth_client):
    """В навбаре аутентифицированного пользователя есть ссылки на все страницы."""
    navbar = get_navbar(auth_client.get('/').text)
    assert 'Главная' in navbar
    assert '/counter' in navbar
    assert '/secret' in navbar


def test_navbar_shows_all_public_pages_for_anonymous(client):
    """В навбаре анонимного пользователя есть ссылки на главную и счётчик."""
    navbar = get_navbar(client.get('/').text)
    assert '/counter' in navbar
    assert '/login' in navbar
