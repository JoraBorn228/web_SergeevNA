from datetime import datetime
import pytest


# ─── Вспомогательная фикстура с набором постов ───────────────────────────────

@pytest.fixture
def mock_posts():
    return [
        {
            'title': 'Заголовок поста',
            'text': 'Текст поста с подробным описанием',
            'author': 'Иванов Иван Иванович',
            'date': datetime(2025, 3, 10),
            'image_id': '7d4e9175-95ea-4c5f-8be5-92a6b708bb3c.jpg',
            'comments': [
                {
                    'author': 'Петров Пётр',
                    'text': 'Отличный пост!',
                    'replies': [
                        {'author': 'Сидоров Сидор', 'text': 'Согласен полностью!'}
                    ]
                }
            ]
        }
    ]


# ─── 1. Список постов: статус 200 ────────────────────────────────────────────

def test_posts_list_returns_200(client):
    response = client.get('/posts')
    assert response.status_code == 200


# ─── 2. Список постов: использует правильный шаблон ──────────────────────────

def test_posts_list_uses_correct_template(client, captured_templates, mocker, mock_posts):
    with captured_templates as templates:
        mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
        client.get('/posts')
        assert len(templates) == 1
        template, _ = templates[0]
        assert template.name == 'posts.html'


# ─── 3. Список постов: в контекст передаются title и posts ───────────────────

def test_posts_list_context_has_title_and_posts(client, captured_templates, mocker, mock_posts):
    with captured_templates as templates:
        mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
        client.get('/posts')
        _, context = templates[0]
        assert context['title'] == 'Посты'
        assert len(context['posts']) == 1


# ─── 4. Страница поста: статус 200 для существующего поста ───────────────────

def test_post_page_returns_200(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts/0')
    assert response.status_code == 200


# ─── 5. Страница поста: 404 для несуществующего индекса ──────────────────────

def test_post_page_404_for_invalid_index(client):
    response = client.get('/posts/9999')
    assert response.status_code == 404


# ─── 6. Страница поста: 404 для отрицательного индекса (как строка) ──────────

def test_post_page_404_for_high_index(client):
    response = client.get('/posts/100')
    assert response.status_code == 404


# ─── 7. Страница поста: использует правильный шаблон ─────────────────────────

def test_post_page_uses_correct_template(client, captured_templates, mocker, mock_posts):
    with captured_templates as templates:
        mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
        client.get('/posts/0')
        assert any(t.name == 'post.html' for t, _ in templates)


# ─── 8. Страница поста: в контекст передаётся post ───────────────────────────

def test_post_page_context_has_post(client, captured_templates, mocker, mock_posts):
    with captured_templates as templates:
        mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
        client.get('/posts/0')
        post_templates = [(t, c) for t, c in templates if t.name == 'post.html']
        assert len(post_templates) == 1
        _, context = post_templates[0]
        assert 'post' in context


# ─── 9. Страница поста: заголовок отображается на странице ───────────────────

def test_post_page_renders_title(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts/0')
    assert 'Заголовок поста' in response.text


# ─── 10. Страница поста: имя автора отображается на странице ─────────────────

def test_post_page_renders_author(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts/0')
    assert 'Иванов Иван Иванович' in response.text


# ─── 11. Страница поста: текст поста отображается на странице ────────────────

def test_post_page_renders_text(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts/0')
    assert 'Текст поста с подробным описанием' in response.text


# ─── 12. Страница поста: дата в формате ДД.ММ.ГГГГ ──────────────────────────

def test_post_page_renders_date_in_correct_format(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts/0')
    assert '10.03.2025' in response.text


# ─── 13. Страница поста: изображение присутствует на странице ────────────────

def test_post_page_has_image(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts/0')
    assert '7d4e9175-95ea-4c5f-8be5-92a6b708bb3c.jpg' in response.text


# ─── 14. Страница поста: форма комментария присутствует ──────────────────────

def test_post_page_has_comment_form(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts/0')
    assert 'Оставьте комментарий' in response.text
    assert '<form' in response.text
    assert 'Отправить' in response.text


# ─── 15. Страница поста: комментарий автора отображается ─────────────────────

def test_post_page_renders_comment_author(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts/0')
    assert 'Петров Пётр' in response.text


# ─── 16. Страница поста: текст комментария отображается ──────────────────────

def test_post_page_renders_comment_text(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts/0')
    assert 'Отличный пост!' in response.text


# ─── 17. Страница поста: ответ на комментарий отображается ──────────────────

def test_post_page_renders_reply(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts/0')
    assert 'Сидоров Сидор' in response.text
    assert 'Согласен полностью!' in response.text


# ─── 18. Главная страница: статус 200 ────────────────────────────────────────

def test_index_page_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200


# ─── 19. Footer присутствует на странице поста ───────────────────────────────

def test_footer_present_on_post_page(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts/0')
    assert 'Сергеев Никита Андреевич' in response.text
    assert '241-372' in response.text


# ─── 20. Footer присутствует на странице списка постов ───────────────────────

def test_footer_present_on_posts_list(client, mocker, mock_posts):
    mocker.patch('app.posts_list', return_value=mock_posts, autospec=True)
    response = client.get('/posts')
    assert 'Сергеев Никита Андреевич' in response.text
    assert '241-372' in response.text
