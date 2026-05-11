import os
import json
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import io
import zipfile 
from datetime import datetime
import uuid
from yookassa import Configuration, Payment






app = Flask(__name__)
app.secret_key = "ultimate_steam_with_registration_v686586786877878657564678658658976865765765765"

# ==========================================================
# ТВОЙ МАССИВ ДАННЫХ
# ==========================================================
DATA_FILE = 'data.json' # Файл будет лежать прямо рядом с этим скриптом

DEFAULT_DATA = {
    "games": [
        {
            "id": 0, 
            "title": "Cyberpunk 2077", 
            "price": 0, 
            "cat": "RPG", 
            "dev": "CD PROJEKT RED", 
            "img": "https://unsplash.com", 
            "desc": "RPG в открытом мире Найт-Сити.", 
            "download_url": "https://example.com"
        }
    ],
    "users": [
        {"username": "admin", "password": generate_password_hash("9448868"), "balance": 10000, "role": "admin", "library": []}
    ]
}

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_DATA, f, indent=4, ensure_ascii=False)
        return DEFAULT_DATA
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

DATA = load_data()

# ==========================================================
# ДИЗАЙН (CSS И LAYOUT)
# ==========================================================
CSS = """
<style>
    :root { --bg: #1b2838; --nav: #171d25; --text: #c7d5e0; --blue: #66c0f4; --green: #a3d200; --card: #16202d; }
    body { background: var(--bg); color: var(--text); font-family: Arial, sans-serif; margin: 0; padding-bottom: 50px; }
    header { background: var(--nav); padding: 15px 0; border-bottom: 1px solid #000; position: sticky; top: 0; z-index: 100; }
    .nav-wrap { max-width: 1000px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; }
    .container { max-width: 1000px; margin: 30px auto; padding: 0 20px; }
    .game-card { background: var(--card); display: flex; margin-bottom: 15px; border-radius: 4px; overflow: hidden; border: 1px solid transparent; transition: 0.2s; cursor: pointer; text-decoration: none; color: inherit; }
    .game-card:hover { border-color: var(--blue); background: #1f2d3d; }
    .game-card img { width: 220px; height: 110px; object-fit: cover; }
    .btn { padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; font-weight: bold; text-decoration: none; color: white; display: inline-block; text-align:center; }
    .btn-blue { background: #66c0f4; }
    .btn-green { background: #5c7e10; }
    .flash { background: #44b2f8; color: black; padding: 15px; margin-bottom: 20px; border-radius: 4px; }
    input, textarea { background: #32353c; border: 1px solid #000; color: white; padding: 12px; width: 100%; margin-bottom: 15px; box-sizing: border-box; border-radius: 4px; }
    pre { background: #000; color: #a3d200; padding: 15px; border: 1px solid #333; overflow-x: auto; font-size: 11px; max-height: 400px; }
    .auth-box { max-width: 400px; margin: 50px auto; background: var(--card); padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
</style>
"""

TOP = CSS + """
<header><div class="nav-wrap">
    <a href="/" style="color:white; text-decoration:none; font-weight:bold; font-size:22px;">Telegram<span style="color:var(--blue)">Store</span></a>
    <div>
        <a href="/" style="color:white; text-decoration:none; margin-right:15px;">МАГАЗИН</a>
        {% if session.get('user') %}
            <a href="/library" style="color:white; text-decoration:none; margin-right:15px;">БИБЛИОТЕКА</a>
            <a href="/profile" style="color:var(--blue); text-decoration:none; margin-right:15px;">ПРОФИЛЬ</a>
            {% if session.get('role') == 'admin' %}<a href="/admin" style="color:#ff4b4b; text-decoration:none;">АДМИН</a>{% endif %}
            <a href="/logout" style="margin-left:15px; color:#888; text-decoration:none;">ВЫХОД</a>
        {% else %}
            <a href="/login" style="color:white; text-decoration:none; margin-right:10px;">ВХОД</a>
            <a href="/register" style="color:var(--blue); text-decoration:none;">РЕГИСТРАЦИЯ</a>
        {% endif %}
    </div>
</div></header>
<div class="container">
    {% with messages = get_flashed_messages() %}
      {% if messages %} {% for m in messages %} <div class="flash">{{ m }}</div> {% endfor %} {% endif %}
    {% endwith %}
"""

