from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next', '')
    if request.method == 'POST':
        login = (request.form.get('login') or '').strip()
        password = request.form.get('password') or ''
        user = User.query.filter_by(login=login).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Вы вошли в систему.', 'success')
            target = request.form.get('next', '')
            if target.startswith('/') and not target.startswith('//'):
                return redirect(target)
            return redirect(url_for('main.index'))
        flash('Неверный логин или пароль.', 'danger')
    return render_template('login.html', next_url=next_url)


@bp.route('/logout', methods=['POST'])
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('Вы вышли из системы.', 'success')
    return redirect(url_for('main.index'))
