@echo off
chcp 65001 >nul
echo ============================================
echo   Electro River - Compilando a .exe
echo ============================================
echo.

echo [1/4] Instalando dependencias...
py -m pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo [2/4] Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "ElectroRiver.spec" del "ElectroRiver.spec"

echo.
echo [3/4] Compilando .exe...
py -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "ElectroRiver" ^
    --icon "icono.ico" ^
    --add-data "assets;assets" ^
    --add-data "sound.py;." ^
    --hidden-import pygame ^
    main.py

if errorlevel 1 goto error

echo.
echo [4/4] Limpiando archivos temporales...
if exist build rmdir /s /q build
if exist "ElectroRiver.spec" del "ElectroRiver.spec"

echo.
echo ============================================
echo   ? Compilacion completada!
echo   Ejecutable: dist\ElectroRiver.exe
echo ============================================
pause
exit /b 0

:error
echo.
echo ? ERROR en la compilacion
pause
exit /b 1