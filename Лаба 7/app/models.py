from datetime import datetime
from pathlib import Path

from flask import current_app, url_for
from flask_login import UserMixin
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


book_genres = Table(
    'book_genres', db.metadata,
    Column('book_id', ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True),
)


class Role(db.Model):
    __tablename__ = 'roles'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    users: Mapped[list['User']] = relationship(back_populates='role')


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100))
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'), nullable=False)
    role: Mapped[Role] = relationship(back_populates='users')
    reviews: Mapped[list['Review']] = relationship(back_populates='user', cascade='all, delete-orphan')
    views: Mapped[list['BookView']] = relationship(back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return ' '.join(part for part in (self.last_name, self.first_name, self.middle_name) if part)

    def has_role(self, *names):
        return self.role is not None and self.role.name in names


class Genre(db.Model):
    __tablename__ = 'genres'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    books: Mapped[list['Book']] = relationship(secondary=book_genres, back_populates='genres')


class Book(db.Model):
    __tablename__ = 'books'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    publisher: Mapped[str] = mapped_column(String(160), nullable=False)
    author: Mapped[str] = mapped_column(String(160), nullable=False)
    page_count: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    genres: Mapped[list[Genre]] = relationship(secondary=book_genres, back_populates='books')
    cover: Mapped['Cover'] = relationship(back_populates='book', cascade='all, delete-orphan', uselist=False)
    reviews: Mapped[list['Review']] = relationship(back_populates='book', cascade='all, delete-orphan')
    views: Mapped[list['BookView']] = relationship(back_populates='book', cascade='all, delete-orphan')

    @property
    def average_rating(self):
        return round(sum(review.rating for review in self.reviews if review.approved) /
                     max(sum(1 for review in self.reviews if review.approved), 1), 2)

    @property
    def review_count(self):
        return sum(1 for review in self.reviews if review.approved)


class Cover(db.Model):
    __tablename__ = 'covers'
    id: Mapped[int] = mapped_column(primary_key=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    md5_hash: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id', ondelete='CASCADE'), unique=True, nullable=False)
    book: Mapped[Book] = relationship(back_populates='cover')

    @property
    def url(self):
        return url_for('main.cover_file', cover_id=self.id)

    @property
    def path(self):
        return Path(current_app.config['UPLOAD_FOLDER']) / self.file_name


class Review(db.Model):
    __tablename__ = 'reviews'
    __table_args__ = (UniqueConstraint('book_id', 'user_id', name='uq_reviews_book_user'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating: Mapped[int] = mapped_column(nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    approved: Mapped[bool] = mapped_column(default=True, nullable=False)
    book: Mapped[Book] = relationship(back_populates='reviews')
    user: Mapped[User] = relationship(back_populates='reviews')


class BookView(db.Model):
    __tablename__ = 'book_views'
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True)
    visitor_id: Mapped[str | None] = mapped_column(String(36), index=True)
    viewed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False, index=True)
    book: Mapped[Book] = relationship(back_populates='views')
    user: Mapped[User | None] = relationship(back_populates='views')
