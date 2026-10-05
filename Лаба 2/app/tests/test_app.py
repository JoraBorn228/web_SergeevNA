import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import validate_phone


# ═══════════════════════════════════════════════════════════════
# 1-3. Страница "Параметры URL"
# ═══════════════════════════════════════════════════════════════

def test_url_params_returns_200(client):
    response = client.get('/url-params')
    assert response.status_code == 200

def test_url_params_shows_all_params(client):
    response = client.get('/url-params?name=Alice&age=25')
    assert b'name' in response.data
    assert b'Alice' in response.data
    assert b'age' in response.data
    assert b'25' in response.data

def test_url_params_shows_multiple_params(client):
    response = client.get('/url-params?a=1&b=2&c=3')
    assert b'a' in response.data
    assert b'b' in response.data
    assert b'c' in response.data

# ═══════════════════════════════════════════════════════════════
# 4-6. Страница "Заголовки запроса"
# ═══════════════════════════════════════════════════════════════

def test_headers_returns_200(client):
    response = client.get('/headers')
    assert response.status_code == 200

def test_headers_shows_header_names(client):
    response = client.get('/headers', headers={'X-Custom-Header': 'test-value'})
    assert b'X-Custom-Header' in response.data

def test_headers_shows_header_values(client):
    response = client.get('/headers', headers={'X-Custom-Header': 'my-unique-value'})
    assert b'my-unique-value' in response.data

# ═══════════════════════════════════════════════════════════════
# 7-9. Страница "Cookie"
# ═══════════════════════════════════════════════════════════════

def test_cookies_returns_200(client):
    response = client.get('/cookies')
    assert response.status_code == 200

def test_cookies_sets_cookie_when_absent(client):
    """При первом заходе (без cookie) должна устанавливаться cookie."""
    with client:
        response = client.get('/cookies')
        # Cookie устанавливается в заголовке Set-Cookie
        assert 'lab2_visited' in response.headers.get('Set-Cookie', '')

def test_cookies_deletes_cookie_when_present(client):
    """Если cookie уже установлена — при следующем запросе она удаляется."""
    client.set_cookie('lab2_visited', 'yes')
    response = client.get('/cookies')
    set_cookie = response.headers.get('Set-Cookie', '')
    # При удалении устанавливается Max-Age=0 или expires в прошлом
    assert 'lab2_visited' in set_cookie
    assert 'Max-Age=0' in set_cookie or 'Expires=' in set_cookie or 'expires=' in set_cookie

# ═══════════════════════════════════════════════════════════════
# 10-11. Страница "Параметры формы"
# ═══════════════════════════════════════════════════════════════

def test_form_params_get_returns_200(client):
    response = client.get('/form-params')
    assert response.status_code == 200

def test_form_params_post_shows_submitted_values(client):
    response = client.post('/form-params', data={
        'name': 'Никита',
        'email': 'nikita@example.com',
        'message': 'Привет, мир!'
    })
    assert b'\xd0\x9d\xd0\xb8\xd0\xba\xd0\xb8\xd1\x82\xd0\xb0' in response.data  # Никита in UTF-8
    assert b'nikita@example.com' in response.data

# ═══════════════════════════════════════════════════════════════
# 12-20. Валидация и форматирование телефона
# ═══════════════════════════════════════════════════════════════

def test_phone_get_returns_200(client):
    response = client.get('/phone')
    assert response.status_code == 200

@pytest.mark.parametrize("phone, expected_formatted", [
    ('+7 (123) 456-78-90', '8-123-456-78-90'),
    ('8(123)4567890',      '8-123-456-78-90'),
    ('123.456.78.90',      '8-123-456-78-90'),
    ('81234567890',        '8-123-456-78-90'),
    ('+71234567890',       '8-123-456-78-90'),
])
def test_phone_valid_formats(phone, expected_formatted):
    formatted, error = validate_phone(phone)
    assert error is None
    assert formatted == expected_formatted

def test_phone_invalid_characters():
    _, error = validate_phone('+7 (123) 456-78-9О')  # О — кириллица
    assert error == 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'

def test_phone_wrong_digit_count_too_few():
    _, error = validate_phone('12345')
    assert error == 'Недопустимый ввод. Неверное количество цифр.'

def test_phone_wrong_digit_count_too_many():
    _, error = validate_phone('123456789012')
    assert error == 'Недопустимый ввод. Неверное количество цифр.'

def test_phone_post_valid_shows_formatted(client):
    response = client.post('/phone', data={'phone': '+7 (123) 456-78-90'})
    assert response.status_code == 200
    assert b'8-123-456-78-90' in response.data

def test_phone_post_invalid_shows_error_message(client):
    response = client.post('/phone', data={'phone': '123'})
    assert b'\xd0\x9d\xd0\xb5\xd0\xb4\xd0\xbe\xd0\xbf\xd1\x83\xd1\x81\xd1\x82\xd0\xb8\xd0\xbc\xd1\x8b\xd0\xb9' in response.data  # Недопустимый

def test_phone_post_invalid_has_bootstrap_classes(client):
    response = client.post('/phone', data={'phone': '123'})
    assert b'is-invalid' in response.data
    assert b'invalid-feedback' in response.data

def test_phone_post_invalid_chars_error_message(client):
    response = client.post('/phone', data={'phone': '+7 (123) 456-78-9О'})
    assert b'is-invalid' in response.data
