import sys
from sqlalchemy import create_engine, MetaData, Table, select, delete, insert, text

OLD_DB_URL = "postgresql://delipizza_db_user:RLMKwMJ1VyhZUI465Prc06yixwrO7GZy@dpg-d7sgonlckfvc73chm8ng-a.oregon-postgres.render.com/delipizza_db"
NEW_DB_URL = "postgresql://postgres:felixalexanderdatabas@db.siwircszmgopgwiixldl.supabase.co:5432/postgres"

def migrate():
    print("🚀 Iniciando la migración de datos de Render a Supabase...")
    
    # Crear conexiones
    try:
        old_engine = create_engine(OLD_DB_URL)
        new_engine = create_engine(NEW_DB_URL)
        print("✅ Conexiones a las bases de datos creadas.")
    except Exception as e:
        print(f"❌ Error al conectar a las bases de datos: {e}")
        sys.exit(1)
        
    # Cargar metadatos
    old_metadata = MetaData()
    new_metadata = MetaData()
    
    try:
        old_metadata.reflect(bind=old_engine)
        new_metadata.reflect(bind=new_engine)
        print("✅ Estructura (tablas) leída correctamente de ambas bases de datos.")
    except Exception as e:
        print(f"❌ Error al leer la estructura de las tablas: {e}")
        sys.exit(1)
        
    # Verificar las tablas requeridas
    tables_to_migrate = ["product", "sale"]
    for table_name in tables_to_migrate:
        if table_name not in old_metadata.tables:
            print(f"❌ La tabla '{table_name}' no existe en la base de datos origen.")
            sys.exit(1)
        if table_name not in new_metadata.tables:
            print(f"❌ La tabla '{table_name}' no existe en la base de datos destino.")
            sys.exit(1)
            
    # Iniciar la transferencia de datos
    with old_engine.connect() as old_conn:
        with new_engine.begin() as new_conn:
            # 1. Limpiar datos de demostración previamente creados en Supabase para evitar conflictos
            print("\n🧹 Limpiando tablas temporales de Supabase antes de la migración...")
            for table_name in reversed(tables_to_migrate):
                table = new_metadata.tables[table_name]
                new_conn.execute(delete(table))
            print("✅ Limpieza completada.")
            
            # 2. Migrar en orden de dependencias: category -> product -> sale
            for table_name in tables_to_migrate:
                print(f"\n📦 Migrando datos de la tabla '{table_name}'...")
                old_table = old_metadata.tables[table_name]
                new_table = new_metadata.tables[table_name]
                
                # Leer registros
                records = old_conn.execute(select(old_table)).fetchall()
                print(f"📊 Encontrados {len(records)} registros en Render.")
                
                if not records:
                    print(f"⏭️ La tabla '{table_name}' está vacía. Saltando inserción.")
                    continue
                    
                # Convertir a lista de diccionarios para inserción masiva
                data_to_insert = [dict(row._mapping) for row in records]
                
                # Insertar en la nueva base de datos
                new_conn.execute(insert(new_table), data_to_insert)
                print(f"✨ Insertados {len(data_to_insert)} registros en Supabase con éxito.")
                
                # 3. Restablecer la secuencia del ID autoincremental en PostgreSQL
                # Esto es crucial para que los nuevos registros que cree el usuario no den error de clave duplicada
                seq_query = f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM {table_name};"
                new_conn.execute(text(seq_query))
                print(f"🔄 Secuencia del ID para '{table_name}' reajustada correctamente.")
                
    print("\n🎉 ¡Felicidades! Migración completada con éxito sin perder ningún dato.")

if __name__ == "__main__":
    migrate()