# ==========================================================
# РОУТЫ
# ==========================================================

@app.route('/')
def index():
    content = """
    <h2>Витрина магазина</h2>
    {% for g in games %}
    <a href="/game/{{ g.id }}" class="game-card">
        <img src="{{ g.img if g.img else 'https://placeholder.com' }}">
        <div style="padding:15px; flex-grow:1;">
            <div style="font-size:18px; font-weight:bold;">{{ g.title }}</div>
            <div style="color:#8f98a0; font-size:12px;">{{ g.cat }} | {{ g.dev }}</div>
        </div>
        <div style="padding:20px; text-align:right;">
            <div style="font-size:18px; color:var(--green); font-weight:bold;">{{ g.price }} ₽</div>
            <span class="btn btn-blue" style="margin-top:10px;">Подробнее</span>
        </div>
    </a>
    {% endfor %}
    """
    return render_template_string(TOP + content + "</div>", games=DATA['games'])





@app.route('/download/<int:id>')
def download_game(id):
    if 'user' not in session: 
        return redirect('/login')
    
    user = next((u for u in DATA['users'] if u['username'] == session['user']), None)
    game = next((g for g in DATA['games'] if g['id'] == id), None)
    
    # Проверяем, что игра куплена и ссылка существует
    if user and game and id in user['library']:
        url = game.get('download_url')
        if url:
            # Перенаправляем браузер пользователя на прямую скачку
            return redirect(url)
        else:
            flash("Ссылка на скачивание не указана!")
            return redirect(url_for('game_detail', id=id))
    
    flash("Сначала купите игру!")
    return redirect('/')




@app.route('/game/<int:id>')
def game_detail(id):
    # Безопасный поиск игры
    game = next((g for g in DATA['games'] if g['id'] == id), None)
    if not game:
        flash("Игра не найдена!")
        return redirect('/')

    is_owned = False
    if 'user' in session:
        # Безопасный поиск пользователя
        user = next((u for u in DATA['users'] if u['username'] == session['user']), None)
        if user:
            is_owned = id in user['library']
        else:
            session.clear() # Если пользователь в сессии есть, а в DATA нет
        
    content = """
    <div style="background:var(--card); padding:20px; border-radius:8px;">
        <img src="{{ game.img }}" style="width:100%; max-height:400px; object-fit:cover; border-radius:5px; margin-bottom:20px;">
        <h1>{{ game.title }}</h1>
        <p style="font-size:18px; line-height:1.6;">{{ game.desc }}</p>
        <hr style="border-color:#333; margin:20px 0;">
        {% if is_owned %}
            <a href="/download/{{ game.id }}" class="btn btn-green" style="width:100%; font-size:18px; text-align:center;">
        СКАЧАТЬ
    </a>
        {% else %}
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:28px; color:var(--green)">{{ game.price }} ₽</span>
                <a href="/buy/{{ game.id }}" class="btn btn-green" style="font-size:18px;">КУПИТЬ</a>
            </div>
        {% endif %}
    </div>
    """
    return render_template_string(TOP + content + "</div>", game=game, is_owned=is_owned)

