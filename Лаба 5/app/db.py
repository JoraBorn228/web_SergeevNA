"""Слой доступа к базе данных (SQLite).

Содержит инициализацию схемы, наполнение (seed) и функции-хелперы
для работы с таблицами ``users``, ``roles`` и ``visit_logs``.
"""
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

# ─── Схема БД ─────────────────────────────────────────────────────────────────

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

CREATE TABLE IF NOT EXISTS visit_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    path       TEXT    NOT NULL,
    user_id    INTEGER REFERENCES users (id) ON DELETE SET NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

DEFAULT_ROLES = [
    ('Администратор', 'Полный доступ к управлению системой и отчётами'),
    ('Пользователь', 'Работа со своим профилем и просмотр своего журнала'),
]

# Учётные записи по умолчанию (создаются при первом запуске)
DEFAULT_USERS = [
    ('admin', 'Admin123', 'Администратор', 'Системы', None, 'Администратор'),
    ('user', 'User123', 'Иванов', 'Иван', 'Иванович', 'Пользователь'),
]


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

    # Пользователи по умолчанию
    for login, password, last, first, middle, role_name in DEFAULT_USERS:
        role = db.execute(
            'SELECT id FROM roles WHERE name = ?', (role_name,)
        ).fetchone()
        db.execute(
            """
            INSERT OR IGNORE INTO users
                (login, password_hash, last_name, first_name, middle_name, role_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                login,
                generate_password_hash(password),
                last,
                first,
                middle,
                role['id'] if role else None,
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
        """
        SELECT u.*, r.name AS role_name
        FROM users u
        LEFT JOIN roles r ON r.id = u.role_id
        WHERE u.login = ?
        """,
        (login,),
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


# ─── Журнал посещений ─────────────────────────────────────────────────────────

def log_visit(path, user_id):
    """Записывает посещение страницы в журнал."""
    db = get_db()
    db.execute(
        'INSERT INTO visit_logs (path, user_id) VALUES (?, ?)',
        (path, user_id),
    )
    db.commit()


def count_visits(user_id=None):
    """Общее количество записей журнала (при необходимости — по пользователю)."""
    if user_id is None:
        row = get_db().execute('SELECT COUNT(*) AS c FROM visit_logs').fetchone()
    else:
        row = get_db().execute(
            'SELECT COUNT(*) AS c FROM visit_logs WHERE user_id = ?',
            (user_id,),
        ).fetchone()
    return row['c']


def list_visits(user_id=None, limit=None, offset=0):
    """Записи журнала (по убыванию даты) с данными пользователя."""
    sql = """
        SELECT v.id, v.path, v.user_id, v.created_at,
               u.last_name, u.first_name, u.middle_name, u.login
        FROM visit_logs v
        LEFT JOIN users u ON u.id = v.user_id
    """
    params = []
    if user_id is not None:
        sql += ' WHERE v.user_id = ?'
        params.append(user_id)
    sql += ' ORDER BY v.created_at DESC, v.id DESC'
    if limit is not None:
        sql += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
    return get_db().execute(sql, params).fetchall()


def report_by_pages():
    """Отчёт: количество посещений по страницам (по убыванию)."""
    return get_db().execute(
        """
        SELECT path, COUNT(*) AS cnt
        FROM visit_logs
        GROUP BY path
        ORDER BY cnt DESC, path ASC
        """
    ).fetchall()


def report_by_users():
    """Отчёт: количество посещений по пользователям (по убыванию)."""
    return get_db().execute(
        """
        SELECT v.user_id AS user_id,
               u.last_name, u.first_name, u.middle_name, u.login,
               COUNT(*) AS cnt
        FROM visit_logs v
        LEFT JOIN users u ON u.id = v.user_id
        GROUP BY v.user_id
        ORDER BY cnt DESC
        """
    ).fetchall()
