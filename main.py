"""
main.py — Punto de entrada de Deli-Pizza M&A como app de escritorio.
"""

import sys
import threading
import time
import socket
import webview

# IMPORTANTE: usar la app real, no crear otra
from app import app, db


# ── Utilidad: esperar a que el servidor esté escuchando ───────────────────────
def _wait_for_server(host: str, port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False


# ── Hilo Flask ─────────────────────────────────────────────────────────────────
def _run_flask():
    with app.app_context():
        db.create_all()

        # Normalizar categorías (si existe esa lógica)
        try:
            from app import Product, normalize_category
            for p in Product.query.all():
                n = normalize_category(p.category)
                if p.category != n:
                    p.category = n
            db.session.commit()
        except Exception:
            pass

    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Iniciar Flask en segundo plano
    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()

    # Esperar a que esté listo
    if not _wait_for_server('127.0.0.1', 5001):
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('Error', 'No se pudo iniciar el servidor interno.')
        sys.exit(1)

    # Abrir ventana nativa
    window = webview.create_window(
        title='Deli-Pizza M&A — Sistema de Gestión',
        url='http://127.0.0.1:5001',
        width=1400,
        height=860,
        min_size=(900, 600),
        resizable=True,
    )

    webview.start(gui=None)