"""Слой доступа к базе данных (SQLite).

Содержит инициализацию схемы, наполнение (seed) и функции-хелперы
для работы с таблицами ``users`` и ``roles``.
"""
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

# ─── Подключение к БД ─────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    login         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    last_name     TEXT,
    first_name    TEXT,
    middle_name   TEXT,
    role_id       INTEGER REFERENCES roles (id) ON DELETE SET NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

DEFAULT_ROLES = [
    ('Администратор', 'Полный доступ к управлению системой'),
    ('Менеджер', 'Управление учётными записями пользователей'),
    ('Пользователь', 'Базовый доступ к приложению'),
]

# Учётная запись по умолчанию (создаётся при первом запуске)
DEFAULT_ADMIN_LOGIN = 'admin'
DEFAULT_ADMIN_PASSWORD = 'Admin123'


def get_db():
    """Возвращает соединение с БД, привязанное к контексту запроса."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(exception=None):
    """Закрывает соединение с БД в конце запроса."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Создаёт таблицы и наполняет БД начальными данными."""
    db = get_db()
    db.executescript(SCHEMA)

    # Роли
    for name, description in DEFAULT_ROLES:
        db.execute(
            'INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)',
            (name, description),
        )

    # Администратор по умолчанию
    admin_role = db.execute(
        'SELECT id FROM roles WHERE name = ?', ('Администратор',)
    ).fetchone()
    db.execute(
        """
        INSERT OR IGNORE INTO users
            (login, password_hash, last_name, first_name, middle_name, role_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            DEFAULT_ADMIN_LOGIN,
            generate_password_hash(DEFAULT_ADMIN_PASSWORD),
            'Администратор',
            'Системы',
            None,
            admin_role['id'] if admin_role else None,
        ),
    )
    db.commit()


def init_app(app):
    """Регистрирует обработчики жизненного цикла БД."""
    app.teardown_appcontext(close_db)


# ─── Роли ─────────────────────────────────────────────────────────────────────

def list_roles():
    return get_db().execute('SELECT * FROM roles ORDER BY id').fetchall()


def get_role(role_id):
    if role_id in (None, ''):
        return None
    return get_db().execute(
        'SELECT * FROM roles WHERE id = ?', (role_id,)
    ).fetchone()


# ─── Пользователи ─────────────────────────────────────────────────────────────

def list_users():
    """Список пользователей вместе с названием роли."""
    return get_db().execute(
        """
        SELECT u.*, r.name AS role_name
        FROM users u
        LEFT JOIN roles r ON r.id = u.role_id
        ORDER BY u.id
        """
    ).fetchall()


def get_user(user_id):
    return get_db().execute(
        """
        SELECT u.*, r.name AS role_name
        FROM users u
        LEFT JOIN roles r ON r.id = u.role_id
        WHERE u.id = ?
        """,
        (user_id,),
    ).fetchone()


def get_user_by_login(login):
    return get_db().execute(
        'SELECT * FROM users WHERE login = ?', (login,)
    ).fetchone()


def create_user(login, password, last_name, first_name, middle_name, role_id):
    db = get_db()
    cur = db.execute(
        """
        INSERT INTO users
            (login, password_hash, last_name, first_name, middle_name, role_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            login,
            generate_password_hash(password),
            last_name or None,
            first_name or None,
            middle_name or None,
            role_id or None,
        ),
    )
    db.commit()
    return cur.lastrowid


def update_user(user_id, last_name, first_name, middle_name, role_id):
    db = get_db()
    db.execute(
        """
        UPDATE users
        SET last_name = ?, first_name = ?, middle_name = ?, role_id = ?
        WHERE id = ?
        """,
        (
            last_name or None,
            first_name or None,
            middle_name or None,
            role_id or None,
            user_id,
        ),
    )
    db.commit()


def update_password(user_id, password):
    db = get_db()
    db.execute(
        'UPDATE users SET password_hash = ? WHERE id = ?',
        (generate_password_hash(password), user_id),
    )
    db.commit()


def delete_user(user_id):
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
