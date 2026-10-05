import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'lab3-super-secret-key-2025')
app.config['REMEMBER_COOKIE_DURATION'] = 2592000  # 30 days in seconds
application = app

# ─── Flask-Login setup ────────────────────────────────────────────────────────

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = (
    'Для доступа к данной странице необходимо пройти процедуру аутентификации.'
)
login_manager.login_message_category = 'warning'

# ─── User model ───────────────────────────────────────────────────────────────

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

USERS = {
    'user': User(id=1, username='user', password='qwerty'),
}

def get_user_by_username(username):
    return USERS.get(username)

@login_manager.user_loader
def load_user(user_id):
    for u in USERS.values():
        if str(u.id) == str(user_id):
            return u
    return None

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', title='Главная')


@app.route('/counter')
def counter():
    session['visits'] = session.get('visits', 0) + 1
    visits = session['visits']
    return render_template('counter.html', title='Счётчик посещений', visits=visits)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember'))

        user = get_user_by_username(username)
        if user and user.password == password:
            login_user(user, remember=remember)
            flash('Вы успешно вошли в систему!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверный логин или пароль.', 'danger')

    return render_template('login.html', title='Вход')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))


@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html', title='Секретная страница')


if __name__ == '__main__':
    app.run(debug=True)
