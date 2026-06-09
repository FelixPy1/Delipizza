import sqlite3
import psycopg2
from datetime import datetime

SQLITE_DB = "delipizza.db"
SUPABASE_URL = "postgresql://postgres:felixalexanderdatabas@db.siwircszmgopgwiixldl.supabase.co:5432/postgres"

def sync():
    print("🔄 Iniciando sincronización de SQLite local a Supabase...")

    # Conectar a SQLite
    try:
        conn_sq = sqlite3.connect(SQLITE_DB)
        cur_sq = conn_sq.cursor()
        print("✅ Conectado a SQLite local.")
    except Exception as e:
        print(f"❌ Error al conectar a SQLite: {e}")
        return

    # Conectar a Supabase
    try:
        conn_sb = psycopg2.connect(SUPABASE_URL)
        cur_sb = conn_sb.cursor()
        print("✅ Conectado a Supabase.")
    except Exception as e:
        print(f"❌ Error al conectar a Supabase: {e}")
        conn_sq.close()
        return

    try:
        # 1. CATEGORÍAS
        print("\n📂 Sincronizando categorías...")
        cur_sq.execute("SELECT id, name, emoji FROM category")
        local_categories = cur_sq.fetchall()

        for cid, name, emoji in local_categories:
            print(f"  📥 Procesando categoría: {name} ({emoji}) con ID {cid}")
            cur_sb.execute(
                """
                INSERT INTO category (id, name, emoji) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (id) DO NOTHING
                """,
                (cid, name, emoji)
            )

        # Ajustar secuencia de ID de categorías
        cur_sb.execute("SELECT setval(pg_get_serial_sequence('category', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM category;")
        print("  🔄 Secuencia de categorías actualizada.")

        # 2. PRODUCTOS
        print("\n🍕 Sincronizando productos...")
        cur_sq.execute("SELECT id, name, price, cost_price, category, emoji FROM product")
        local_products = cur_sq.fetchall()

        for pid, name, price, cost_price, category, emoji in local_products:
            print(f"  📥 Procesando producto: {name} con ID {pid}")
            cur_sb.execute(
                """
                INSERT INTO product (id, name, price, cost_price, category, emoji) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                ON CONFLICT (id) DO NOTHING
                """,
                (pid, name, price, cost_price, category, emoji)
            )

        # Ajustar secuencia de ID de productos
        cur_sb.execute("SELECT setval(pg_get_serial_sequence('product', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM product;")
        print("  🔄 Secuencia de productos actualizada.")

        # 3. VENTAS (SALES)
        print("\n🧾 Sincronizando ventas...")
        cur_sq.execute("SELECT id, product_id, date, price_at_sale, cost_at_sale, quantity FROM sale")
        local_sales = cur_sq.fetchall()

        for sid, product_id, sdate, price_at_sale, cost_at_sale, quantity in local_sales:
            print(f"  📥 Procesando venta ID {sid}: Producto {product_id}, Cantidad {quantity}")
            # Parsear fecha de sqlite
            try:
                dt = datetime.strptime(sdate, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                dt = datetime.strptime(sdate, "%Y-%m-%d %H:%M:%S")
            
            cur_sb.execute(
                """
                INSERT INTO sale (id, product_id, date, price_at_sale, cost_at_sale, quantity) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                ON CONFLICT (id) DO NOTHING
                """,
                (sid, product_id, dt, price_at_sale, cost_at_sale, quantity)
            )

        # Ajustar secuencia de ID de ventas
        cur_sb.execute("SELECT setval(pg_get_serial_sequence('sale', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM sale;")
        print("  🔄 Secuencia de ventas actualizada.")

        # Confirmar los cambios
        conn_sb.commit()
        print("\n🎉 ¡Sincronización completada con éxito!")

    except Exception as e:
        conn_sb.rollback()
        print(f"\n❌ Error durante la sincronización: {e}")
    finally:
        conn_sq.close()
        conn_sb.close()

if __name__ == "__main__":
    sync()
