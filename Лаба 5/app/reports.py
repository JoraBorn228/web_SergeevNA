"""Модуль статистических отчётов (Blueprint).

Содержит:
  * «Журнал посещений» с пагинацией (``/visits/``);
  * отчёт по страницам (``/visits/pages``) и экспорт в CSV;
  * отчёт по пользователям (``/visits/users``) и экспорт в CSV.
"""
import csv
import io

from flask import Blueprint, Response, render_template, request
from flask_login import current_user

import db
from rights import (
    RIGHT_VIEW_VISITS_ALL, RIGHT_VIEW_VISITS_OWN,
    check_rights, user_has_right,
)

bp = Blueprint('reports', __name__, url_prefix='/visits')

PER_PAGE = 10
ANONYMOUS_LABEL = 'Неаутентифицированный пользователь'


def _display_user_name(row):
    """ФИО пользователя из строки выборки либо метка гостя."""
    if row['user_id'] is None:
        return ANONYMOUS_LABEL
    parts = [row['last_name'], row['first_name'], row['middle_name']]
    name = ' '.join(p for p in parts if p)
    return name or (row['login'] or f"Пользователь #{row['user_id']}")


def _csv_response(filename, header, rows):
    """Формирует CSV-файл (UTF-8 с BOM, разделитель «;») для скачивания."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';', lineterminator='\r\n')
    writer.writerow(header)
    writer.writerows(rows)
    content = '\ufeff' + buffer.getvalue()
    return Response(
        content,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@bp.route('/')
@check_rights(RIGHT_VIEW_VISITS_ALL, RIGHT_VIEW_VISITS_OWN)
def visits():
    """Главная страница журнала посещений с пагинацией."""
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    only_own = not user_has_right(current_user, RIGHT_VIEW_VISITS_ALL)
    user_filter = current_user.id if only_own else None

    total = db.count_visits(user_filter)
    pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    if page > pages:
        page = pages
    offset = (page - 1) * PER_PAGE
    logs = db.list_visits(user_filter, PER_PAGE, offset)

    return render_template(
        'visits.html',
        title='Журнал посещений',
        logs=logs,
        page=page,
        pages=pages,
        total=total,
        only_own=only_own,
        start_index=offset,
    )


@bp.route('/pages')
@check_rights(RIGHT_VIEW_VISITS_ALL)
def report_pages():
    """Отчёт по страницам: количество посещений каждой страницы."""
    rows = db.report_by_pages()
    return render_template(
        'report_pages.html',
        title='Отчёт по страницам',
        rows=rows,
    )


@bp.route('/pages/export')
@check_rights(RIGHT_VIEW_VISITS_ALL)
def export_pages():
    rows = db.report_by_pages()
    data = [
        (index, row['path'], row['cnt'])
        for index, row in enumerate(rows, start=1)
    ]
    return _csv_response(
        'report_by_pages.csv',
        ['№', 'Страница', 'Количество посещений'],
        data,
    )


@bp.route('/users')
@check_rights(RIGHT_VIEW_VISITS_ALL)
def report_users():
    """Отчёт по пользователям: количество посещений каждым пользователем."""
    rows = db.report_by_users()
    data = [
        {'name': _display_user_name(row), 'cnt': row['cnt']}
        for row in rows
    ]
    return render_template(
        'report_users.html',
        title='Отчёт по пользователям',
        rows=data,
    )


@bp.route('/users/export')
@check_rights(RIGHT_VIEW_VISITS_ALL)
def export_users():
    rows = db.report_by_users()
    data = [
        (index, _display_user_name(row), row['cnt'])
        for index, row in enumerate(rows, start=1)
    ]
    return _csv_response(
        'report_by_users.csv',
        ['№', 'Пользователь', 'Количество посещений'],
        data,
    )
