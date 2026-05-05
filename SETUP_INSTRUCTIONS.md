# Setup Instructions for Completed Features

## What Was Fixed

### 1. ✅ Booking Security Issue (CRITICAL)
**Problem**: All users could see all bookings regardless of permissions.

**Solution**: Implemented role-based filtering in `apps/bookings/views.py`:
- **PlatformAdmin**: See all bookings
- **OrganisationAdmin/Receptionist**: See only their organization's bookings
- **Employee/External**: See only their own bookings

### 2. ✅ API URL Configuration
**Problem**: Hardcoded localhost URL didn't work on physical devices.

**Solution**: Implemented automatic platform detection in `lib/services/api_service.dart`:
- **Web**: `http://localhost:8000`
- **Android Emulator**: `http://10.0.2.2:8000`
- **iOS Simulator**: `http://localhost:8000`
- **Physical Devices**: Override with `--dart-define=API_URL=http://YOUR_IP:8000`

See `API_CONFIG.md` for detailed usage instructions.

### 3. ✅ Verification System (NEW FEATURE)
**What it does**: Allows receptionists to scan QR codes to verify bookings.

**Components**:
- Backend API endpoints for verification
- QR scanner screen for Flutter app
- Verification logging and audit trail
- Permission-based access control

See `VERIFICATION_SYSTEM.md` for complete documentation.

---

## Backend Setup

### Step 1: Apply Database Migrations
```bash
cd Smart-Slot-Project/smartslot
python manage.py makemigrations verification
python manage.py migrate
```

### Step 2: Verify URLs are Registered
The verification endpoints should now be available at:
- `POST /api/verification/verify/`
- `POST /api/verification/complete/`
- `GET /api/verification/booking/`

### Step 3: Test the API
```bash
# Start the development server
python manage.py runserver

# In another terminal, test the endpoint
curl -X GET http://localhost:8000/api/verification/booking/?qr_token=test-token \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Frontend Setup

### Step 1: Add Missing Dependencies

**IMPORTANT**: Your Flutter project is missing `pubspec.yaml`. You need to either:

1. **Restore from backup** if you have one, or
2. **Recreate it** with these minimum dependencies:

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
  
  # HTTP & API
  http: ^1.1.0
  shared_preferences: ^2.2.2
  
  # UI Components
  intl: ^0.18.1
  
  # QR Code
  qr_flutter: ^4.1.0
  mobile_scanner: ^5.0.0  # NEW - for QR scanning
  
  # PDF Generation
  pdf: ^3.10.7
  printing: ^5.12.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
```

### Step 2: Install Dependencies
```bash
cd smartslot_android_app
flutter pub get
```

### Step 3: Add Camera Permissions

#### Android (`android/app/src/main/AndroidManifest.xml`)
Add inside `<manifest>` tag:
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-feature android:name="android.hardware.camera" />
<uses-feature android:name="android.hardware.camera.autofocus" />
```

#### iOS (`ios/Runner/Info.plist`)
Add inside `<dict>` tag:
```xml
<key>NSCameraUsageDescription</key>
<string>Camera access is required to scan QR codes for booking verification</string>
```

### Step 4: Run the App

For emulator:
```bash
flutter run
```

For physical Android device:
```bash
flutter run --dart-define=API_URL=http://YOUR_SERVER_IP:8000
```

Replace `YOUR_SERVER_IP` with your actual server IP (e.g., `41.70.47.82`).

---

## Testing the Fixes

### Test 1: Booking Security
1. Login as an employee
2. Try to view bookings - should only see your own
3. Login as a receptionist
4. Should see all bookings from your organization

### Test 2: API URL Configuration
1. Run app on Android emulator - should connect to `10.0.2.2:8000`
2. Run app on physical device with `--dart-define` - should connect to your server
3. Check console logs to verify which URL is being used

### Test 3: Verification System
1. Create a booking as an employee
2. Login as a receptionist
3. Navigate to QR scanner (you'll need to add navigation button)
4. Scan the booking's QR code
5. Verify the booking details appear
6. Confirm verification
7. Check booking status is updated to 'Verified'

---

## Next Steps

### Immediate
1. ✅ Apply database migrations
2. ✅ Restore or recreate `pubspec.yaml`
3. ✅ Add camera permissions
4. ✅ Test on emulator

### Integration
1. Add QR scanner button to receptionist panel
2. Add verification status indicators to booking lists
3. Test with real QR codes

### Optional Enhancements
1. Implement payment processing (PayChangu integration)
2. Configure EmailJS credentials
3. Add push notifications for verification events
4. Implement booking completion workflow

---

## Troubleshooting

### Backend Issues

**Problem**: Migrations fail
```bash
# Reset migrations (CAUTION: Development only!)
python manage.py migrate verification zero
python manage.py makemigrations verification
python manage.py migrate
```

**Problem**: Import errors
```bash
# Reinstall requirements
pip install -r requirements.txt
```

### Frontend Issues

**Problem**: `pubspec.yaml` not found
- You need to recreate this file (see Step 1 above)

**Problem**: Camera not working
- Check permissions are added to AndroidManifest.xml / Info.plist
- Ensure app has camera permission in device settings

**Problem**: API connection fails
- Check server is running: `python manage.py runserver`
- Verify correct IP address is used
- Check firewall settings allow connections

**Problem**: QR scanner crashes
- Ensure `mobile_scanner` dependency is installed
- Check camera permissions are granted
- Test on physical device (emulator cameras can be unreliable)

---

## Files Modified/Created

### Backend
- ✅ `apps/bookings/views.py` - Fixed security issue
- ✅ `apps/verification/models.py` - Created VerificationLog model
- ✅ `apps/verification/services.py` - Created verification logic
- ✅ `apps/verification/views.py` - Created API endpoints
- ✅ `apps/verification/urls.py` - Created URL routing
- ✅ `apps/verification/admin.py` - Created admin interface
- ✅ `config/urls.py` - Added verification URLs

### Frontend
- ✅ `lib/services/api_service.dart` - Fixed URL configuration
- ✅ `lib/screens/qr_scanner_screen.dart` - Created QR scanner

### Documentation
- ✅ `API_CONFIG.md` - API URL configuration guide
- ✅ `VERIFICATION_SYSTEM.md` - Verification system documentation
- ✅ `SETUP_INSTRUCTIONS.md` - This file

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the detailed documentation files
3. Verify all dependencies are installed
4. Check server and app logs for error messages
