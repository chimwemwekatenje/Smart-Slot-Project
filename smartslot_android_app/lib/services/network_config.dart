import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

/// Stores predefined server profiles and current configuration
class NetworkConfig {
  static const String _profilesKey = 'network_profiles';
  static const String _activeProfileKey = 'active_profile';

  /// Predefined profiles for common environments
  static const Map<String, String> defaultProfiles = {
    'Local (Emulator)': 'http://10.0.2.2:8000',
    'Local (iPhone)': 'http://localhost:8000',
    'Local (Web)': 'http://localhost:8000',
  };

  /// Save a custom server profile
  static Future<void> saveProfile(String name, String url) async {
    final prefs = await SharedPreferences.getInstance();
    final profiles = _getProfiles();
    profiles[name] = url;
    await prefs.setString(_profilesKey, jsonEncode(profiles));
  }

  /// Remove a custom profile
  static Future<void> removeProfile(String name) async {
    final prefs = await SharedPreferences.getInstance();
    final profiles = _getProfiles();
    profiles.remove(name);
    await prefs.setString(_profilesKey, jsonEncode(profiles));
  }

  /// Get all available profiles (default + custom)
  static Map<String, String> getAllProfiles() {
    return {...defaultProfiles, ..._getProfiles()};
  }

  /// Get stored custom profiles only
  static Map<String, String> _getProfiles() {
    try {
      final prefs = SharedPreferences.getInstance();
      return {};
    } catch (_) {
      return {};
    }
  }

  /// Set active profile
  static Future<void> setActiveProfile(String profileName) async {
    final prefs = await SharedPreferences.getInstance();
    final profiles = getAllProfiles();
    if (profiles.containsKey(profileName)) {
      final url = profiles[profileName]!;
      await prefs.setString(_activeProfileKey, profileName);
      return;
    }
  }

  /// Get active profile name
  static Future<String?> getActiveProfile() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_activeProfileKey);
  }

  /// Get description for error (with helpful suggestions)
  static String getErrorSuggestion(String errorMessage) {
    if (errorMessage.toLowerCase().contains('connection')) {
      return 'Cannot connect to server.\n\n'
          '• Check your Wi-Fi/Mobile data\n'
          '• Verify the server IP address in Settings\n'
          '• Ensure backend server is running\n'
          '• Try a different Network Profile';
    } else if (errorMessage.toLowerCase().contains('unauthorized')) {
      return 'Invalid credentials. Please check your username and password.';
    } else if (errorMessage.toLowerCase().contains('timeout')) {
      return 'Server took too long to respond.\n\n'
          '• Check your network speed\n'
          '• Verify the server address is correct\n'
          '• Try again in a moment';
    }
    return errorMessage;
  }
}
