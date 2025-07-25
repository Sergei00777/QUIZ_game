from flask import Flask, render_template, request, session, redirect, url_for
import json
import sqlite3
from datetime import datetime
import random
from flask import jsonify  # Добавьте это в начало файла с другими импортами

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


# Инициализация БД
def init_db():
    conn = sqlite3.connect('quiz_game.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  money INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS inventory
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  item_name TEXT,
                  item_category TEXT,
                  purchase_date TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS quiz_results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  subject TEXT,
                  correct INTEGER,
                  wrong INTEGER,
                  date TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')

    conn.commit()
    conn.close()


init_db()

# Загрузка вопросов
with open('questions.json', 'r', encoding='utf-8') as f:
    questions_data = json.load(f)


@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('quiz_game.db')
    c = conn.cursor()
    c.execute("SELECT money FROM users WHERE username=?", (session['username'],))
    money = c.fetchone()[0]
    conn.close()

    return render_template('index.html', username=session['username'], money=money)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']

        conn = sqlite3.connect('quiz_game.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
        conn.commit()
        conn.close()

        session['username'] = username
        return redirect(url_for('index'))
    return render_template('login.html')


# ОДИН единственный обработчик для викторины
@app.route('/quiz/<subject>', methods=['GET', 'POST'])
def quiz(subject):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('quiz_game.db')
    c = conn.cursor()
    c.execute("SELECT id, money FROM users WHERE username=?", (session['username'],))
    user = c.fetchone()
    user_id, current_money = user[0], user[1]

    if request.method == 'POST':
        question_id = int(request.form['question_id'])
        selected_answer = int(request.form['answer'])
        question = questions_data[subject][question_id]

        if selected_answer == question['correct']:
            new_money = current_money + 1
            c.execute("UPDATE users SET money = ? WHERE id=?", (new_money, user_id))
            message = f"Правильно! +1 рубль. Ваш баланс: {new_money} руб."
        else:
            c.execute("SELECT wrong FROM quiz_results WHERE user_id=? ORDER BY date DESC LIMIT 1", (user_id,))
            last_result = c.fetchone()

            wrong_in_row = 1
            if last_result and last_result[0] >= 2:
                new_money = max(0, current_money - 5)
                c.execute("UPDATE users SET money = ? WHERE id=?", (new_money, user_id))
                message = f"Неправильно! Штраф -5 руб. за 3 ошибки подряд. Баланс: {new_money} руб."
            else:
                new_money = current_money
                message = "Неправильно! Попробуйте еще раз"

            c.execute("INSERT INTO quiz_results (user_id, subject, correct, wrong, date) VALUES (?, ?, ?, ?, ?)",
                      (user_id, subject, 0, wrong_in_row, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()
        return render_template('quiz_result.html', message=message, money=new_money, subject=subject)

    question = random.choice(questions_data[subject])
    question_id = questions_data[subject].index(question)
    conn.close()
    return render_template('quiz.html',
                           subject=subject,
                           question=question,
                           question_id=question_id,
                           money=current_money)


@app.route('/shop')
def shop():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        conn = sqlite3.connect('quiz_game.db')
        c = conn.cursor()
        c.execute("SELECT money FROM users WHERE username=?", (session['username'],))
        money = c.fetchone()[0]

        # Создаем структуру с ценами
        shop_items = {
            'Clothes': [
                {'name': 'Футболка', 'price': 10},
                {'name': 'Штаны', 'price': 15},
                {'name': 'Шапка', 'price': 15},
                {'name': 'Джинсы', 'price': 30},
                {'name': 'Куртка', 'price': 45},
                {'name': 'Кроссовки', 'price': 60},
                {'name': 'Рубашка', 'price': 25},
                {'name': 'Платье', 'price': 35},
                {'name': 'Кепка', 'price': 12},
                {'name': 'Толстовка', 'price': 40}
            ],
            'houses': [
                {'name': 'Домик', 'price': 100},
                {'name': 'Вилла', 'price': 300},
                {'name': 'Дворец', 'price': 1000},
                {'name': 'Бунгало', 'price': 200},
                {'name': 'Коттедж', 'price': 500},
                {'name': 'Замок', 'price': 2000},
                {'name': 'Хижина', 'price': 80},
                {'name': 'Таунхаус', 'price': 700},
                {'name': 'Небоскрёб', 'price': 5000},
                {'name': 'Подводный дом', 'price': 3000}
            ],
            'cars': [
                {'name': 'Велосипед', 'price': 50},
                {'name': 'Самокат', 'price': 25},
                {'name': 'Машина', 'price': 500},
                {'name': 'Мотоцикл', 'price': 300},
                {'name': 'Автобус', 'price': 800},
                {'name': 'Яхта', 'price': 1500},
                {'name': 'Снегоход', 'price': 400},
                {'name': 'Квадроцикл', 'price': 450},
                {'name': 'Вертолёт', 'price': 2500},
                {'name': 'Спорткар', 'price': 1200}
            ],
            'snacks': [
                {'name': 'Мороженое', 'price': 5},
                {'name': 'Шоколадка', 'price': 7},
                {'name': 'Пирожное', 'price': 8},
                {'name': 'Чипсы', 'price': 6},
                {'name': 'Леденец', 'price': 2},
                {'name': 'Сок', 'price': 4},
                {'name': 'Бургер', 'price': 10},
                {'name': 'Пицца', 'price': 12},
                {'name': 'Пончик', 'price': 6},
                {'name': 'Кофе', 'price': 5}
            ],
            'items': [
                {'name': 'Ручка', 'price': 3},
                {'name': 'Тетрадь', 'price': 5},
                {'name': 'Книга', 'price': 15},
                {'name': 'Ластик', 'price': 2},
                {'name': 'Линейка', 'price': 4},
                {'name': 'Рюкзак', 'price': 20},
                {'name': 'Ножницы', 'price': 6},
                {'name': 'Клей', 'price': 5},
                {'name': 'Фонарик', 'price': 18},
                {'name': 'Часы', 'price': 50}
            ],
            'weapons': [
                {'name': 'Нож', 'price': 20},
                {'name': 'Пистолет', 'price': 200},
                {'name': 'Винтовка', 'price': 500},
                {'name': 'Граната', 'price': 100},
                {'name': 'Бронежилет', 'price': 150},
                {'name': 'Лук', 'price': 80},
                {'name': 'Меч', 'price': 300},
                {'name': 'Дробовик', 'price': 400},
                {'name': 'Ракетница', 'price': 800},
                {'name': 'Лазерная пушка', 'price': 2000}
            ],
            'pets': [
                {'name': 'Кот', 'price': 30},
                {'name': 'Собака', 'price': 50},
                {'name': 'Попугай', 'price': 40},
                {'name': 'Хомяк', 'price': 20},
                {'name': 'Рыбка', 'price': 10},
                {'name': 'Черепаха', 'price': 60},
                {'name': 'Змея', 'price': 70},
                {'name': 'Паук', 'price': 25},
                {'name': 'Феникс', 'price': 1000},
                {'name': 'Дракон', 'price': 5000}
            ],
            'gadgets': [
                {'name': 'Телефон', 'price': 300},
                {'name': 'Ноутбук', 'price': 800},
                {'name': 'Наушники', 'price': 100},
                {'name': 'Смарт-часы', 'price': 150},
                {'name': 'Планшет', 'price': 400},
                {'name': 'Камера', 'price': 250},
                {'name': 'Квадрокоптер', 'price': 600},
                {'name': 'VR-очки', 'price': 350},
                {'name': 'Робот-пылесос', 'price': 450},
                {'name': 'Голографический проектор', 'price': 1200}
            ],
            'furniture': [
                {'name': 'Стул', 'price': 20},
                {'name': 'Стол', 'price': 50},
                {'name': 'Диван', 'price': 150},
                {'name': 'Кровать', 'price': 200},
                {'name': 'Шкаф', 'price': 120},
                {'name': 'Лампа', 'price': 30},
                {'name': 'Ковёр', 'price': 40},
                {'name': 'Полка', 'price': 35},
                {'name': 'Тумбочка', 'price': 45},
                {'name': 'Аквариум', 'price': 180}
            ],
            'plants': [
                {'name': 'Кактус', 'price': 15},
                {'name': 'Фикус', 'price': 25},
                {'name': 'Орхидея', 'price': 40},
                {'name': 'Сансевиерия', 'price': 30},
                {'name': 'Бамбук', 'price': 35},
                {'name': 'Плющ', 'price': 20},
                {'name': 'Алоэ', 'price': 18},
                {'name': 'Монстера', 'price': 60},
                {'name': 'Цветущая лоза', 'price': 50},
                {'name': 'Магическое дерево', 'price': 500}
            ]
        }

        return render_template('shop.html', categories=shop_items, money=money)
    except Exception as e:
        print(f"Ошибка: {e}")
        return render_template('shop.html', categories={}, money=0)
    finally:
        conn.close()


@app.route('/achievements')
def achievements():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        conn = sqlite3.connect('quiz_game.db')
        c = conn.cursor()

        # Получаем данные пользователя
        c.execute("SELECT id, money FROM users WHERE username=?", (session['username'],))
        user = c.fetchone()
        if not user:
            return redirect(url_for('login'))

        user_id, money = user

        # Получаем статистику по викторинам (группируем по предмету)
        c.execute("""
            SELECT subject, 
                   SUM(correct) as correct_answers,
                   SUM(wrong) as wrong_answers
            FROM quiz_results
            WHERE user_id = ?
            GROUP BY subject
        """, (user_id,))
        results = c.fetchall()

        # Получаем инвентарь (последние покупки)
        c.execute("""
            SELECT item_name, item_category
            FROM inventory
            WHERE user_id = ?
            ORDER BY purchase_date DESC
            LIMIT 10
        """, (user_id,))
        inventory = c.fetchall()

        return render_template('achievements.html',
                               username=session['username'],
                               money=money,
                               results=results,
                               inventory=inventory)

    except Exception as e:
        print(f"Ошибка при получении достижений: {e}")
        return render_template('achievements.html',
                               username=session.get('username'),
                               money=0,
                               results=[],
                               inventory=[])
    finally:
        conn.close()


@app.route('/purchase', methods=['POST'])
def purchase():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Требуется авторизация'})

    data = request.get_json()
    item = data['item']
    category = data['category']
    price = data['price']

    conn = sqlite3.connect('quiz_game.db')
    c = conn.cursor()

    # Проверяем баланс
    c.execute("SELECT id, money FROM users WHERE username=?", (session['username'],))
    user = c.fetchone()

    if not user or user[1] < price:
        conn.close()
        return jsonify({'success': False, 'message': 'Недостаточно средств'})

    # Списание денег
    c.execute("UPDATE users SET money = money - ? WHERE id=?", (price, user[0]))

    # Добавляем в инвентарь
    c.execute("INSERT INTO inventory (user_id, item_name, item_category, purchase_date) VALUES (?, ?, ?, ?)",
              (user[0], item, category, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Покупка успешна'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)