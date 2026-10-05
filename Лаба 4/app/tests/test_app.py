"""Тесты для Лабораторной работы №4.

Проверяется:
  * список пользователей и условный вывод кнопок;
  * просмотр записи;
  * создание записи (доступ, валидация, успех, ошибки БД);
  * редактирование записи (доступ, предзаполнение, успех, валидация);
  * удаление записи (доступ, модальное окно, успех);
  * аутентификация (загрузка из БД, успех/ошибка);
  * смена пароля;
  * серверная валидация логина и пароля.
"""
import pytest

import validation

ADMIN_LOGIN = 'admin'
ADMIN_PASSWORD = 'Admin123'


# ═══════════════════════════════════════════════════════════════════
# Список пользователей (главная страница)
# ═══════════════════════════════════════════════════════════════════

def test_index_shows_users_table(client):
    """Главная страница отображает таблицу пользователей."""
    response = client.get('/')
    assert response.status_code == 200
    assert '<table' in response.text
    assert 'ФИО' in response.text
    assert 'Роль' in response.text
    assert 'Действия' in response.text


def test_index_anonymous_hides_actions_and_create(client):
    """Анонимный пользователь не видит кнопки редактирования/удаления/создания."""
    html = client.get('/').text
    assert 'Редактирование' not in html
    assert 'Удаление' not in html
    assert 'Создание пользователя' not in html
    assert 'deleteModal' not in html
    # Просмотр доступен всем
    assert 'Просмотр' in html


def test_index_authenticated_shows_actions(auth_client):
    """Аутентифицированный пользователь видит все действия и кнопку создания."""
    html = auth_client.get('/').text
    assert 'Редактирование' in html
    assert 'Удаление' in html
    assert 'Создание пользователя' in html
    assert 'data-bs-target="#deleteModal"' in html


# ═══════════════════════════════════════════════════════════════════
# Просмотр записи
# ═══════════════════════════════════════════════════════════════════

def test_view_user_accessible_anonymous(client, add_user):
    """Просмотр записи доступен без аутентификации."""
    user_id = add_user(login='viewme', last_name='Петров', first_name='Пётр')
    response = client.get(f'/users/{user_id}')
    assert response.status_code == 200
    assert 'viewme' in response.text
    assert 'Петров' in response.text
    assert 'Пётр' in response.text


def test_view_user_not_found(client):
    """Просмотр несуществующего пользователя возвращает 404."""
    assert client.get('/users/9999').status_code == 404


# ═══════════════════════════════════════════════════════════════════
# Создание записи
# ═══════════════════════════════════════════════════════════════════

