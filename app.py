import os
import sys
import urllib.parse
import functools
from flask import Flask, request, jsonify, render_template, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── RUTAS PARA .EXE Y DESARROLLO ──────────────────────────────────────────────
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # cuando es .exe
    except Exception:
        base_path = os.path.abspath(".")  # desarrollo
    return os.path.join(base_path, relative_path)

def data_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")

# ── APP ───────────────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static")
)
app.config['SECRET_KEY'] = 'dp-ma-s3cr3t-2026-xK9'

# ── CREDENCIALES ────────────────────────────────────────────────────────────────────────
ADMIN_USER = os.getenv('ADMIN_USER', 'alexander2026MA')
ADMIN_PASS = os.getenv('ADMIN_PASS', '12345MMAA')

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

# ── BASE DE DATOS (SQL Server) ────────────────────────────────────────────────
DB_SERVER = os.getenv('DB_SERVER', 'ALEXANDER')
DB_NAME   = os.getenv('DB_NAME',   'delipizza')
DB_USER   = os.getenv('DB_USER',   'delipizza')
DB_PASS   = os.getenv('DB_PASSWORD', '123456789')
DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')

_driver_enc = urllib.parse.quote_plus(
    f"DRIVER={{{DB_DRIVER}}};SERVER={DB_SERVER};DATABASE={DB_NAME};"
    f"UID={DB_USER};PWD={DB_PASS};TrustServerCertificate=yes;"
)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={_driver_enc}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── CATEGORÍAS ────────────────────────────────────────────────────────────────
CAT_MAP = {
    'pizza': 'Pizza', 'pizzas': 'Pizza',
    'papas': 'Papas', 'papa': 'Papas', 'fries': 'Papas',
    'bebidas': 'Bebidas', 'bebida': 'Bebidas', 'drink': 'Bebidas',
    'sandwich': 'Sandwich', 'sandwitch': 'Sandwich', 'sandwiches': 'Sandwich',
    'nuggets': 'Nuggets', 'nugget': 'Nuggets',
}
VALID_CATS = {'Pizza', 'Papas', 'Bebidas', 'Sandwich', 'Nuggets'}

def normalize_category(cat):
    if not cat:
        return 'Pizza'
    key = cat.strip().lower()
    if key in CAT_MAP:
        return CAT_MAP[key]
    if cat.strip() in VALID_CATS:
        return cat.strip()
    return 'Pizza'

# ── MODELOS ───────────────────────────────────────────────────────────────────
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.Unicode(50), default='Pizza')
    emoji = db.Column(db.Unicode(10), default='🍕')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'category': self.category,
            'emoji': self.emoji
        }

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    price_at_sale = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)

    product = db.relationship('Product')

    def to_dict(self):
        unit_price = round(self.price_at_sale / self.quantity, 2) if self.quantity else self.price_at_sale
        return {
            'id': self.id,
            'invoice_number': f'FAC-{self.id:04d}',
            'product_name': self.product.name if self.product else 'Eliminado',
            'product_emoji': self.product.emoji if self.product else '❓',
            'product_category': self.product.category if self.product else '—',
            'product_id': self.product_id,
            'date': self.date.isoformat(),
            'price_at_sale': self.price_at_sale,
            'unit_price': unit_price,
            'quantity': self.quantity
        }

# ── RUTAS ─────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect('/')
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            session['username'] = username
            return redirect('/')
        error = 'Usuario o contraseña incorrectos'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# PRODUCTOS
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify([p.to_dict() for p in Product.query.all()])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    p = Product(
        name=data['name'],
        price=float(data['price']),
        category=normalize_category(data.get('category')),
        emoji=data.get('emoji', '🍕')
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict())

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    p = Product.query.get_or_404(id)
    data = request.json
    p.name = data.get('name', p.name)
    p.price = float(data.get('price', p.price))
    p.category = normalize_category(data.get('category', p.category))
    p.emoji = data.get('emoji', p.emoji)
    db.session.commit()
    return jsonify(p.to_dict())

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    p = Product.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'ok': True})

# VENTAS
@app.route('/api/sales', methods=['POST'])
def add_sale():
    data = request.json
    p = Product.query.get(data['product_id'])
    qty = int(data.get('quantity', 1))
    s = Sale(product_id=p.id, price_at_sale=p.price * qty, quantity=qty)
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict())

@app.route('/api/sales/<int:id>', methods=['DELETE'])
def delete_sale(id):
    s = Sale.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/stats', methods=['GET'])
def stats():
    today = datetime.now().date()
    sales = Sale.query.all()

    daily_sales = [s for s in sales if s.date.date() == today]
    daily_profit = sum(s.price_at_sale for s in daily_sales)
    daily_count = len(daily_sales)
    monthly_profit = sum(s.price_at_sale for s in sales if s.date.month == today.month and s.date.year == today.year)

    return jsonify({
        "daily_profit": daily_profit,
        "daily_count": daily_count,
        "monthly_profit": monthly_profit,
        # backward compat
        "daily": daily_profit,
        "monthly": monthly_profit
    })

@app.route('/api/sales/history', methods=['GET'])
def sales_history():
    period = request.args.get('period', 'today')
    product_id = request.args.get('product_id', None)
    now = datetime.now()
    today = now.date()

    sales = Sale.query.order_by(Sale.date.desc()).all()

    if period == 'today':
        filtered = [s for s in sales if s.date.date() == today]
    elif period == 'week':
        week_ago = today - timedelta(days=7)
        filtered = [s for s in sales if s.date.date() >= week_ago]
    elif period == 'month':
        filtered = [s for s in sales if s.date.month == today.month and s.date.year == today.year]
    else:
        filtered = sales

    if product_id and product_id != 'all':
        filtered = [s for s in filtered if s.product_id == int(product_id)]

    return jsonify([s.to_dict() for s in filtered])

# ── INIT ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5001, debug=True)