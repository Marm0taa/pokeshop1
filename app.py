from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3, hashlib, os, json

app = Flask(__name__)
app.secret_key = 'pokeshop_secret_2024'
DB = 'pokeshop.db'

# ── Base de datos ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT    UNIQUE NOT NULL,
                email     TEXT    UNIQUE NOT NULL,
                password  TEXT    NOT NULL,
                created   DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS orders (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                items      TEXT    NOT NULL,
                total      REAL    NOT NULL,
                created    DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── Helpers ────────────────────────────────────────────────────
def get_cart():
    return session.get('cart', [])

def save_cart(cart):
    session['cart'] = cart

def cart_total(cart):
    return round(sum(float(i['price']) * int(i['qty']) for i in cart), 2)

# ── Rutas públicas ─────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', user=session.get('user'))

@app.route('/catalog')
def catalog():
    return render_template('catalog.html', user=session.get('user'))

# ── Auth ───────────────────────────────────────────────────────
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template('register.html')
        try:
            with get_db() as db:
                db.execute('INSERT INTO users (username,email,password) VALUES (?,?,?)',
                           (username, email, hash_pw(password)))
            flash('¡Cuenta creada! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('El usuario o correo ya está en uso.', 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        with get_db() as db:
            user = db.execute(
                'SELECT * FROM users WHERE username=? AND password=?',
                (username, hash_pw(password))
            ).fetchone()
        if user:
            session['user'] = {'id': user['id'], 'username': user['username']}
            flash(f'¡Bienvenido, {user["username"]}!', 'success')
            return redirect(url_for('catalog'))
        flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ── Carrito (API JSON) ─────────────────────────────────────────
@app.route('/api/cart', methods=['GET'])
def api_cart_get():
    cart = get_cart()
    return jsonify({'items': cart, 'total': cart_total(cart), 'count': sum(i['qty'] for i in cart)})

@app.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    data  = request.get_json()
    cart  = get_cart()
    card_id = data['id']
    for item in cart:
        if item['id'] == card_id:
            item['qty'] += 1
            save_cart(cart)
            return jsonify({'ok': True, 'count': sum(i['qty'] for i in cart)})
    cart.append({'id': card_id, 'name': data['name'],
                 'image': data['image'], 'price': data['price'], 'qty': 1})
    save_cart(cart)
    return jsonify({'ok': True, 'count': sum(i['qty'] for i in cart)})

@app.route('/api/cart/remove', methods=['POST'])
def api_cart_remove():
    data  = request.get_json()
    cart  = [i for i in get_cart() if i['id'] != data['id']]
    save_cart(cart)
    return jsonify({'ok': True, 'count': sum(i['qty'] for i in cart)})

@app.route('/api/cart/update', methods=['POST'])
def api_cart_update():
    data = request.get_json()
    cart = get_cart()
    for item in cart:
        if item['id'] == data['id']:
            item['qty'] = max(1, int(data['qty']))
    save_cart(cart)
    return jsonify({'ok': True, 'total': cart_total(cart)})

@app.route('/api/cart/clear', methods=['POST'])
def api_cart_clear():
    save_cart([])
    return jsonify({'ok': True})

# ── Checkout ───────────────────────────────────────────────────
@app.route('/checkout', methods=['GET','POST'])
def checkout():
    if not session.get('user'):
        flash('Debes iniciar sesión para comprar.', 'error')
        return redirect(url_for('login'))
    cart = get_cart()
    if not cart:
        return redirect(url_for('catalog'))
    if request.method == 'POST':
        with get_db() as db:
            db.execute('INSERT INTO orders (user_id,items,total) VALUES (?,?,?)',
                       (session['user']['id'], json.dumps(cart), cart_total(cart)))
        save_cart([])
        flash('¡Pedido confirmado! Gracias por tu compra.', 'success')
        return redirect(url_for('order_success'))
    return render_template('checkout.html', cart=cart, total=cart_total(cart), user=session.get('user'))

@app.route('/order-success')
def order_success():
    return render_template('order_success.html', user=session.get('user'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