@app.route('/profile', methods=['GET'])
def profile():
    if 'user' not in session: return redirect('/login')
    user = next((u for u in DATA['users'] if u['username'] == session['user']), None)
    if not user: 
        session.clear()
        return redirect('/login')
    
    return render_template_string(TOP + """
    <h2>Мой профиль: {{ user.username }}</h2>
    """, user=user)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('role') != 'admin': return redirect('/')
    if request.method == 'POST':
        new_id = max([g['id'] for g in DATA['games']] + [-1]) + 1
        DATA['games'].append({
            "id": new_id, "title": request.form['title'], "price": int(request.form['price']),
            "cat": request.form['cat'], "dev": request.form['dev'], "img": request.form['img'],
            "desc": request.form['desc'], "reviews": []
        })
        flash("Игра добавлена!")

    json_text = json.dumps(DATA, indent=4, ensure_ascii=False)
    return render_template_string(TOP + """
    <h2>Админ-панель</h2>
    <form method="post" style="background:var(--card); padding:20px; margin-bottom:20px;">
        <input name="title" placeholder="Название" required>
        <input name="price" type="number" placeholder="Цена">
        <input name="cat" placeholder="Жанр">
        <input name="dev" placeholder="Разработчик">
        <input name="img" placeholder="Ссылка на фото">
        <input name="download_url" placeholder="Ссылка на файл">
        <textarea name="desc" placeholder="Описание"></textarea>
        <button class="btn btn-blue" style="width:100%">Добавить</button>
    </form>
    <h3>JSON для сохранения:</h3>
    <pre id="d">{{ j }}</pre>
    <button class="btn btn-green" onclick="navigator.clipboard.writeText(document.getElementById('d').innerText); alert('Скопировано!')">Копировать</button>
    </div>""", j=json_text)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        if any(u['username'] == username for u in DATA['users']):
            flash("Логин занят!"); return redirect('/register')
        DATA['users'].append({"username": username, "password": generate_password_hash(password), "balance": 1000, "role": "admin" if username == "admin" else "user", "library": []})
        flash("Успешно! Теперь войдите."); return redirect('/login')
    return render_template_string(TOP + '<div class="auth-box"><h2>Регистрация</h2><form method="post"><input name="username" placeholder="Логин" required><input type="password" name="password" placeholder="Пароль" required><button class="btn btn-blue" style="width:100%">Создать</button></form></div></div>')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = next((u for u in DATA['users'] if u['username'] == request.form['username']), None)
        if user and check_password_hash(user['password'], request.form['password']):
            session.update({'user': user['username'], 'role': user['role']})
            return redirect('/')
        flash("Ошибка входа")
    return render_template_string(TOP + '<div class="auth-box"><h2>Вход</h2><form method="post"><input name="username" placeholder="Логин" required><input type="password" name="password" placeholder="Пароль" required><button class="btn btn-blue" style="width:100%">Войти</button></form></div></div>')

@app.route('/buy/<int:id>')
def buy(id):
    if 'user' not in session: return redirect('/login')
    user = next((u for u in DATA['users'] if u['username'] == session['user']), None)
    game = next((g for g in DATA['games'] if g['id'] == id), None)
    if user and game and id not in user['library'] and user['balance'] >= game['price']:
        user['balance'] -= game['price']
        user['library'].append(id)
        flash("Куплено!")
    return redirect('/library')

@app.route('/library')
def library():
    if 'user' not in session: return redirect('/login')
    user = next((u for u in DATA['users'] if u['username'] == session['user']), None)
    if not user:
        session.clear()
        return redirect('/login')
    my_games = [g for g in DATA['games'] if g['id'] in user['library']]
    content = """
    <h2>Моя библиотека ({{ my_games|length }})</h2>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
        {% for g in my_games %}
        <div style="background:var(--card); border-radius:5px; overflow:hidden;">
            <img src="{{ g.img }}" style="width:100%; height:150px; object-fit:cover;">
            <div style="padding:15px;">
    <b>{{ g.title }}</b>
    <!-- Оборачиваем кнопку в ссылку на скачивание -->
    <a href="/download/{{ g.id }}" class="btn btn-blue" style="width:100%; margin-top:10px; text-align:center; display:block; box-sizing:border-box;">
        СКАЧАТЬ
    </a>
</div>

        {% endfor %}
    </div>
    """
    return render_template_string(TOP + content + "</div>", my_games=my_games)

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)



