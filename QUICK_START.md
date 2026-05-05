# Quick Start Guide

## 🚀 Get Up and Running in 5 Minutes

### Backend (2 minutes)

```bash
# Navigate to backend
cd Smart-Slot-Project/smartslot

# Apply migrations
python manage.py makemigrations verification
python manage.py migrate

# Start server
python manage.py runserver
```

✅ Backend is now running at `http://localhost:8000`

---

### Frontend (3 minutes)

#### Step 1: Fix Missing pubspec.yaml
Your Flutter project is missing `pubspec.yaml`. Create it:

```bash
cd smartslot_android_app
```

Create a file named `pubspec.yaml` with this content:

```yaml
name: smartslot_android_app
description: Smart Slot booking application
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  shared_preferences: ^2.2.2
  intl: ^0.18.1
  qr_flutter: ^4.1.0
  mobile_scanner: ^5.0.0
  pdf: ^3.10.7
  printing: ^5.12.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
```

#### Step 2: Install Dependencies
```bash
flutter pub get
```

#### Step 3: Add Camera Permission (Android)
Edit `android/app/src/main/AndroidManifest.xml`, add inside `<manifest>`:

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-feature android:name="android.hardware.camera" />
```

#### Step 4: Run the App
```bash
# For emulator
flutter run

# For physical device (replace with your server IP)
flutter run --dart-define=API_URL=http://192.168.1.100:8000
```

✅ App is now running!

---

## 🧪 Quick Test

### Test 1: Booking Security (30 seconds)
1. Login as any user
2. Navigate to bookings
3. You should only see your own bookings (or your org's if you're a receptionist)

### Test 2: API Connection (30 seconds)
1. Try to login
2. If successful, API connection is working
3. Check console for the URL being used

### Test 3: Verification System (2 minutes)
1. Create a booking as an employee
2. Login as a receptionist
3. Add a button to navigate to QR scanner:
   ```dart
   ElevatedButton(
     onPressed: () {
       Navigator.push(
         context,
         MaterialPageRoute(builder: (context) => const QRScannerScreen()),
       );
     },
     child: const Text('Scan QR'),
   )
   ```
4. Scan the booking's QR code
5. Verify it works!

---

## 📖 Need More Details?

- **Full setup instructions**: See `SETUP_INSTRUCTIONS.md`
- **Verification system docs**: See `VERIFICATION_SYSTEM.md`
- **API configuration**: See `API_CONFIG.md`
- **What was completed**: See `COMPLETION_SUMMARY.md`

---

## ❓ Common Issues

### "pubspec.yaml not found"
→ Create the file using the template above

### "Camera permission denied"
→ Add permissions to AndroidManifest.xml (see Step 3)

### "Connection refused"
→ Check server is running: `python manage.py runserver`

### "Package not found: mobile_scanner"
→ Run `flutter pub get`

---

## ✅ What's Working Now

1. ✅ **Booking Security** - Users only see authorized bookings
2. ✅ **API URLs** - Automatic platform detection
3. ✅ **Verification System** - QR code scanning for receptionists

---

## 🎯 Next Steps

1. Test the three completed features
2. Add QR scanner button to receptionist panel
3. Test with real bookings
4. (Optional) Implement payment processing
5. (Optional) Configure email service

---

**Need help?** Check the detailed documentation files or review the troubleshooting section in `SETUP_INSTRUCTIONS.md`.
