import 'dart:convert';
import 'dart:io' show Platform;
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

class ApiService {
  // ─── BASE URL ────────────────────────────────────────────────────────────────
  // Priority order:
  //   1. --dart-define=API_URL=http://x.x.x.x:8000  (passed at build/run time)
  //   2. Saved URL from last successful connection
  //   3. Platform default

  static String? _cachedBaseUrl;

  static String get baseUrl {
    if (_cachedBaseUrl != null) return _cachedBaseUrl!;

    // 1. Build-time override
    const envUrl = String.fromEnvironment('API_URL', defaultValue: '');
    if (envUrl.isNotEmpty) {
      _cachedBaseUrl = envUrl;
      return envUrl;
    }

    // 2. Platform defaults
    if (kIsWeb) {
      _cachedBaseUrl = 'http://localhost:8000';
    } else if (Platform.isAndroid) {
      // Physical device — use your PC's hotspot IP.
      _cachedBaseUrl = 'http://10.91.252.84:8000';
    } else if (Platform.isIOS) {
      _cachedBaseUrl = 'http://localhost:8000';
    } else {
      _cachedBaseUrl = 'http://localhost:8000';
    }

    return _cachedBaseUrl!;
  }

  // ─── TOKEN / SESSION ─────────────────────────────────────────────────────────

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
  }

  static Future<void> saveRefreshToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('refresh_token', token);
  }

  static Future<String?> getRefreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('refresh_token');
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
    await prefs.remove('refresh_token');
    await prefs.remove('user');
    _cachedBaseUrl = null;
  }

  // ─── HEADERS ─────────────────────────────────────────────────────────────────

  static Future<Map<String, String>> _headers({bool auth = true}) async {
    final headers = {'Content-Type': 'application/json'};
    if (auth) {
      final token = await getToken();
      if (token != null) headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  // ─── HTTP METHODS ─────────────────────────────────────────────────────────────

  static Future<http.Response> get(String path) async {
    return http.get(
      Uri.parse('$baseUrl$path'),
      headers: await _headers(),
    );
  }

  static Future<http.Response> post(
    String path,
    Map<String, dynamic> body, {
    bool auth = true,
  }) async {
    return http.post(
      Uri.parse('$baseUrl$path'),
      headers: await _headers(auth: auth),
      body: jsonEncode(body),
    );
  }

  static Future<http.Response> patch(
    String path,
    Map<String, dynamic> body,
  ) async {
    return http.patch(
      Uri.parse('$baseUrl$path'),
      headers: await _headers(),
      body: jsonEncode(body),
    );
  }

  static Future<http.Response> delete(String path) async {
    return http.delete(
      Uri.parse('$baseUrl$path'),
      headers: await _headers(),
    );
  }

  // ── Token refresh ─────────────────────────────────────────────────────────────

  /// Attempts to refresh the access token using the stored refresh token.
  /// Returns true on success, false if the refresh token is expired/invalid.
  static Future<bool> refreshAccessToken() async {
    final refreshToken = await getRefreshToken();
    if (refreshToken == null) return false;

    try {
      final res = await http.post(
        Uri.parse('$baseUrl/api/auth/refresh/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh': refreshToken}),
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        await saveToken(data['access']);
        return true;
      }
    } catch (_) {}
    return false;
  }

  // ─── MEDIA URL HELPER ────────────────────────────────────────────────────────
  // Converts a relative media path like /media/resources_photos/img.jpg
  // into a full URL using the current baseUrl.

  static String mediaUrl(String relativePath) {
    if (relativePath.startsWith('http')) return relativePath;
    final base = baseUrl.replaceAll(RegExp(r'/$'), '');
    final path = relativePath.startsWith('/') ? relativePath : '/$relativePath';
    return '$base$path';
  }
}
