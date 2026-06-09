import os
import unittest
import json
from datetime import datetime

# Asegurar que usamos base de datos SQLite de prueba
os.environ['DATABASE_URL'] = 'sqlite:///test_delipizza.db'

from app import app, db, Shift, Sale, Product, Category

class ShiftSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Crear tablas limpias
        db.create_all()
        
        # Crear datos de prueba iniciales
        self.category = Category(name="TestCat", emoji="🍕")
        self.product = Product(name="Pizza Test", price=500.0, cost_price=200.0, category="TestCat", emoji="🍕")
        db.session.add(self.category)
        db.session.add(self.product)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        # Eliminar archivo de db de pruebas
        if os.path.exists('test_delipizza.db'):
            try:
                os.remove('test_delipizza.db')
            except OSError:
                pass

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_shift_flow(self):
        # 1. Intentar registrar una venta sin turno abierto (debe retornar 400)
        res = self.app.post('/api/sales', json={"product_id": self.product.id, "quantity": 1})
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertIn("Debes abrir caja primero", data["error"])

        # Iniciar sesión como vendedor/Usuario
        self.login('Usuario', '6508')

        # 2. Intentar registrar venta con sesión iniciada pero SIN turno abierto (debe retornar 400)
        res = self.app.post('/api/sales', json={"product_id": self.product.id, "quantity": 1})
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertIn("Debes abrir caja primero", data["error"])

        # 3. Consultar turno activo (debe retornar active: False)
        res = self.app.get('/api/shifts/active')
        data = json.loads(res.data)
        self.assertFalse(data["active"])

        # 4. Abrir un turno con caja inicial de $1000
        res = self.app.post('/api/shifts/open', json={"initial_cash": 1000.00})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["ok"])
        self.assertEqual(data["shift"]["initial_cash"], 1000.00)

        # 5. Volver a consultar turno activo (debe retornar active: True)
        res = self.app.get('/api/shifts/active')
        data = json.loads(res.data)
        self.assertTrue(data["active"])
        self.assertEqual(data["initial_cash"], 1000.00)
        self.assertEqual(data["total_sales"], 0.0)

        # 6. Registrar una venta de 2 pizzas
        res = self.app.post('/api/sales', json={"product_id": self.product.id, "quantity": 2})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["total_price"], 1000.0)

        # 7. Consultar turno activo nuevamente (debe mostrar total_sales: $1000, expected: $2000)
        res = self.app.get('/api/shifts/active')
        data = json.loads(res.data)
        self.assertEqual(data["total_sales"], 1000.00)
        self.assertEqual(data["expected_cash"], 2000.00)

        # 8. Consultar historial como vendedor (debe mostrar la venta)
        res = self.app.get('/api/sales/history')
        data = json.loads(res.data)
        self.assertEqual(len(data), 1)

        # 9. Cerrar turno ingresando caja final de $2000
        res = self.app.post('/api/shifts/close', json={"final_cash": 2000.00})
        self.assertEqual(res.status_code, 200)
        
        # Al cerrar turno, la sesión se limpia. Iniciamos sesión de nuevo para comprobar
        self.login('Usuario', '6508')

        # 10. Consultar historial como vendedor ahora que el turno está cerrado (debe mostrar 0 ventas)
        res = self.app.get('/api/sales/history')
        data = json.loads(res.data)
        self.assertEqual(len(data), 0)

        # 11. Iniciar sesión como Administrador
        self.app.get('/logout') # limpiar sesión
        self.login('Admin', 'Dellipizzam&a6508')

        # 12. Consultar historial como Administrador (debe mostrar la venta del turno cerrado)
        res = self.app.get('/api/sales/history')
        data = json.loads(res.data)
        self.assertEqual(len(data), 1)

        # 13. Consultar historial de turnos como Administrador
        res = self.app.get('/api/shifts/history')
        data = json.loads(res.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["status"], "closed")
        self.assertEqual(data[0]["initial_cash"], 1000.00)
        self.assertEqual(data[0]["final_cash"], 2000.00)
        self.assertEqual(data[0]["total_sales"], 1000.00)

        # 14. Consultar ventas asociadas a este turno específico como Administrador
        shift_id = data[0]["id"]
        res = self.app.get(f'/api/shifts/{shift_id}/sales')
        self.assertEqual(res.status_code, 200)
        sales_data = json.loads(res.data)
        self.assertEqual(len(sales_data), 1)
        self.assertEqual(sales_data[0]["invoice_number"], f"FAC-{str(sales_data[0]['id']).zfill(4)}")
        self.assertEqual(sales_data[0]["total_price"], 1000.00)
        self.assertEqual(sales_data[0]["items"][0]["product_name"], "Pizza Test")

        # 15. Consultar ventas de turno específico como Vendedor ordinario (debe fallar con 403)
        self.app.get('/logout') # limpiar admin
        self.login('Usuario', '6508')
        res = self.app.get(f'/api/shifts/{shift_id}/sales')
        self.assertEqual(res.status_code, 403)

if __name__ == '__main__':
    unittest.main()
