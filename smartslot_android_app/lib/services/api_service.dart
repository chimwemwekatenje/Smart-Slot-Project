import 'dart:convert';
import 'dart:io' show Platform;
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

class ApiService {
  // Automatically detect the correct base URL based on platform
  static String get baseUrl {
    if (kIsWeb) {
      // Flutter web → localhost
      return 'http://localhost:8000';
    } else if (Platform.isAndroid) {
      // Android emulator → 10.0.2.2 (emulator's host machine)
      // Android physical device → use your actual server IP
      // For development, you can override this by setting an environment variable
      const envUrl = String.fromEnvironment('API_URL', defaultValue: '');
      if (envUrl.isNotEmpty) return envUrl;
      
      // Default: assume emulator
      return 'http://10.0.2.2:8000';
    } else if (Platform.isIOS) {
      // iOS simulator → localhost
      return 'http://localhost:8000';
    } else {
      // Desktop (Windows, macOS, Linux) → localhost
      return 'http://localhost:8000';
    }
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
  }

  static Future<void> saveUser(Map<String, dynamic> user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user', jsonEncode(user));
  }

  static Future<Map<String, dynamic>?> getUser() async {
    final prefs = await SharedPreferences.getInstance();
    final str = prefs.getString('user');
    if (str == null) return null;
    return jsonDecode(str);
  }

  static Future<void> clearSession() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('user');
  }

  static Future<Map<String, String>> _headers({bool auth = true}) async {
    final headers = {'Content-Type': 'application/json'};
    if (auth) {
      final token = await getToken();
      if (token != null) headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  static Future<http.Response> get(String path) async {
    return http.get(Uri.parse('$baseUrl$path'), headers: await _headers());
  }

  static Future<http.Response> post(String path, Map<String, dynamic> body, {bool auth = true}) async {
    return http.post(Uri.parse('$baseUrl$path'), headers: await _headers(auth: auth), body: jsonEncode(body));
  }

  static Future<http.Response> patch(String path, Map<String, dynamic> body) async {
    return http.patch(Uri.parse('$baseUrl$path'), headers: await _headers(), body: jsonEncode(body));
  }

  static Future<http.Response> delete(String path) async {
    return http.delete(Uri.parse('$baseUrl$path'), headers: await _headers());
  }
}
