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

---

### Лаба 3 — Flask: сессии, аутентификация (Flask-Login)
Путь: `Лаба 3/`

**Что реализовано:**
- `/counter` — «Счётчик посещений»: число посещений хранится в глобальном объекте
  `session`, поэтому у каждого пользователя/браузера своё значение
- `/login` — форма входа (логин, пароль, чекбокс «Запомнить меня»):
  - пользователь `user` с паролем `qwerty`
  - при успешном входе — редирект на главную с сообщением об успехе
  - при ошибке — остаёмся на странице входа с сообщением о неверных данных
  - чекбокс «Запомнить меня» устанавливает `remember_token` (срок хранения 30 дней)
- `/logout` — выход из системы
- `/secret` — «Секретная страница», доступна только через `@login_required`:
  - ссылка в навбаре видна только аутентифицированным пользователям
  - анонимного пользователя перенаправляет на `/login?next=/secret`
    с сообщением о необходимости аутентификации
  - после входа происходит автоматический возврат на запрошенную страницу
- Навбар со ссылками на все страницы; блок «Войти/Выйти» зависит от статуса
- **21 тест** в `tests/test_app.py`

**Запуск в Git Bash (как в предыдущих лабах):**
```bash
cd "Лаба 3/app"
source ve/Scripts/activate
pip install -r ../requirements.txt
python app.py
```

Либо одной командой (скрипт сам найдёт/создаст окружение и поставит зависимости):
```bash
cd "Лаба 3/app"
bash run.sh
```

**Запуск в cmd/PowerShell (Windows):**
```bat
cd "Лаба 3/app"
run.bat
```
или вручную:
```bat
cd "Лаба 3/app"
python -m venv ve
ve\Scripts\activate
pip install -r ..\requirements.txt
python app.py
```

Приложение откроется на http://127.0.0.1:5000

> ⚠️ **Важно:** запускать нужно **из активированного окружения** (`ve`).
> Если выполнить `python app.py` системным Python, будет ошибка
> `ModuleNotFoundError: No module named 'flask_login'`.

**Тесты:**
```bash
# Git Bash
cd "Лаба 3/app"
source ve/Scripts/activate
python -m pytest tests/ -v
```
```bat
:: cmd / PowerShell
cd "Лаба 3/app"
ve\Scripts\python.exe -m pytest tests\ -v
```

**Деплой на хостинг (Render):**
1. Запушить репозиторий на GitHub.
2. На [render.com](https://render.com) → *New* → *Blueprint* → выбрать репозиторий
   (Render сам прочитает `render.yaml` из корня).
   Либо *New* → *Web Service*, указать:
   - **Root Directory:** `Лаба 3/app`
   - **Build Command:** `pip install -r ../requirements.txt`
   - **Start Command:** `gunicorn app:app`
3. В настройках сервиса задать переменную окружения `SECRET_KEY`.
4. Готовая ссылка будет вида `https://flask-lab3.onrender.com`.

> `Procfile` (`web: gunicorn app:app`) уже добавлен в `Лаба 3/app/`.
