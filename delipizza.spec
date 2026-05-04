# -*- mode: python ; coding: utf-8 -*-
"""
delipizza.spec — Configuración de PyInstaller para Deli-Pizza M&A.

Para construir el .exe ejecuta:
    venv\Scripts\pyinstaller.exe delipizza.spec --noconfirm
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(Path('.').resolve())],
    binaries=[],
    # Incluir templates y static dentro del bundle
    datas=[
        ('templates', 'templates'),
        ('static',    'static'),
    ],
    hiddenimports=[
        # Flask y extensiones
        'flask',
        'flask_sqlalchemy',
        'sqlalchemy',
        'sqlalchemy.dialects.mssql',
        'sqlalchemy.dialects.mssql.pyodbc',
        'sqlalchemy.orm',
        # pyodbc
        'pyodbc',
        # Dotenv
        'dotenv',
        # Jinja2
        'jinja2',
        'jinja2.ext',
        'markupsafe',
        # WebView
        'webview',
        'webview.platforms.winforms',
        'clr',
        # Werkzeug
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.routing',
        'werkzeug.middleware',
        'werkzeug.middleware.proxy_fix',
        # Itsdangerous / click
        'itsdangerous',
        'click',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'PIL', 'PyQt5', 'tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DeliPizza',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # Sin ventana de consola negra
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='static/icon.ico',  # Descomenta si tienes un .ico
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DeliPizza',
)
