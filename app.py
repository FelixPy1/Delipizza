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
# En Render no usamos resource_path para evitar problemas con gunicorn
if os.environ.get("RENDER"):
    app = Flask(__name__)
else:
    app = Flask(
        __name__,
        template_folder=resource_path("templates"),
        static_folder=resource_path("static")
    )

app.config['SECRET_KEY'] = 'dp-ma-secret'

# ── BASE DE DATOS ──────────────────────────────────
db_url = os.environ.get('DATABASE_URL')

if db_url:
    # Limpiar espacios y corregir prefijo
    db_url = db_url.strip()
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    print(f"🔗 Intentando conectar a: {db_url.split('@')[-1]}") # Solo mostramos el host por seguridad
else:
    db_path = os.path.join(os.path.abspath("."), "delipizza.db")
    db_url = f"sqlite:///{db_path}"
    print("🏠 Usando base de datos local (SQLite)")

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Forzar a SQLAlchemy a usar un pool de conexiones más estable
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

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
    cost_price = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(50))
    emoji = db.Column(db.String(10))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    emoji = db.Column(db.String(10))

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.now)
    price_at_sale = db.Column(db.Float)
    cost_at_sale = db.Column(db.Float, default=0.0)
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

# CATEGORIAS
@app.route('/api/categories')
def get_categories():
    return jsonify([{
        "id": c.id, "name": c.name, "emoji": c.emoji
    } for c in Category.query.all()])

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.json
    if Category.query.filter_by(name=data['name']).first():
        return jsonify({"error": "La categoría ya existe"}), 400
    c = Category(name=data['name'], emoji=data.get('emoji', '📁'))
    db.session.add(c)
    db.session.commit()
    return jsonify({"ok": True})

@app.route('/api/categories/<int:id>', methods=['PUT'])
def update_category(id):
    c = Category.query.get_or_404(id)
    data = request.json
    old_name = c.name
    new_name = data.get('name', c.name)
    
    # Si cambió el nombre, actualizamos los productos
    if old_name != new_name:
        products = Product.query.filter_by(category=old_name).all()
        for p in products:
            p.category = new_name
            
    c.name = new_name
    c.emoji = data.get('emoji', c.emoji)
    db.session.commit()
    return jsonify({"ok": True})

@app.route('/api/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    c = Category.query.get_or_404(id)
    name = c.name
    
    # Actualizar productos a 'General' (o Pizza si prefieres) para que no queden huérfanos
    products = Product.query.filter_by(category=name).all()
    for p in products:
        p.category = 'General'
        
    db.session.delete(c)
    db.session.commit()
    return jsonify({"ok": True})

# PRODUCTOS
@app.route('/api/products')
def products():
    return jsonify([{
        "id":p.id,"name":p.name,"price":p.price,"cost_price":p.cost_price,"category":p.category,"emoji":p.emoji
    } for p in Product.query.all()])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    p = Product(
        name=data['name'],
        price=data['price'],
        cost_price=data.get('cost_price', 0),
        category=data.get('category', 'Pizza'),
        emoji=data.get('emoji', '🍕')
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"ok":True})

@app.route('/api/stats')
def stats():
    sales = Sale.query.all()
    today = datetime.now().date()
    daily_sales = [s for s in sales if s.date.date() == today]
    
    daily_profit = sum(s.price_at_sale - (s.cost_at_sale or 0) for s in daily_sales)
    monthly_profit = sum(s.price_at_sale - (s.cost_at_sale or 0) for s in sales if s.date.month == today.month and s.date.year == today.year)
    
    return jsonify({
        "daily_revenue": sum(s.price_at_sale for s in daily_sales),
        "daily_profit": daily_profit,
        "daily_count": len(daily_sales),
        "monthly_profit": monthly_profit
    })

# --- PRODUCTOS (EXTENDIDO) ---
@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    p = Product.query.get_or_404(id)
    data = request.json
    p.name = data.get('name', p.name)
    p.price = data.get('price', p.price)
    p.cost_price = data.get('cost_price', p.cost_price)
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
    total_price = prod.price * qty
    total_cost = (prod.cost_price or 0) * qty
    
    s = Sale(
        product_id=prod.id,
        quantity=qty,
        price_at_sale=total_price,
        cost_at_sale=total_cost
    )
    db.session.add(s)
    db.session.commit()
    
    # Return full data for the invoice modal
    return jsonify({
        "id": s.id,
        "invoice_number": f"FAC-{str(s.id).zfill(4)}",
        "product_name": prod.name,
        "product_emoji": prod.emoji,
        "quantity": s.quantity,
        "price_at_sale": s.price_at_sale,
        "cost_at_sale": s.cost_at_sale,
        "profit_at_sale": s.price_at_sale - s.cost_at_sale,
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
            "cost_at_sale": s.cost_at_sale,
            "profit_at_sale": s.price_at_sale - (s.cost_at_sale or 0),
            "invoice_number": f"FAC-{str(s.id).zfill(4)}"
        })
    return jsonify(results)

@app.route('/api/sales/<int:id>', methods=['DELETE'])
def void_sale(id):
    s = Sale.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({"ok":True})

# ── INIT ──────────────────────────────────────────
with app.app_context():
    # Creamos las tablas de forma segura (sin borrar nada)
    db.create_all()

    # Semilla de categorías si está vacío
    try:
        if Category.query.count() == 0:
            print("Sembrando categorías iniciales...")
            cats = [
                Category(name="Pizza", emoji="🍕"),
                Category(name="Papas", emoji="🍟"),
                Category(name="Bebidas", emoji="🥤"),
                Category(name="Sandwich", emoji="🥪"),
                Category(name="Nuggets", emoji="🍗")
            ]
            db.session.add_all(cats)
            db.session.commit()
    except Exception as e:
        print(f"Error sembrando categorías: {e}")
        db.session.rollback()

    # Semilla de productos (solo si está vacío)
    try:
        if Product.query.count() == 0:
            print("Sembrando datos iniciales...")
            p1 = Product(name="Pizza Pepperoni", price=500, cost_price=350, category="Pizza", emoji="🍕")
            p2 = Product(name="Papas Fritas", price=150, cost_price=80, category="Papas", emoji="🍟")
            p3 = Product(name="Refresco 16oz", price=75, cost_price=40, category="Bebidas", emoji="🥤")
            db.session.add_all([p1, p2, p3])
            db.session.commit()
    except Exception as e:
        print(f"Error sembrando productos: {e}")
        db.session.rollback()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)