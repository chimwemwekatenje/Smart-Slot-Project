# API Configuration Guide

## Automatic URL Detection

The app now automatically detects the correct API URL based on the platform:

### Default URLs by Platform:
- **Web**: `http://localhost:8000`
- **Android Emulator**: `http://10.0.2.2:8000` (points to host machine)
- **iOS Simulator**: `http://localhost:8000`
- **Desktop**: `http://localhost:8000`

## For Physical Android Devices

When testing on a physical Android device, you need to override the default URL:

### Option 1: Using --dart-define (Recommended)
```bash
flutter run --dart-define=API_URL=http://YOUR_SERVER_IP:8000
```

Example with your server IP:
```bash
flutter run --dart-define=API_URL=http://41.70.47.82:8000
```

### Option 2: Build with Custom URL
```bash
flutter build apk --dart-define=API_URL=http://41.70.47.82:8000
```

## For Production

When building for production, set your production API URL:
```bash
flutter build apk --release --dart-define=API_URL=https://api.yourproduction.com
```

## Testing the Connection

After running the app, check the console logs to see which URL is being used. The app will automatically select the appropriate URL based on the platform.
