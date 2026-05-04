@echo off
:: =============================================================================
::  build.bat — Construye DeliPizza.exe con un doble clic
::  Resultado: dist\DeliPizza\DeliPizza.exe
:: =============================================================================

echo.
echo  =============================================
echo   Deli-Pizza M^&A  —  Generando .exe
echo  =============================================
echo.

:: 1. Activar entorno virtual
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEq 0 (
    echo [ERROR] No se encontro el entorno virtual en venv\
    echo         Ejecuta primero:  python -m venv venv
    pause & exit /b 1
)

:: 2. Instalar / actualizar dependencias de build
echo [1/3] Instalando pywebview y pyinstaller...
pip install pywebview pyinstaller --quiet --upgrade
if %ERRORLEVEL% NEq 0 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause & exit /b 1
)

:: 3. Limpiar builds anteriores
echo [2/3] Limpiando build anterior...
if exist dist\DeliPizza  rmdir /s /q dist\DeliPizza
if exist build\DeliPizza rmdir /s /q build\DeliPizza

:: 4. Construir el .exe
echo [3/3] Construyendo el ejecutable (puede tardar 1-3 minutos)...
pyinstaller delipizza.spec --noconfirm
if %ERRORLEVEL% NEq 0 (
    echo [ERROR] PyInstaller fallo. Revisa los mensajes de arriba.
    pause & exit /b 1
)

echo.
echo  =============================================
echo   LISTO!  El ejecutable esta en:
echo   dist\DeliPizza\DeliPizza.exe
echo  =============================================
echo.
echo  Puedes copiar toda la carpeta dist\DeliPizza\
echo  a cualquier PC con Windows y funciona sin instalar nada.
echo.
pause
