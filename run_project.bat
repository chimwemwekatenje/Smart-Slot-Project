@echo off
echo ===================================================
echo SmartSlot - Launching Backend ^& Frontend
echo ===================================================
echo.

echo [1/2] Starting Django backend server on http://127.0.0.1:8000 (and local network)...
start "SmartSlot Backend" cmd /k "cd smartslot && ..\.venv\Scripts\python manage.py runserver 0.0.0.0:8000"

echo.
echo [2/2] Launching Flutter web app in Chrome...
cd smartslot_android_app
flutter run -d chrome

echo.
pause
