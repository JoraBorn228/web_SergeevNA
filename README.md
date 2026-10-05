# Лабораторные работы по Web-разработке

**Сергеев Никита Андреевич — группа 241-372**

## Содержание

### Лаба 1 — Блог на Flask (шаблоны Jinja2)
Путь: `Лаба 1/lab1_template/`

**Что реализовано:**
- Страница списка постов (`/posts`)
- Страница отдельного поста (`/posts/<index>`) с шаблоном `post.html`:
  - Заголовок, автор, дата публикации, изображение, текст поста
  - Вложенные комментарии и ответы на них (Bootstrap media objects)
  - Форма «Оставьте комментарий»
- Footer с ФИО и группой во всех шаблонах
- Обработка 404 для несуществующих постов
- **20 тестов** в `tests/test_posts.py`

**Запуск:**
```bash
cd "Лаба 1/lab1_template/app"
python -m venv ve
ve\Scripts\activate
pip install -r ../requirements.txt
python app.py
```

**Тесты:**
```bash
cd "Лаба 1/lab1_template/app"
python -m pytest tests/ -v
```

---

### Лаба 2 — Flask: данные запроса и валидация телефона
Путь: `Лаба 2/`

**Что реализовано:**
- `/url-params` — параметры URL-запроса
- `/headers` — заголовки HTTP-запроса
- `/cookies` — установка/удаление cookie `lab2_visited`
- `/form-params` — параметры POST-формы
- `/phone` — валидация и форматирование номера телефона (формат `8-XXX-XXX-XX-XX`)
  - Bootstrap классы `is-invalid` / `invalid-feedback` при ошибке
  - Поддерживаемые форматы: `+7 (123) 456-78-90`, `8(123)4567890`, `123.456.78.90`
- **24 теста** в `tests/test_app.py`

**Запуск:**
```bash
cd "Лаба 2/app"
python -m venv ve
ve\Scripts\activate
pip install flask pytest pytest-mock
python app.py
```

**Тесты:**
```bash
cd "Лаба 2/app"
python -m pytest tests/ -v
```
