import os
import sys
import functools
from flask import Flask, request, jsonify, render_template, session, redirect, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

def get_now():
    return datetime.now(pytz.timezone("America/Santo_Domingo")).replace(tzinfo=None)

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
ADMIN_USER = os.getenv('ADMIN_USER', 'Admin')
ADMIN_PASS = os.getenv('ADMIN_PASS', 'Dellipizzam&a6508')

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({"error": "No autenticado", "redirect": "/login"}), 401
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

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, default=get_now)
    end_time = db.Column(db.DateTime, nullable=True)
    initial_cash = db.Column(db.Float, default=0.0)
    final_cash = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='open') # 'open', 'closed'
    opened_by = db.Column(db.String(50), default='Usuario')
    closed_by = db.Column(db.String(50), nullable=True)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=get_now)
    price_at_sale = db.Column(db.Float)
    cost_at_sale = db.Column(db.Float, default=0.0)
    quantity = db.Column(db.Integer)
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.id'), nullable=True)

# ── RUTAS ─────────────────────────────────────────
@app.route('/sw.js')
def service_worker():
    return send_from_directory(app.static_folder, 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(app.static_folder, 'manifest.json', mimetype='application/json')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            session['role'] = 'admin'
            return redirect('/')
        elif request.form['username'] == 'Usuario' and request.form['password'] == '6508':
            session['logged_in'] = True
            session['role'] = 'user'
            return redirect('/')
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
@login_required
def index():
    resp = make_response(render_template('index.html', role=session.get('role', 'user')))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

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

@app.route('/api/shifts/active')
@login_required
def get_active_shift():
    active_shift = Shift.query.filter_by(status='open').first()
    if active_shift:
        sales = Sale.query.filter_by(shift_id=active_shift.id).all()
        total_sales = sum(s.price_at_sale for s in sales)
        return jsonify({
            "active": True,
            "id": active_shift.id,
            "start_time": active_shift.start_time.isoformat(),
            "initial_cash": active_shift.initial_cash,
            "opened_by": active_shift.opened_by,
            "total_sales": total_sales,
            "expected_cash": active_shift.initial_cash + total_sales
        })
    return jsonify({"active": False})

@app.route('/api/shifts/open', methods=['POST'])
@login_required
def open_shift():
    active_shift = Shift.query.filter_by(status='open').first()
    if active_shift:
        return jsonify({"error": "Ya hay un turno activo"}), 400
    
    data = request.json or {}
    initial_cash = float(data.get('initial_cash', 0.0))
    
    new_shift = Shift(
        initial_cash=initial_cash,
        opened_by=session.get('role', 'user'),
        status='open',
        start_time=get_now()
    )
    db.session.add(new_shift)
    db.session.commit()
    return jsonify({
        "ok": True,
        "shift": {
            "id": new_shift.id,
            "initial_cash": new_shift.initial_cash,
            "start_time": new_shift.start_time.isoformat()
        }
    })

@app.route('/api/shifts/close', methods=['POST'])
@login_required
def close_shift():
    active_shift = Shift.query.filter_by(status='open').first()
    if not active_shift:
        return jsonify({"error": "No hay ningún turno activo para cerrar"}), 400
    
    data = request.json or {}
    final_cash = float(data.get('final_cash', 0.0))
    
    active_shift.status = 'closed'
    active_shift.end_time = get_now()
    active_shift.final_cash = final_cash
    active_shift.closed_by = session.get('role', 'user')
    
    db.session.commit()
    session.clear()
    return jsonify({"ok": True})

@app.route('/api/shifts/history')
@login_required
def get_shifts_history():
    if session.get('role') != 'admin':
        return jsonify({"error": "No autorizado"}), 403
    
    shifts = Shift.query.order_by(Shift.start_time.desc()).all()
    res = []
    for s in shifts:
        sales = Sale.query.filter_by(shift_id=s.id).all()
        total_sales = sum(s.price_at_sale for s in sales)
        res.append({
            "id": s.id,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "initial_cash": s.initial_cash,
            "final_cash": s.final_cash,
            "status": s.status,
            "opened_by": s.opened_by,
            "closed_by": s.closed_by,
            "total_sales": total_sales,
            "expected_cash": s.initial_cash + total_sales
        })
    return jsonify(res)

@app.route('/api/shifts/<int:shift_id>/sales')
@login_required
def get_shift_sales(shift_id):
    if session.get('role') != 'admin':
        return jsonify({"error": "No autorizado"}), 403
        
    sales = Sale.query.filter(Sale.shift_id == shift_id).order_by(Sale.date.desc()).all()
    grouped_sales = {}
    for s in sales:
        date_str = s.date.isoformat()
        if date_str not in grouped_sales:
            grouped_sales[date_str] = {
                "id": s.id,
                "invoice_number": f"FAC-{str(s.id).zfill(4)}",
                "date": date_str,
                "items": [],
                "total_price": 0,
                "total_cost": 0,
                "total_profit": 0,
                "total_quantity": 0
            }
            
        p = Product.query.get(s.product_id)
        grouped_sales[date_str]["items"].append({
            "product_name": p.name if p else "Producto Eliminado",
            "product_emoji": p.emoji if p else "❓",
            "quantity": s.quantity,
            "price_at_sale": s.price_at_sale,
            "unit_price": p.price if p else (s.price_at_sale / s.quantity)
        })
        grouped_sales[date_str]["total_price"] += s.price_at_sale
        grouped_sales[date_str]["total_cost"] += (s.cost_at_sale or 0)
        grouped_sales[date_str]["total_profit"] += (s.price_at_sale - (s.cost_at_sale or 0))
        grouped_sales[date_str]["total_quantity"] += s.quantity
        
    return jsonify(list(grouped_sales.values()))

@app.route('/api/stats')
@login_required
def stats():
    role = session.get('role', 'user')
    if role == 'user':
        active_shift = Shift.query.filter_by(status='open').first()
        if not active_shift:
            return jsonify({
                "daily_revenue": 0.0,
                "daily_profit": 0.0,
                "daily_count": 0,
                "monthly_profit": 0.0
            })
        shift_sales = Sale.query.filter_by(shift_id=active_shift.id).all()
        profit = sum(s.price_at_sale - (s.cost_at_sale or 0) for s in shift_sales)
        return jsonify({
            "daily_revenue": sum(s.price_at_sale for s in shift_sales),
            "daily_profit": profit,
            "daily_count": len(shift_sales),
            "monthly_profit": profit
        })
    else:
        sales = Sale.query.all()
        today = get_now().date()
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
    active_shift = Shift.query.filter_by(status='open').first()
    if not active_shift:
        return jsonify({"error": "No hay un turno activo. Debes abrir caja primero."}), 400
        
    data = request.json
    prod = Product.query.get(data['product_id'])
    if not prod: return jsonify({"error":"Product not found"}), 404
    
    qty = data.get('quantity', 1)
    total_price = prod.price * qty
    total_cost = (prod.cost_price or 0) * qty
    
    now = get_now()
    s = Sale(
        product_id=prod.id,
        quantity=qty,
        price_at_sale=total_price,
        cost_at_sale=total_cost,
        date=now,
        shift_id=active_shift.id
    )
    db.session.add(s)
    db.session.commit()
    
    return jsonify({
        "id": s.id,
        "invoice_number": f"FAC-{str(s.id).zfill(4)}",
        "date": s.date.isoformat(),
        "total_price": s.price_at_sale,
        "total_cost": s.cost_at_sale,
        "total_profit": s.price_at_sale - s.cost_at_sale,
        "total_quantity": s.quantity,
        "items": [{
            "product_name": prod.name,
            "product_emoji": prod.emoji,
            "quantity": s.quantity,
            "price_at_sale": s.price_at_sale,
            "unit_price": prod.price
        }]
    })

@app.route('/api/sales/batch', methods=['POST'])
def add_sale_batch():
    active_shift = Shift.query.filter_by(status='open').first()
    if not active_shift:
        return jsonify({"error": "No hay un turno activo. Debes abrir caja primero."}), 400
        
    items_data = request.json.get('items', [])
    if not items_data:
        return jsonify({"error": "No items"}), 400
        
    now = get_now()
    sales_created = []
    
    for item in items_data:
        prod = Product.query.get(item['product_id'])
        if not prod: continue
        qty = item.get('quantity', 1)
        
        s = Sale(
            product_id=prod.id,
            quantity=qty,
            price_at_sale=prod.price * qty,
            cost_at_sale=(prod.cost_price or 0) * qty,
            date=now,
            shift_id=active_shift.id
        )
        db.session.add(s)
        sales_created.append((s, prod))
        
    db.session.commit()
    
    if not sales_created:
        return jsonify({"error": "No valid items"}), 400
        
    first_sale = sales_created[0][0]
    
    resp_items = []
    total_price = 0
    total_cost = 0
    total_qty = 0
    
    for s, prod in sales_created:
        total_price += s.price_at_sale
        total_cost += s.cost_at_sale
        total_qty += s.quantity
        resp_items.append({
            "product_name": prod.name,
            "product_emoji": prod.emoji,
            "quantity": s.quantity,
            "price_at_sale": s.price_at_sale,
            "unit_price": prod.price
        })
        
    return jsonify({
        "id": first_sale.id,
        "invoice_number": f"FAC-{str(first_sale.id).zfill(4)}",
        "date": first_sale.date.isoformat(),
        "total_price": total_price,
        "total_cost": total_cost,
        "total_profit": total_price - total_cost,
        "total_quantity": total_qty,
        "items": resp_items
    })

@app.route('/api/sales/history')
@login_required
def sales_history():
    period = request.args.get('period', 'today')
    pid = request.args.get('product_id', 'all')
    
    role = session.get('role', 'user')
    if role == 'user':
        active_shift = Shift.query.filter_by(status='open').first()
        if not active_shift:
            return jsonify([])
        query = Sale.query.filter(Sale.shift_id == active_shift.id)
    else:
        query = Sale.query
        now = get_now()
        
        if period == 'today':
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            query = query.filter(Sale.date >= start_of_day, Sale.date < end_of_day)
        elif period == 'week':
            week_ago = now - timedelta(days=7)
            query = query.filter(Sale.date >= week_ago)
        elif period == 'month':
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Sale.date >= start_of_month)
        # elif period == 'all': no filter — return everything
        
    if pid != 'all':
        # Encontrar las fechas que contienen este producto
        dates_with_product = [s.date for s in query.filter(Sale.product_id == int(pid)).all()]
        if not dates_with_product:
            return jsonify([])
        query = query.filter(Sale.date.in_(dates_with_product))

    sales = query.order_by(Sale.date.desc()).all()
    
    grouped_sales = {}
    for s in sales:
        date_str = s.date.isoformat()
        if date_str not in grouped_sales:
            grouped_sales[date_str] = {
                "id": s.id,
                "invoice_number": f"FAC-{str(s.id).zfill(4)}",
                "date": date_str,
                "items": [],
                "total_price": 0,
                "total_cost": 0,
                "total_profit": 0,
                "total_quantity": 0
            }
            
        p = Product.query.get(s.product_id)
        grouped_sales[date_str]["items"].append({
            "product_name": p.name if p else "Producto Eliminado",
            "product_emoji": p.emoji if p else "❓",
            "quantity": s.quantity,
            "price_at_sale": s.price_at_sale,
            "unit_price": p.price if p else (s.price_at_sale / s.quantity)
        })
        grouped_sales[date_str]["total_price"] += s.price_at_sale
        grouped_sales[date_str]["total_cost"] += (s.cost_at_sale or 0)
        grouped_sales[date_str]["total_profit"] += (s.price_at_sale - (s.cost_at_sale or 0))
        grouped_sales[date_str]["total_quantity"] += s.quantity
        
    return jsonify(list(grouped_sales.values()))

@app.route('/api/sales/<int:id>', methods=['DELETE'])
def void_sale(id):
    s = Sale.query.get_or_404(id)
    sales_to_delete = Sale.query.filter_by(date=s.date).all()
    for sale in sales_to_delete:
        db.session.delete(sale)
    db.session.commit()
    return jsonify({"ok":True})

# ── INIT ──────────────────────────────────────────
with app.app_context():
    # Creamos las tablas de forma segura (sin borrar nada)
    db.create_all()

    # Migración automática: agregar shift_id a sale si no existe (SQLite no la tiene con ALTER TABLE en versiones viejas)
    try:
        inspector = db.inspect(db.engine)
        existing_cols = [col['name'] for col in inspector.get_columns('sale')]
        if 'shift_id' not in existing_cols:
            print("⚙️  Migrando esquema: añadiendo columna shift_id a la tabla sale...")
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE sale ADD COLUMN shift_id INTEGER REFERENCES shift(id)"))
                conn.commit()
            print("✅ Migración completada.")
    except Exception as e:
        print(f"⚠️  Error en migración de shift_id: {e}")

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