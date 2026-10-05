from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user, login_required


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.has_role(*roles):
                flash('У вас недостаточно прав для выполнения данного действия', 'danger')
                return redirect(url_for('main.index'))
            return view(*args, **kwargs)
        return wrapped
    return decorator
