# Network Configuration - Long-Term Solution

## Problem Solved
❌ **Before**: Users had to rebuild the app with `--dart-define=API_URL=...` every time they changed networks
✅ **After**: Users can now dynamically configure the server URL without rebuilding

## How It Works

### 1. **Settings → Network Configuration**
Users can now permanently save their server URL:
- Open **Settings** → Scroll to **Support** section → Tap **Server URL**
- Enter the API base URL (e.g., `http://192.168.1.43:8000`)
- Tap **Test & Save** to verify connection and save permanently
- The app remembers this URL even after closing

### 2. **Connection Error Handling**
When login fails with a connection error:
- Clear error message explains what went wrong
- Link to **"Open Network Configuration"** appears
- User can jump directly to settings to fix the URL
- No need to restart or rebuild the app

### 3. **Network Profiles** (Future Enhancement)
We've built the foundation for multiple saved profiles:
- Local (Emulator)
- Local (iPhone)
- Local (Web)
- Custom profiles for Staging, Production, etc.

This can be extended to include a profile switcher.

## For Different Scenarios

### Local Development (Physical Device)
1. Find your PC's IP address:
   ```bash
   # Windows
   ipconfig | find "IPv4"
   
   # macOS/Linux
   ifconfig | grep inet
   ```
2. Ensure device is on same Wi-Fi network
3. Go to Settings → Server URL
4. Enter: `http://YOUR_IP:8000`
5. Tap "Test & Save"

### Android Emulator
- Automatically uses `http://10.0.2.2:8000` (default emulator host)
- Or change in Settings if needed

### iOS Simulator
- Automatically uses `http://localhost:8000`
- Ensure backend runs on your Mac

### Production
- Save your production API URL: `https://api.yourproduction.com`
- Works for all devices automatically

## Technical Implementation

### Key Files Created:
1. **`lib/services/network_config.dart`**
   - Manages server profiles
   - Provides error suggestions
   - Validates URLs

2. **`lib/screens/connection_diagnostics_screen.dart`**
   - Diagnoses connection issues
   - Troubleshooting steps
   - Current server status

### Key Files Updated:
1. **`lib/services/api_service.dart`**
   - Already had `setBaseUrl()` and `validateAndSaveBaseUrl()`
   - Loads saved URL on app startup

2. **`lib/providers/auth_provider.dart`**
   - Better error messages
   - Specific handling for different error types (timeout, socket, etc.)

3. **`lib/screens/login_screen.dart`**
   - Error messages show link to network config
   - Connection errors show configuration button

4. **`lib/main.dart`**
   - Added route for diagnostics screen

## Usage Flow

```
User tries to login
    ↓
Connection error occurs
    ↓
Error message shows + "Open Network Configuration" link
    ↓
User taps link → Connection Diagnostics Screen
    ↓
Diagnostics shows current server URL and status
    ↓
User can either:
   a) Go to Settings and change URL
   b) Try troubleshooting steps
    ↓
URL saved → No need to rebuild
```

## Benefits

✅ **No Rebuilding** - Change URL without `flutter run --dart-define=...`
✅ **Better UX** - Clear error messages guide users
✅ **Persistent** - URL saved to SharedPreferences
✅ **Flexible** - Works for any network configuration
✅ **Maintainable** - Foundation for profiles and advanced features

## Future Enhancements

1. **Profile Switcher** - Quick toggle between Dev/Staging/Prod
2. **Auto-Discovery** - Scan QR code to set server URL
3. **mDNS Resolution** - Connect to server by name instead of IP
4. **Network History** - Remember recently used URLs
5. **Offline Mode** - Cache data when offline

## Testing

To test the solution:

1. **Change URL in Settings:**
   - Go to Settings → Server URL
   - Change to a different IP
   - Tap "Test & Save"
   - Should show connection status

2. **Test Connection Error:**
   - Set URL to invalid address (e.g., `http://1.1.1.1:8000`)
   - Try logging in
   - Should show connection error + network config link

3. **Verify Persistence:**
   - Close app completely
   - Reopen app
   - Should use the saved URL

## Notes

- URL validation timeout is 8 seconds
- SavedPreferences key: `api_base_url`
- Active profile key: `active_profile`
- Default profiles cannot be deleted but can be overridden
