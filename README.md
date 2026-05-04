# 🍕 Deli-Pizza M&A — Sistema de Gestión

Sistema de punto de venta y gestión diseñado para la pizzería **Deli-Pizza M&A**. Funciona como una aplicación de escritorio con ventana nativa (sin necesidad de abrir el navegador manualmente).

---

## 🚀 Cómo abrir la app

1. Ve al escritorio de Windows.
2. Haz doble clic en el acceso directo **"Deli-Pizza M&A"**.
3. La app abre automáticamente su propia ventana — no necesitas instalar nada más.

> ⚠️ **Importante:** Si en algún momento mueves la carpeta `dist\DeliPizza\`, el acceso directo dejará de funcionar. En ese caso, crea uno nuevo apuntando al nuevo `DeliPizza.exe`.

---

## 🗂️ Secciones de la App

La app tiene 4 secciones accesibles desde el menú lateral izquierdo:

---

### 🖥️ 1. Punto de Venta (POS)

Es la pantalla principal para registrar ventas rápidamente.

**¿Cómo usar?**
1. Selecciona una categoría usando los tabs superiores: **Todos · Pizzas · Papas · Bebidas · Sandwich · Nuggets**
2. Toca/haz clic en el producto que quieres vender.
3. Se abre un modal de confirmación donde puedes:
   - Aumentar o disminuir la **cantidad** con los botones `+` y `−`
   - Ver el **total** calculado automáticamente
4. Haz clic en **"Confirmar Venta"** para registrarla.
5. **Se abre automáticamente la factura** — puedes imprimirla o cerrarla.
6. Aparece una notificación verde confirmando que la venta fue guardada.

> 💡 Si no hay productos, verás un mensaje pidiendo que los agregues desde la sección **Productos**.

---

### 🧾 3. Facturas

Historial completo de todas las ventas, con opción de reimprimir cualquier comprobante.

**Filtros disponibles:**

| Filtro | Opciones |
|---|---|
| **Período** | Hoy · Semana · Mes · Todo |
| **Producto** | Todos · [cada producto del menú] |

**¿Cómo usar?**
1. Selecciona el período que quieres ver (Hoy, Semana, Mes o Todo).
2. Opcionalmente filtra por un producto específico haciendo clic en su chip.
3. La barra de estadísticas muestra cuántas facturas hay y el total vendido en ese filtro.
4. Haz clic en **"Imprimir"** en cualquier fila para reimprimir esa factura.

---

### 📊 4. Reportes

Muestra un resumen de las ventas del negocio.

**¿Qué incluye?**

| Tarjeta | Qué muestra |
|---|---|
| **Ventas de Hoy** | Total en dinero vendido en el día actual |
| **Pedidos Hoy** | Cantidad de transacciones realizadas hoy |

**Historial de Ventas:**
- Tabla con todas las ventas registradas.
- Usa los tabs **Día / Semana / Mes** para filtrar el período.
- Cada fila muestra: producto, hora/fecha, cantidad y monto.
- El badge superior muestra el **total de ventas y la suma** del período seleccionado.

---

### 📦 5. Productos

Administra el menú completo de la pizzería.

**¿Cómo agregar un producto?**
1. Haz clic en el botón **"Nuevo Producto"** (arriba a la derecha).
2. Selecciona el **icono** que representa el producto.
3. Escribe el **nombre** del producto.
4. Ingresa el **precio** en RD$.
5. Selecciona la **categoría** (Pizza, Papas, Bebidas, Sandwich, Nuggets).
6. Haz clic en **"Guardar Producto"**.

**¿Cómo editar un producto?**
- Haz clic en el botón ✏️ (lápiz) en la tarjeta del producto.
- Modifica los datos y guarda.

**¿Cómo eliminar un producto?**
- Haz clic en el botón 🗑️ (basura) en la tarjeta del producto.
- Confirma la eliminación en el diálogo que aparece.

> ⚠️ Eliminar un producto no borra el historial de ventas pasadas de ese producto.

---

### 📋 6. Notas

Un bloc de notas personal integrado, ideal para llevar control de pagos pendientes o recordatorios del negocio.

**¿Cómo usar?**
1. Escribe una nota en el campo de texto y haz clic en **"Agregar"**.
2. Las notas aparecen en la sección **PENDIENTES**.
3. Marca una nota como pagada/completada haciendo clic en el ✅ de la nota.
4. Las notas completadas pasan a la sección **PAGADOS / COMPLETADOS**.
5. Usa el botón **"Borrar pagados"** para limpiar las notas completadas.

> 💡 Las notas se guardan en el navegador local (localStorage) — no se sincronizan entre dispositivos.

---

## 🗄️ Base de Datos

La app utiliza **SQLite** como motor de base de datos. SQLite es un motor de base de datos relacional embebido — no requiere instalar ningún servidor, funciona directamente como un archivo local en el disco.

### Archivo de base de datos

Cuando abres la app por primera vez, se crea automáticamente el archivo:
```
dist\DeliPizza\
  └── delipizza.db     ← Base de datos SQLite
