"""Серверная валидация данных форм.

Правила:
  * логин  — только латинские буквы и цифры, длина не менее 5 символов;
  * пароль — 8..128 символов, без пробелов, только латиница/кириллица, арабские
             цифры и спецсимволы ``~!?@#$%^&*_-+()[]{}\\><|"',:;``,
             минимум одна заглавная, одна строчная буква и одна цифра.
"""
import re

LOGIN_RE = re.compile(r'^[A-Za-z0-9]+$')

# Разрешённые символы пароля: буквы (лат/кир), арабские цифры и спецсимволы
ALLOWED_RE = re.compile(r'^[A-Za-zА-Яа-яЁё0-9~!?@#$%^&*_\-+()\[\]{}\/><|"\',:;]+$')

UPPER_RE = re.compile(r'[A-ZА-ЯЁ]')
LOWER_RE = re.compile(r'[a-zа-яё]')
DIGIT_RE = re.compile(r'[0-9]')
WHITESPACE_RE = re.compile(r'\s')

ALLOWED_SPECIALS = "~!?@#$%^&*_-+()[]{}\\><|\"',:;"


def validate_login(login):
    """Возвращает список сообщений об ошибках для логина."""
    errors = []
    if not login:
        errors.append('Поле не может быть пустым')
        return errors
    if not LOGIN_RE.match(login):
        errors.append('Логин должен содержать только латинские буквы и цифры')
    if len(login) < 5:
        errors.append('Логин должен содержать не менее 5 символов')
    return errors


def validate_password(password):
    """Возвращает список сообщений об ошибках для пароля."""
    errors = []
    if not password:
        errors.append('Поле не может быть пустым')
        return errors
    if len(password) < 8:
        errors.append('Пароль должен содержать не менее 8 символов')
    if len(password) > 128:
        errors.append('Пароль должен содержать не более 128 символов')
    if WHITESPACE_RE.search(password):
        errors.append('Пароль не должен содержать пробелов')
    if not ALLOWED_RE.match(password):
        errors.append(
            'Пароль может содержать только латинские/кириллические буквы, '
            'арабские цифры и символы ' + ALLOWED_SPECIALS
        )
    if not UPPER_RE.search(password):
        errors.append('Пароль должен содержать хотя бы одну заглавную букву')
    if not LOWER_RE.search(password):
        errors.append('Пароль должен содержать хотя бы одну строчную букву')
    if not DIGIT_RE.search(password):
        errors.append('Пароль должен содержать хотя бы одну цифру')
    return errors


def validate_user_form(data, is_edit=False):
    """Проверяет данные формы пользователя.

    Возвращает словарь ``{имя_поля: сообщение}`` (по одному сообщению на поле,
    берётся первое нарушение).
    """
    errors = {}

    # Логин и пароль — только при создании
    if not is_edit:
        login_errors = validate_login((data.get('login') or '').strip())
        if login_errors:
            errors['login'] = login_errors[0]

        password_errors = validate_password(data.get('password') or '')
        if password_errors:
            errors['password'] = password_errors[0]

    # Обязательные поля
    if not (data.get('last_name') or '').strip():
        errors['last_name'] = 'Поле не может быть пустым'
    if not (data.get('first_name') or '').strip():
        errors['first_name'] = 'Поле не может быть пустым'

    return errors


def validate_password_change(old_password, new_password, confirm_password):
    """Проверяет данные формы смены пароля (без сверки старого с БД)."""
    errors = {}

    if not old_password:
        errors['old_password'] = 'Поле не может быть пустым'

    new_errors = validate_password(new_password or '')
    if new_errors:
        errors['new_password'] = new_errors[0]

    if not confirm_password:
        errors['confirm_password'] = 'Поле не может быть пустым'
    elif new_password != confirm_password:
        errors['confirm_password'] = 'Пароли не совпадают'

    return errors
