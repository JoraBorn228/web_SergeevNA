# --- Использование правильных шаблонов ---

def test_index_uses_index_template(client, captured_templates):
    with captured_templates as templates:
        client.get('/')
        assert len(templates) == 1
        template, _ = templates[0]
        assert template.name == 'index.html'


def test_posts_uses_posts_template(client, captured_templates, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    with captured_templates as templates:
        client.get('/posts')
        assert len(templates) == 1
        template, _ = templates[0]
        assert template.name == 'posts.html'


def test_post_uses_post_template(client, captured_templates, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    with captured_templates as templates:
        client.get('/posts/0')
        assert len(templates) == 1
        template, _ = templates[0]
        assert template.name == 'post.html'


def test_about_uses_about_template(client, captured_templates):
    with captured_templates as templates:
        client.get('/about')
        assert len(templates) == 1
        template, _ = templates[0]
        assert template.name == 'about.html'


# --- Передача данных в шаблоны ---

def test_posts_context_contains_posts(client, captured_templates, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    with captured_templates as templates:
        client.get('/posts')
        _, context = templates[0]
        assert context['posts'] == posts_list


def test_posts_context_contains_title(client, captured_templates, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    with captured_templates as templates:
        client.get('/posts')
        _, context = templates[0]
        assert context['title'] == 'Посты'


def test_post_context_contains_post(client, captured_templates, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    with captured_templates as templates:
        client.get('/posts/0')
        _, context = templates[0]
        assert context['post'] == posts_list[0]


def test_post_context_title_equals_post_title(client, captured_templates, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    with captured_templates as templates:
        client.get('/posts/0')
        _, context = templates[0]
        assert context['title'] == posts_list[0]['title']


def test_about_context_contains_title(client, captured_templates):
    with captured_templates as templates:
        client.get('/about')
        _, context = templates[0]
        assert context['title'] == 'Об авторе'


# --- Отображение данных поста на странице ---

def test_post_page_contains_title(client, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    response = client.get('/posts/0')
    assert 'Заголовок поста' in response.text


def test_post_page_contains_text(client, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    response = client.get('/posts/0')
    assert 'Текст поста' in response.text


def test_post_page_contains_author(client, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    response = client.get('/posts/0')
    assert 'Иванов Иван Иванович' in response.text


def test_post_page_contains_image(client, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    response = client.get('/posts/0')
    assert '123.jpg' in response.text


def test_post_page_date_has_correct_format(client, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    response = client.get('/posts/0')
    assert '10.03.2025' in response.text


def test_post_page_contains_comment_form(client, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    response = client.get('/posts/0')
    assert 'Оставьте комментарий' in response.text
    assert '<textarea' in response.text
    assert 'Отправить' in response.text


def test_post_page_contains_comments(client, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    response = client.get('/posts/0')
    assert 'Петров Пётр Петрович' in response.text
    assert 'Текст комментария' in response.text


def test_post_page_contains_replies(client, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    response = client.get('/posts/0')
    assert 'Сидоров Семён Семёнович' in response.text
    assert 'Текст ответа' in response.text


def test_posts_page_contains_post_data(client, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    response = client.get('/posts')
    assert 'Заголовок поста' in response.text
    assert 'Иванов Иван Иванович' in response.text
    assert '10.03.2025' in response.text


# --- Подвал сайта ---

def test_base_template_contains_footer(client):
    response = client.get('/')
    assert 'Сергеев Никита Андреевич' in response.text
    assert '241-372' in response.text


# --- Коды состояния ---

def test_index_status_ok(client):
    assert client.get('/').status_code == 200


def test_posts_status_ok(client):
    assert client.get('/posts').status_code == 200


def test_about_status_ok(client):
    assert client.get('/about').status_code == 200


def test_post_status_ok(client, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    assert client.get('/posts/0').status_code == 200


def test_post_returns_404_for_missing_index(client, mocker, posts_list):
    mocker.patch('app.posts_list', return_value=posts_list, autospec=True)
    response = client.get('/posts/1')
    assert response.status_code == 404


def test_post_returns_404_for_large_index(client):
    response = client.get('/posts/999')
    assert response.status_code == 404
