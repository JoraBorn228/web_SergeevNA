"""Авторизация: права пользователей, привязанные к ролям.

Права сгруппированы по названию роли. Проверка прав выполняется
декоратором :func:`check_rights`, который применяется к view-функциям.
"""
from functools import wraps

from flask import flash, redirect, request, url_for
from flask_login import current_user

# Названия ролей
ROLE_ADMIN = 'Администратор'
ROLE_USER = 'Пользователь'

# Права, соответствующие действиям
RIGHT_CREATE_USER = 'create_user'
RIGHT_EDIT_USER = 'edit_user'
RIGHT_VIEW_USER = 'view_user'
RIGHT_DELETE_USER = 'delete_user'
RIGHT_VIEW_VISITS_ALL = 'view_visits_all'
RIGHT_EDIT_OWN_PROFILE = 'edit_own_profile'
RIGHT_VIEW_OWN_PROFILE = 'view_own_profile'
RIGHT_VIEW_VISITS_OWN = 'view_visits_own'

# Права ролей
ROLE_RIGHTS = {
    ROLE_ADMIN: {
        RIGHT_CREATE_USER,
        RIGHT_EDIT_USER,
        RIGHT_VIEW_USER,
        RIGHT_DELETE_USER,
        RIGHT_VIEW_VISITS_ALL,
    },
    ROLE_USER: {
        RIGHT_EDIT_OWN_PROFILE,
        RIGHT_VIEW_OWN_PROFILE,
        RIGHT_VIEW_VISITS_OWN,
    },
}

NO_RIGHTS_MESSAGE = 'У вас недостаточно прав для доступа к данной странице.'
AUTH_REQUIRED_MESSAGE = (
    'Для доступа к запрашиваемой странице необходимо пройти процедуру '
    'аутентификации.'
)


def get_user_rights(user):
    """Возвращает множество прав пользователя согласно его роли."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return set()
    return set(ROLE_RIGHTS.get(getattr(user, 'role_name', None), set()))


def user_has_right(user, right):
    """Есть ли у пользователя указанное право."""
    return right in get_user_rights(user)


def user_has_any_right(user, rights):
    """Есть ли у пользователя хотя бы одно из указанных прав."""
    return bool(get_user_rights(user) & set(rights))


def check_rights(*required_rights):
    """Декоратор проверки прав для view-функции.

    Пользователь должен обладать хотя бы одним из переданных прав.
    Если пользователь не аутентифицирован — его перенаправляют на страницу
    входа; если прав недостаточно — на главную страницу с сообщением.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash(AUTH_REQUIRED_MESSAGE, 'warning')
                return redirect(url_for('login', next=request.url))
            if not user_has_any_right(current_user, required_rights):
                flash(NO_RIGHTS_MESSAGE, 'danger')
                return redirect(url_for('index'))
            return view_func(*args, **kwargs)
        return wrapper
    return decorator
