@echo off
echo ===================================================
2: echo SmartSlot - Launching Backend & Frontend
3: echo ===================================================
4: echo.
5: 
6: echo [1/2] Starting Django backend server on http://127.0.0.1:8000 (and local network)...
7: start "SmartSlot Backend" cmd /k "cd smartslot && ..\.venv\Scripts\python manage.py runserver 0.0.0.0:8000"
8: 
9: echo.
10: echo [2/2] Launching Flutter web app in Chrome...
11: cd smartslot_android_app
12: flutter run -d chrome
13: 
14: pause