```

> ✅ **Backup:** Copia ese archivo a una USB o Google Drive para hacer respaldo de todos tus datos.

---

### Tabla: `product` — Productos del menú

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER | ID único autoincremental (clave primaria) |
| `name` | TEXT | Nombre del producto (ej: "Pizza Personal") |
| `price` | REAL | Precio de venta en RD$ |
| `category` | TEXT | Categoría: Pizza, Papas, Bebidas, Sandwich, Nuggets |
| `emoji` | TEXT | Ícono del producto (ej: 🍕) |

---

### Tabla: `sale` — Ventas registradas

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER | ID único autoincremental (clave primaria) |
| `product_id` | INTEGER | Referencia al producto vendido (FK → product.id) |
| `date` | DATETIME | Fecha y hora exacta de la venta |
| `price_at_sale` | REAL | Monto total cobrado (precio × cantidad) |
| `quantity` | INTEGER | Cantidad de unidades vendidas |

> ℹ️ El **número de factura** (`FAC-XXXX`) se genera dinámicamente a partir del `id` de la venta, por lo que no se almacena como campo separado.

---

### ¿Cómo se relacionan las tablas?

```
product               sale
─────────────         ──────────────────────
id (PK)    ←─────┐   id (PK)
name              └── product_id (FK)
price              date
category           price_at_sale
emoji              quantity
```

Cada venta registrada en `sale` apunta a un producto de la tabla `product`. Si el producto es eliminado, la venta queda registrada con el texto "Eliminado" en su lugar.

---

## 🛠️ Para Desarrolladores

### Estructura del proyecto

```
Deli-Pizza M&A\
  ├── app.py              ← Backend Flask (rutas API y base de datos)
  ├── main.py             ← Punto de entrada de la app de escritorio
  ├── delipizza.spec      ← Configuración de PyInstaller
  ├── build.bat           ← Script para generar el .exe
  ├── templates\
  │   └── index.html      ← Interfaz de usuario (HTML)
  ├── static\
  │   ├── css\styles.css  ← Estilos de la app
  │   └── js\
  │       ├── app.js      ← Lógica principal (POS, Reportes, Productos)
  │       └── notes.js    ← Lógica de Notas
  ├── dist\DeliPizza\     ← App compilada (esto se distribuye)
  └── venv\               ← Entorno virtual de Python
```

### Correr en modo desarrollo

```powershell
# Activar entorno virtual
venv\Scripts\activate

# Iniciar la app (modo navegador)
python app.py
# Luego abre http://127.0.0.1:5001 en el navegador

# O iniciar con ventana nativa (modo escritorio)
python main.py
```

### Generar el .exe

```powershell
# Doble clic en build.bat
# O desde PowerShell:
cmd /c build.bat
```

El resultado queda en `dist\DeliPizza\`. **Copia toda esa carpeta** — no solo el `.exe`.

### API Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/products` | Lista todos los productos |
| `POST` | `/api/products` | Crea un nuevo producto |
| `PUT` | `/api/products/<id>` | Edita un producto existente |
| `DELETE` | `/api/products/<id>` | Elimina un producto |
| `POST` | `/api/sales` | Registra una venta |
| `GET` | `/api/sales/history` | Historial de ventas (`?period=today/week/month`) |
| `GET` | `/api/stats` | Estadísticas del día y mes |

---

## ❓ Problemas Frecuentes

| Problema | Solución |
|---|---|
| La app no abre | Asegúrate de que la carpeta `dist\DeliPizza\` esté completa con `_internal\` |
| No se ven los productos | Ve a **Productos** y agrega items al menú |
| Los reportes muestran $0 | Es normal si no hay ventas registradas hoy |
| El acceso directo no funciona | Recrea el acceso directo apuntando a `dist\DeliPizza\DeliPizza.exe` |

---

*Desarrollado para Deli-Pizza M&A · 2026*
#   D e l i p i z z a  
 