def test_create_requires_login(client):
    """Анонимный пользователь перенаправляется со страницы создания на вход."""
    response = client.get('/users/create')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_create_post_requires_login(client):
    """POST на создание без аутентификации не создаёт запись."""
    response = client.post('/users/create', data={
        'login': 'hacker', 'password': 'Hacker123',
        'last_name': 'Хак', 'first_name': 'Хакер',
    })
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_create_user_success(auth_client, app):
    """Успешное создание пользователя: редирект и flash-сообщение."""
    response = auth_client.post('/users/create', data={
        'login': 'newuser', 'password': 'Newpass1',
        'last_name': 'Сидоров', 'first_name': 'Сидор', 'middle_name': 'Сидорович',
        'role_id': '',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == '/'
    assert 'успешно создан' in response.text.lower()

    # Запись действительно в БД
    with app.app_context():
        import db
        assert db.get_user_by_login('newuser') is not None


def test_create_user_empty_fields(auth_client):
    """Пустые обязательные поля подсвечиваются и содержат пояснения."""
    response = auth_client.post('/users/create', data={
        'login': '', 'password': '', 'last_name': '', 'first_name': '',
    })
    assert response.status_code == 200
    assert 'is-invalid' in response.text
    assert 'Поле не может быть пустым' in response.text


def test_create_user_invalid_login(auth_client):
    """Логин с недопустимыми символами отклоняется."""
    response = auth_client.post('/users/create', data={
        'login': 'Логин', 'password': 'Newpass1',
        'last_name': 'Иванов', 'first_name': 'Иван',
    })
    assert response.status_code == 200
    assert 'is-invalid' in response.text
    assert 'латинские буквы' in response.text


def test_create_user_short_login(auth_client):
    """Слишком короткий логин отклоняется."""
    response = auth_client.post('/users/create', data={
        'login': 'abc', 'password': 'Newpass1',
        'last_name': 'Иванов', 'first_name': 'Иван',
    })
    assert 'не менее 5 символов' in response.text


def test_create_user_weak_password(auth_client):
    """Слабый пароль отклоняется с пояснением."""
    response = auth_client.post('/users/create', data={
        'login': 'newuser', 'password': 'weak',
        'last_name': 'Иванов', 'first_name': 'Иван',
    })
    assert response.status_code == 200
    assert 'is-invalid' in response.text
    assert 'не менее 8 символов' in response.text


def test_create_duplicate_login(auth_client):
    """Повторяющийся логин отклоняется."""
    response = auth_client.post('/users/create', data={
        'login': ADMIN_LOGIN, 'password': 'Newpass1',
        'last_name': 'Иванов', 'first_name': 'Иван',
    })
    assert response.status_code == 200
    assert 'уже существует' in response.text


def test_create_keeps_form_values_on_error(auth_client):
    """При ошибке форма сохраняет введённые пользователем данные."""
    response = auth_client.post('/users/create', data={
        'login': 'ab', 'password': 'weak',
        'last_name': 'Сохранённая', 'first_name': 'Имя',
    })
    assert 'Сохранённая' in response.text
    assert 'value="ab"' in response.text


# ═══════════════════════════════════════════════════════════════════
# Редактирование записи
# ═══════════════════════════════════════════════════════════════════

def test_edit_requires_login(client, add_user):
    """Анонимный пользователь перенаправляется со страницы редактирования."""
    user_id = add_user()
    response = client.get(f'/users/{user_id}/edit')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_edit_form_prefilled_without_login_password(auth_client, add_user):
    """Форма редактирования заполнена данными и не содержит полей логина/пароля."""
    user_id = add_user(login='editme', last_name='Смирнов', first_name='Олег')
    html = auth_client.get(f'/users/{user_id}/edit').text
    assert 'Смирнов' in html
    assert 'Олег' in html
    # Полей логина и пароля быть не должно
    assert 'name="login"' not in html
    assert 'name="password"' not in html
    # Остальные поля формы присутствуют
    assert 'name="last_name"' in html
    assert 'name="first_name"' in html
    assert 'name="role_id"' in html


def test_edit_user_success(auth_client, app, add_user):
    """Успешное редактирование: редирект, flash, обновление в БД."""
    user_id = add_user(login='editme', last_name='Старый', first_name='Имя')
    response = auth_client.post(f'/users/{user_id}/edit', data={
        'last_name': 'Новый', 'first_name': 'Имя2', 'middle_name': 'Отчество',
        'role_id': '',
    }, follow_redirects=True)
    assert response.request.path == '/'
    assert 'успешно сохранены' in response.text.lower()

    with app.app_context():
        import db
        updated = db.get_user(user_id)
        assert updated['last_name'] == 'Новый'
        assert updated['first_name'] == 'Имя2'


def test_edit_validation_errors(auth_client, add_user):
    """Пустые обязательные поля при редактировании подсвечиваются."""
    user_id = add_user()
    response = auth_client.post(f'/users/{user_id}/edit', data={
        'last_name': '', 'first_name': '', 'middle_name': '', 'role_id': '',
    })
    assert response.status_code == 200
    assert 'is-invalid' in response.text
    assert 'Поле не может быть пустым' in response.text


# ═══════════════════════════════════════════════════════════════════
# Удаление записи
# ═══════════════════════════════════════════════════════════════════

def test_delete_requires_login(client, add_user, app):
    """Анонимный пользователь не может удалить запись."""
    user_id = add_user(login='deleteme')
    response = client.post(f'/users/{user_id}/delete')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']
    with app.app_context():
        import db
        assert db.get_user(user_id) is not None


def test_delete_user_success(auth_client, app, add_user):
    """Успешное удаление: редирект, flash, запись удалена из БД."""
    user_id = add_user(login='deleteme', last_name='Удаляемый')
    response = auth_client.post(
        f'/users/{user_id}/delete', follow_redirects=True
    )
    assert response.request.path == '/'
    assert 'успешно удалён' in response.text.lower()
    with app.app_context():
        import db
        assert db.get_user(user_id) is None


def test_delete_modal_message_present(auth_client, add_user):
    """На главной есть модальное окно с текстом подтверждения удаления."""
    add_user(login='deleteme', last_name='Удаляемый', first_name='Иван')
    html = auth_client.get('/').text
    assert 'Вы уверены, что хотите удалить пользователя' in html
    assert 'deleteModal' in html
    assert '>Да<' in html
    assert '>Нет<' in html


# ═══════════════════════════════════════════════════════════════════
# Аутентификация
# ═══════════════════════════════════════════════════════════════════

def test_login_success(client):
    """Успешный вход перенаправляет на главную с сообщением."""
    response = client.post('/login', data={
        'login': ADMIN_LOGIN, 'password': ADMIN_PASSWORD,
    }, follow_redirects=True)
    assert response.request.path == '/'
    assert 'успешно вошли' in response.text.lower()


def test_login_failure_stays_on_login(client):
    """Неудачный вход оставляет на странице входа с сообщением об ошибке."""
    response = client.post('/login', data={
        'login': ADMIN_LOGIN, 'password': 'wrong',
    }, follow_redirects=True)
    assert response.request.path == '/login'
    assert 'неверный логин или пароль' in response.text.lower()


def test_login_loads_user_from_db(client, add_user):
    """Аутентификация использует данные пользователя из БД."""
    add_user(login='dbuser', password='Dbpass123', last_name='БД', first_name='Юзер')
    response = client.post('/login', data={
        'login': 'dbuser', 'password': 'Dbpass123',
    }, follow_redirects=True)
    assert response.request.path == '/'
    assert 'БД' in response.text


def test_login_redirects_to_requested_page(client):
    """После входа аноним возвращается на запрошенную страницу."""
    response = client.post('/login?next=/users/create', data={
        'login': ADMIN_LOGIN, 'password': ADMIN_PASSWORD,
    }, follow_redirects=True)
    assert response.request.path == '/users/create'


# ═══════════════════════════════════════════════════════════════════
# Смена пароля
# ═══════════════════════════════════════════════════════════════════

def test_change_password_requires_login(client):
    """Смена пароля доступна только аутентифицированным пользователям."""
    response = client.get('/change-password')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_change_password_success(auth_client, app):
    """Успешная смена пароля: редирект, flash, новый пароль работает."""
    response = auth_client.post('/change-password', data={
        'old_password': ADMIN_PASSWORD,
        'new_password': 'Newsecret1',
        'confirm_password': 'Newsecret1',
    }, follow_redirects=True)
    assert response.request.path == '/'
    assert 'пароль успешно изменён' in response.text.lower()

    # Вход с новым паролем
    fresh = app.test_client()
    login = fresh.post('/login', data={
        'login': ADMIN_LOGIN, 'password': 'Newsecret1',
    }, follow_redirects=True)
    assert login.request.path == '/'


def test_change_password_wrong_old(auth_client):
    """Неверный старый пароль отклоняется."""
    response = auth_client.post('/change-password', data={
        'old_password': 'WrongOld1',
        'new_password': 'Newsecret1',
        'confirm_password': 'Newsecret1',
    })
    assert response.status_code == 200
    assert 'Неверный старый пароль' in response.text
    assert 'is-invalid' in response.text


def test_change_password_mismatch(auth_client):
    """Несовпадающие новый пароль и подтверждение отклоняются."""
    response = auth_client.post('/change-password', data={
        'old_password': ADMIN_PASSWORD,
        'new_password': 'Newsecret1',
        'confirm_password': 'Different1',
    })
    assert response.status_code == 200
    assert 'Пароли не совпадают' in response.text


def test_change_password_weak_new(auth_client):
    """Слабый новый пароль отклоняется."""
    response = auth_client.post('/change-password', data={
        'old_password': ADMIN_PASSWORD,
        'new_password': 'weak',
        'confirm_password': 'weak',
    })
    assert response.status_code == 200
    assert 'не менее 8 символов' in response.text


# ═══════════════════════════════════════════════════════════════════
# Общий макрос формы
# ═══════════════════════════════════════════════════════════════════

def test_form_macro_used_on_create_and_edit(auth_client, add_user):
    """Одна и та же форма-макрос используется на создании и редактировании."""
    user_id = add_user()
    create_html = auth_client.get('/users/create').text
    edit_html = auth_client.get(f'/users/{user_id}/edit').text

    for field in ('name="last_name"', 'name="first_name"',
                  'name="middle_name"', 'name="role_id"'):
        assert field in create_html
        assert field in edit_html


# ═══════════════════════════════════════════════════════════════════
# Серверная валидация (unit-тесты)
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.parametrize('login, valid', [
    ('admin', True),
    ('user123', True),
    ('abc', False),          # короткий
    ('юзер', False),         # кириллица
    ('user_1', False),       # подчёркивание
    ('', False),             # пусто
])
def test_validate_login(login, valid):
    assert (len(validation.validate_login(login)) == 0) is valid


@pytest.mark.parametrize('password, valid', [
    ('Password1', True),          # латиница + цифра + регистр
    ('Пароль123', True),          # кириллица
    ('Pass~word1', True),         # спецсимвол
    ('short1A', False),           # короткий
    ('password1', False),         # нет заглавной
    ('PASSWORD1', False),         # нет строчной
    ('Password', False),          # нет цифры
    ('Pass word1', False),        # пробел
    ('Pass中文1', False),          # недопустимые символы
])
def test_validate_password(password, valid):
    assert (len(validation.validate_password(password)) == 0) is valid
