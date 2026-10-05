from pathlib import Path

from flask import Flask
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


@event.listens_for(Engine, 'connect')
def enable_sqlite_foreign_keys(connection, _record):
    if connection.__class__.__module__.startswith('sqlite3'):
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Для выполнения данного действия необходимо пройти процедуру аутентификации'
login_manager.login_message_category = 'warning'


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    upload_dir = Path(app.instance_path) / 'covers'
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config.from_mapping(
        SECRET_KEY='local-development-key-change-me',
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{Path(app.instance_path) / 'library.sqlite'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(upload_dir),
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    @app.context_processor
    def inject_current_user():
        return {'current_user': current_user}

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes import bp
    from app.auth import bp as auth_bp
    app.register_blueprint(bp)
    app.register_blueprint(auth_bp)

    @app.cli.command('init-db')
    def init_db_command():
        db.create_all()
        print('Таблицы библиотеки созданы.')

    return app
