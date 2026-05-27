@echo off
echo ========================================
echo Android Platform Tools Setup
echo ========================================
echo.

REM Check if platform-tools already exists
if exist "platform-tools\adb.exe" (
    echo Platform tools already installed!
    goto :setup_path
)

echo Step 1: Downloading Android Platform Tools...
echo This may take a few minutes depending on your connection...
curl -L https://dl.google.com/android/repository/platform-tools-latest-windows.zip -o platform-tools.zip

if not exist platform-tools.zip (
    echo ERROR: Download failed. Please check your internet connection.
    pause
    exit /b 1
)

echo.
echo Step 2: Extracting files...
powershell -command "Expand-Archive -Path platform-tools.zip -DestinationPath . -Force"

if not exist "platform-tools\adb.exe" (
    echo ERROR: Extraction failed. Please extract platform-tools.zip manually.
    pause
    exit /b 1
)

echo.
echo Step 3: Cleaning up...
del platform-tools.zip

:setup_path
echo.
echo Step 4: Setting up PATH for this session...
set PATH=%CD%\platform-tools;%PATH%

echo.
echo Step 5: Starting ADB server...
platform-tools\adb start-server

echo.
echo Step 6: Checking for connected devices...
platform-tools\adb devices

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Your phone should appear above with "device" status.
echo If it shows "unauthorized", check your phone for a USB debugging prompt.
echo.
echo To use ADB in this terminal session, run:
echo   set PATH=%CD%\platform-tools;%%PATH%%
echo.
echo To use Flutter with your phone, run:
echo   flutter devices
echo   flutter run --dart-define=API_URL=http://YOUR_IP:8000
echo.
pause
