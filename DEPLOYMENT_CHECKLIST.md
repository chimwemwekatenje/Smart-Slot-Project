# Deployment Checklist

Use this checklist to ensure everything is set up correctly.

## ✅ Backend Setup

### Database Migrations
- [ ] Navigate to `Smart-Slot-Project/smartslot`
- [ ] Run `python manage.py makemigrations verification`
- [ ] Run `python manage.py migrate`
- [ ] Verify no migration errors

### Verification Endpoints
- [ ] Start server: `python manage.py runserver`
- [ ] Test endpoint exists: `curl http://localhost:8000/api/verification/verify/`
- [ ] Should return 401 (unauthorized) - this is correct!

### Admin Panel
- [ ] Login to admin: `http://localhost:8000/admin/`
- [ ] Verify "Verification Logs" appears in admin
- [ ] Check that bookings show correct data

### Security Fix
- [ ] Login as different user roles
- [ ] Verify each role sees only authorized bookings:
  - Platform Admin: All bookings
  - Org Admin/Receptionist: Only their org's bookings
  - Employee/External: Only their own bookings

---

## ✅ Frontend Setup

### File Structure
- [ ] Verify `pubspec.yaml` exists (if not, copy from `pubspec.yaml.example`)
- [ ] Verify `lib/services/api_service.dart` has platform detection
- [ ] Verify `lib/screens/qr_scanner_screen.dart` exists

### Dependencies
- [ ] Run `flutter pub get`
- [ ] Verify no dependency errors
- [ ] Check that `mobile_scanner` is installed

### Permissions (Android)
- [ ] Open `android/app/src/main/AndroidManifest.xml`
- [ ] Verify camera permission exists:
  ```xml
  <uses-permission android:name="android.permission.CAMERA" />
  <uses-feature android:name="android.hardware.camera" />
  ```

### Permissions (iOS)
- [ ] Open `ios/Runner/Info.plist`
- [ ] Verify camera usage description exists:
  ```xml
  <key>NSCameraUsageDescription</key>
  <string>Camera access is required to scan QR codes</string>
  ```

### API Configuration
- [ ] Run app on emulator
- [ ] Check console logs for API URL being used
- [ ] Verify it's using `10.0.2.2:8000` for Android emulator
- [ ] Test login to verify API connection

### Physical Device Testing
- [ ] Get your server's IP address
- [ ] Run: `flutter run --dart-define=API_URL=http://YOUR_IP:8000`
- [ ] Test login on physical device
- [ ] Verify API calls work

---

## ✅ Integration Testing

### Booking Security
- [ ] Create test users with different roles
- [ ] Login as Employee → should see only own bookings
- [ ] Login as Receptionist → should see org's bookings
- [ ] Login as Platform Admin → should see all bookings

### API URL Configuration
- [ ] Test on web → should use `localhost:8000`
- [ ] Test on Android emulator → should use `10.0.2.2:8000`
- [ ] Test on physical device → should use custom URL
- [ ] Verify all platforms can connect to backend

### Verification System
- [ ] Create a booking as an employee
- [ ] Note the booking ID and QR token
- [ ] Login as a receptionist from the same org
- [ ] Navigate to QR scanner (add button if needed)
- [ ] Scan the QR code
- [ ] Verify booking details appear
- [ ] Confirm verification
- [ ] Check booking status changed to "Verified"
- [ ] Check VerificationLog was created in admin

### Cross-Organization Testing
- [ ] Create booking in Org A
- [ ] Login as receptionist from Org B
- [ ] Try to verify Org A's booking
- [ ] Should fail with permission error

### Invalid QR Code Testing
- [ ] Scan an invalid QR code
- [ ] Should show "Booking not found" error
- [ ] Check VerificationLog shows failed attempt

---

## ✅ Documentation Review

- [ ] Read `QUICK_START.md` - verify instructions are clear
- [ ] Read `SETUP_INSTRUCTIONS.md` - verify all steps work
- [ ] Read `VERIFICATION_SYSTEM.md` - understand the system
- [ ] Read `API_CONFIG.md` - understand URL configuration
- [ ] Read `COMPLETION_SUMMARY.md` - know what was completed

---

## ✅ Code Quality

### Backend
- [ ] No Python syntax errors
- [ ] All imports resolve correctly
- [ ] Models are properly defined
- [ ] Services have proper error handling
- [ ] Views return appropriate status codes

### Frontend
- [ ] No Dart syntax errors (except missing package warnings)
- [ ] API service uses correct endpoints
- [ ] QR scanner handles errors gracefully
- [ ] UI shows appropriate feedback

---

## ✅ Production Readiness (Optional)

### Backend
- [ ] Set `DEBUG = False` in settings
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up proper database (PostgreSQL/MySQL)
- [ ] Configure email backend (SMTP)
- [ ] Set up static file serving
- [ ] Configure CORS properly
- [ ] Add rate limiting
- [ ] Set up logging

### Frontend
- [ ] Build release APK: `flutter build apk --release`
- [ ] Set production API URL: `--dart-define=API_URL=https://api.production.com`
- [ ] Test release build on physical device
- [ ] Verify app signing
- [ ] Test on multiple devices

---

## 🐛 Known Issues to Address

### Critical
- [ ] Missing `pubspec.yaml` - must be created before running app

### Important
- [ ] Payment processing not implemented
- [ ] Email service credentials not configured
- [ ] No booking completion workflow

### Nice to Have
- [ ] Add QR scanner button to receptionist panel
- [ ] Add verification status indicators
- [ ] Implement push notifications
- [ ] Add offline support

---

## 📊 Testing Results

### Backend Tests
- Booking security: ⬜ Pass / ⬜ Fail
- Verification API: ⬜ Pass / ⬜ Fail
- Permission checks: ⬜ Pass / ⬜ Fail
- Audit logging: ⬜ Pass / ⬜ Fail

### Frontend Tests
- API connection: ⬜ Pass / ⬜ Fail
- QR scanning: ⬜ Pass / ⬜ Fail
- Error handling: ⬜ Pass / ⬜ Fail
- UI/UX: ⬜ Pass / ⬜ Fail

### Integration Tests
- End-to-end verification: ⬜ Pass / ⬜ Fail
- Cross-org isolation: ⬜ Pass / ⬜ Fail
- Invalid QR handling: ⬜ Pass / ⬜ Fail

---

## 🎯 Sign-Off

- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] All integration tests pass
- [ ] Documentation is complete
- [ ] Known issues are documented
- [ ] Ready for deployment

**Deployed by**: _______________  
**Date**: _______________  
**Environment**: ⬜ Development / ⬜ Staging / ⬜ Production

---

## 📞 Support Contacts

- Backend issues: Check Django logs
- Frontend issues: Check Flutter logs with `flutter run -v`
- Documentation: See `SETUP_INSTRUCTIONS.md`
- Emergency: Review `COMPLETION_SUMMARY.md` for what was changed
