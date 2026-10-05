import re
from flask import Flask, render_template, request, redirect, url_for, make_response

app = Flask(__name__)
application = app

COOKIE_NAME = 'lab2_visited'
COOKIE_VALUE = 'yes'


def validate_phone(phone: str):
    """
    Validates and formats a phone number.
    Returns (formatted, error) where error is None on success.
    """
    # Check for invalid characters (only digits, spaces, +, (, ), -, . allowed)
    allowed = re.compile(r'^[\d\s\+\(\)\-\.]+$')
    if not allowed.match(phone):
        return None, 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'

    # Extract only digits
    digits = re.sub(r'\D', '', phone)

    # Determine required length
    stripped = phone.strip()
    if stripped.startswith('+7') or stripped.startswith('8'):
        required = 11
    else:
        required = 10

    if len(digits) != required:
        return None, 'Недопустимый ввод. Неверное количество цифр.'

    # Normalize to 11 digits starting with 8
    if len(digits) == 10:
        digits = '8' + digits

    # Format: 8-***-***-**-**
    formatted = f'8-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}'
    return formatted, None


@app.route('/')
def index():
    return render_template('index.html', title='Главная')


@app.route('/url-params')
def url_params():
    params = request.args.to_dict()
    return render_template('url_params.html', title='Параметры URL', params=params)


@app.route('/headers')
def headers():
    hdrs = dict(request.headers)
    return render_template('headers.html', title='Заголовки запроса', headers=hdrs)


@app.route('/cookies')
def cookies():
    cookie_set = request.cookies.get(COOKIE_NAME)
    response = make_response(
        render_template('cookies.html', title='Cookie',
                         cookie_name=COOKIE_NAME,
                         cookie_value=cookie_set)
    )
    if cookie_set:
        response.delete_cookie(COOKIE_NAME)
    else:
        response.set_cookie(COOKIE_NAME, COOKIE_VALUE)
    return response


@app.route('/form-params', methods=['GET', 'POST'])
def form_params():
    params = {}
    if request.method == 'POST':
        params = request.form.to_dict()
    return render_template('form_params.html', title='Параметры формы', params=params, method=request.method)


@app.route('/phone', methods=['GET', 'POST'])
def phone():
    phone_input = ''
    formatted = None
    error = None
    if request.method == 'POST':
        phone_input = request.form.get('phone', '')
        formatted, error = validate_phone(phone_input)
    return render_template('phone.html', title='Проверка телефона',
                            phone_input=phone_input,
                            formatted=formatted,
                            error=error)


if __name__ == '__main__':
    app.run(debug=True)
