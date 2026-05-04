import os
import sys
import functools
from flask import Flask, request, jsonify, render_template, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── RUTAS ─────────────────────────────────────────
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ── APP ───────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static")
)

app.config['SECRET_KEY'] = 'dp-ma-secret'

# ── BASE DE DATOS ──────────────────────────────────
# En Render, usar DATABASE_URL (PostgreSQL), sino SQLite local
db_url = os.getenv('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if not db_url:
    db_path = os.path.join(os.path.abspath("."), "delipizza.db")
    db_url = f"sqlite:///{db_path}"

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── CONFIG ─────────────────────────────────────────
ADMIN_USER = os.getenv('ADMIN_USER', 'alexander2026MA')
ADMIN_PASS = os.getenv('ADMIN_PASS', '12345MMAA')

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

# ── MODELOS ───────────────────────────────────────
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    category = db.Column(db.String(50))
    emoji = db.Column(db.String(10))

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.now)
    price_at_sale = db.Column(db.Float)
    quantity = db.Column(db.Integer)

# ── RUTAS ─────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect('/')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# PRODUCTOS
@app.route('/api/products')
def products():
    return jsonify([{
        "id":p.id,"name":p.name,"price":p.price,"category":p.category,"emoji":p.emoji
    } for p in Product.query.all()])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    p = Product(**data)
    db.session.add(p)
    db.session.commit()
    return jsonify({"ok":True})

@app.route('/api/stats')
def stats():
    sales = Sale.query.all()
    today = datetime.now().date()
    daily_sales = [s for s in sales if s.date.date() == today]
    
    return jsonify({
        "daily_profit": sum(s.price_at_sale for s in daily_sales),
        "daily_count": len(daily_sales),
        "monthly_profit": sum(s.price_at_sale for s in sales if s.date.month == today.month and s.date.year == today.year)
    })

# --- PRODUCTOS (EXTENDIDO) ---
@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    p = Product.query.get_or_404(id)
    data = request.json
    p.name = data.get('name', p.name)
    p.price = data.get('price', p.price)
    p.category = data.get('category', p.category)
    p.emoji = data.get('emoji', p.emoji)
    db.session.commit()
    return jsonify({"ok":True})

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    p = Product.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"ok":True})

# --- VENTAS (EXTENDIDO) ---
@app.route('/api/sales', methods=['POST'])
def add_sale():
    data = request.json
    prod = Product.query.get(data['product_id'])
    if not prod: return jsonify({"error":"Product not found"}), 404
    
    qty = data.get('quantity', 1)
    total = prod.price * qty
    
    s = Sale(
        product_id=prod.id,
        quantity=qty,
        price_at_sale=total
    )
    db.session.add(s)
    db.session.commit()
    
    # Return full data for the invoice modal
    return jsonify({
        "id": s.id,
        "invoice_number": f"FAC-{str(s.id).padStart(4,'0')}",
        "product_name": prod.name,
        "product_emoji": prod.emoji,
        "quantity": s.quantity,
        "price_at_sale": s.price_at_sale,
        "date": s.date.isoformat(),
        "unit_price": prod.price
    })

@app.route('/api/sales/history')
def sales_history():
    period = request.args.get('period', 'today')
    pid = request.args.get('product_id', 'all')
    
    query = Sale.query
    now = datetime.now()
    
    if period == 'today':
        query = query.filter(db.func.date(Sale.date) == now.date())
    elif period == 'week':
        week_ago = now - timedelta(days=7)
        query = query.filter(Sale.date >= week_ago)
    elif period == 'month':
        query = query.filter(db.func.extract('month', Sale.date) == now.month)
        
    if pid != 'all':
        query = query.filter(Sale.product_id == int(pid))

    sales = query.order_by(Sale.date.desc()).all()
    
    results = []
    for s in sales:
        p = Product.query.get(s.product_id)
        results.append({
            "id": s.id,
            "product_name": p.name if p else "Producto Eliminado",
            "product_emoji": p.emoji if p else "❓",
            "date": s.date.isoformat(),
            "quantity": s.quantity,
            "price_at_sale": s.price_at_sale,
            "invoice_number": f"FAC-{str(s.id).padStart(4,'0')}"
        })
    return jsonify(results)

@app.route('/api/sales/<int:id>', methods=['DELETE'])
def void_sale(id):
    s = Sale.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({"ok":True})

# ── INIT ──────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))