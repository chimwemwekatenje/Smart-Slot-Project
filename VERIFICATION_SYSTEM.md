# Verification System Documentation

## Overview
The verification system allows receptionists and organization admins to verify bookings by scanning QR codes. This ensures that only authorized personnel can confirm that a user has arrived for their booking.

## Backend Implementation

### Models (`apps/verification/models.py`)
- **VerificationLog**: Tracks all verification attempts (successful and failed)
  - Links to booking, verified_by user, action type
  - Records timestamp, success status, and notes

### Services (`apps/verification/services.py`)
- **VerificationService.verify_booking()**: Verifies a booking using QR token
  - Validates booking exists and is in correct status
  - Checks user permissions (PlatformAdmin, OrganisationAdmin, Receptionist)
  - Ensures receptionist can only verify their org's bookings
  - Updates booking status to 'Verified' and sets verified_at timestamp
  
- **VerificationService.complete_booking()**: Marks verified booking as completed
  - Only works on 'Verified' bookings
  - Same permission checks as verify
  - Updates status to 'Completed'

### API Endpoints (`apps/verification/views.py`)

#### 1. Verify Booking
```
POST /api/verification/verify/
Body: {"qr_token": "uuid-string"}
```
- Verifies a booking by QR token
- Returns booking details on success

#### 2. Complete Booking
```
POST /api/verification/complete/
Body: {"qr_token": "uuid-string", "notes": "optional"}
```
- Marks a verified booking as completed
- Optional notes field for additional information

#### 3. Get Booking by Token
```
GET /api/verification/booking/?qr_token=uuid-string
```
- Retrieves booking details before verification
- Useful for preview in the scanner UI

### Permissions
- **PlatformAdmin**: Can verify any booking
- **OrganisationAdmin**: Can verify bookings from their organization
- **Receptionist**: Can verify bookings from their organization
- **Employee/External**: Cannot verify bookings

### Booking Status Flow
```
Pending → Issued → Verified → Completed
                      ↓
                  Cancelled
```

## Frontend Implementation

### QR Scanner Screen (`lib/screens/qr_scanner_screen.dart`)
A Flutter screen that:
1. Opens camera for QR code scanning
2. Detects QR codes using mobile_scanner package
3. Fetches booking details from API
4. Shows confirmation dialog with booking information
5. Calls verification endpoint on confirmation
6. Displays success/error messages

### Features
- Real-time QR code scanning
- Torch (flashlight) toggle
- Camera flip (front/back)
- Booking preview before verification
- Success/error feedback
- Prevents duplicate scans

### Required Dependencies
Add to `pubspec.yaml`:
```yaml
dependencies:
  mobile_scanner: ^5.0.0  # For QR code scanning
```

### Permissions Required

#### Android (`android/app/src/main/AndroidManifest.xml`)
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-feature android:name="android.hardware.camera" />
<uses-feature android:name="android.hardware.camera.autofocus" />
```

#### iOS (`ios/Runner/Info.plist`)
```xml
<key>NSCameraUsageDescription</key>
<string>Camera access is required to scan QR codes for booking verification</string>
```

## Integration Steps

### 1. Backend Setup
```bash
cd Smart-Slot-Project/smartslot
python manage.py makemigrations verification
python manage.py migrate
```

### 2. Frontend Setup
```bash
cd smartslot_android_app
flutter pub add mobile_scanner
flutter pub get
```

### 3. Add Scanner to Navigation
In your receptionist/admin panel, add a button to navigate to QR scanner:
```dart
ElevatedButton(
  onPressed: () {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const QRScannerScreen(),
      ),
    );
  },
  child: const Text('Scan QR Code'),
)
```

## Testing

### 1. Create a Test Booking
- Login as an employee or external user
- Book a resource
- Note the QR token from the booking response

### 2. Test Verification
- Login as a receptionist
- Navigate to QR scanner
- Scan the QR code (or manually enter token for testing)
- Verify the booking details appear
- Confirm verification
- Check booking status is updated to 'Verified'

### 3. Test Permissions
- Try verifying a booking from a different organization (should fail)
- Try verifying as an employee (should fail)
- Try verifying an already verified booking (should fail)

## Security Considerations

1. **QR Token Uniqueness**: Each booking has a unique UUID token
2. **Permission Checks**: Multiple layers of permission validation
3. **Organization Isolation**: Receptionists can only verify their org's bookings
4. **Audit Trail**: All verification attempts are logged in VerificationLog
5. **Status Validation**: Bookings can only be verified if in correct status

## Future Enhancements

1. **Push Notifications**: Notify user when booking is verified
2. **Bulk Verification**: Scan multiple QR codes in sequence
3. **Offline Mode**: Cache bookings for offline verification
4. **Analytics**: Track verification times and patterns
5. **No-Show Handling**: Mark bookings as no-show if not verified by end time
