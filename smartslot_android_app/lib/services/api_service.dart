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
  static bool _demoMode = false;

  static bool get isDemoMode => _demoMode;
  static void activateDemoMode() => _demoMode = true;
  static void deactivateDemoMode() => _demoMode = false;

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
      // This is updated automatically when you run:
      //   flutter run --dart-define=API_URL=http://YOUR_IP:8000
      _cachedBaseUrl = 'http://10.40.235.84:8000';
    } else if (Platform.isIOS) {
      _cachedBaseUrl = 'http://localhost:8000';
    } else {
      _cachedBaseUrl = 'http://localhost:8000';
    }

    return _cachedBaseUrl!;
  }

  /// Initialize the ApiService by loading any saved base URL from
  /// SharedPreferences. Call this once at app startup before `runApp`.
  static Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString('api_base_url');
    if (saved != null && saved.isNotEmpty) {
      _cachedBaseUrl = saved;
    }
  }

  /// Save a custom base URL to persistent storage and cache it.
  static Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    _cachedBaseUrl = url;
    await prefs.setString('api_base_url', url);
  }

  /// Validate a candidate base URL by hitting a known public endpoint
  /// and, on success, persist it. Returns true when the URL works.
  static Future<bool> validateAndSaveBaseUrl(String url, {String testPath = '/api/organisations/'}) async {
    try {
      final uri = Uri.parse(url).resolve(testPath);
      final resp = await http.get(uri).timeout(const Duration(seconds: 8));
      if (resp.statusCode == 200) {
        await setBaseUrl(url);
        return true;
      }
    } catch (_) {
      // ignore errors — validation failed
    }
    return false;
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
    _cachedBaseUrl = null; // reset so next launch re-detects
    _demoMode = false;
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
    if (_demoMode) {
      return _handleDemoDelete(path);
    }
    return http.delete(
      Uri.parse('$baseUrl$path'),
      headers: await _headers(),
    );
  }

  // ─── DEMO FALLBACK (Temporary offline mode) ─────────────────────────────────
  static http.Response _fakeResponse(Object body, int statusCode) {
    return http.Response(jsonEncode(body), statusCode, headers: {'content-type': 'application/json'});
  }

  static Future<http.Response> _handleDemoGet(String path) async {
    final uri = Uri.parse(path);
    final segmentPath = uri.path;

    if (segmentPath == '/api/resources/') {
      return _fakeResponse(_demoResources, 200);
    }
    if (segmentPath == '/api/organisations/') {
      return _fakeResponse(_demoOrganisations, 200);
    }
    if (segmentPath == '/api/bookings/my/') {
      return _fakeResponse(_demoBookings, 200);
    }
    if (segmentPath == '/api/org/resources/') {
      return _fakeResponse(_demoResources, 200);
    }
    if (segmentPath == '/api/org/bookings/') {
      return _fakeResponse(_demoBookings, 200);
    }
    if (segmentPath.startsWith('/api/resources/') && segmentPath.endsWith('/schedule/')) {
      return _fakeResponse(_demoSchedule, 200);
    }
    if (segmentPath == '/api/verification/booking/') {
      final qrToken = uri.queryParameters['qr_token'] ?? 'DEMO-QR-1';
      final booking = _demoBookings.firstWhere(
          (b) => b['qr_token'] == qrToken,
          orElse: () => _demoBookings.first,
      );
      return _fakeResponse(booking, 200);
    }
    return _fakeResponse({'detail': 'Not found'}, 404);
  }

  static Future<http.Response> _handleDemoPost(String path, Map<String, dynamic> body) async {
    final uri = Uri.parse(path);
    final segmentPath = uri.path;
    if (segmentPath == '/api/bookings/') {
      final newBooking = {
        'id': _demoBookings.length + 1,
        'resource_name': body['resource_name'] ?? 'Demo Resource',
        'resource_category': body['resource_category'] ?? 'Boardroom',
        'status': 'Issued',
        'start_time': body['start_time'] ?? DateTime.now().toIso8601String(),
        'end_time': body['end_time'] ?? DateTime.now().add(const Duration(hours: 2)).toIso8601String(),
        'qr_token': 'DEMO-QR-${_demoBookings.length + 1}',
      };
      _demoBookings.add(newBooking);
      return _fakeResponse(newBooking, 201);
    }
    if (segmentPath == '/api/auth/register/') {
      return _fakeResponse({'detail': 'Demo registration completed'}, 201);
    }
    if (segmentPath == '/api/verification/verify/') {
      return _fakeResponse({'detail': 'Booking verified', 'status': 'Verified'}, 200);
    }
    return _fakeResponse({'detail': 'Not found'}, 404);
  }

  static Future<http.Response> _handleDemoPatch(String path, Map<String, dynamic> body) async {
    final uri = Uri.parse(path);
    final segments = uri.pathSegments;
    if (segments.length >= 3 && segments[0] == 'api' && segments[1] == 'bookings') {
      final id = int.tryParse(segments[2]) ?? 0;
      final booking = _demoBookings.firstWhere((b) => b['id'] == id, orElse: () => {});
      booking.addAll(body);
      return _fakeResponse(booking, 200);
          return _fakeResponse({'detail': 'Booking not found'}, 404);
    }
    return _fakeResponse({'detail': 'Not found'}, 404);
  }

  static Future<http.Response> _handleDemoDelete(String path) async {
    final uri = Uri.parse(path);
    final segments = uri.pathSegments;
    if (segments.length >= 4 && segments[0] == 'api' && segments[1] == 'bookings' && segments[3] == 'delete') {
      final id = int.tryParse(segments[2]) ?? 0;
      _demoBookings.removeWhere((b) => b['id'] == id);
      return _fakeResponse('', 204);
    }
    return _fakeResponse({'detail': 'Not found'}, 404);
  }

  static final List<Map<String, dynamic>> _demoResources = [
    {
      'id': 101,
      'name': 'Boardroom A',
      'category': 'Boardroom',
      'price': '0',
      'description': 'A spacious boardroom with seating for 12 and projector.',
      'organisation_name': 'Smart Slots HQ',
      'photo_url': 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80',
    },
    {
      'id': 102,
      'name': 'Executive Vehicle',
      'category': 'Vehicle',
      'price': '250',
      'description': 'Comfortable executive transport for up to 4 people.',
      'organisation_name': 'Smart Slots Transport',
      'photo_url': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=800&q=80',
    },
    {
      'id': 103,
      'name': 'Conference Hall',
      'category': 'Hall',
      'price': '500',
      'description': 'Large hall ideal for conferences, trainings, and events.',
      'organisation_name': 'Smart Slots Events',
      'photo_url': 'https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=800&q=80',
    },
  ];

  static final List<Map<String, dynamic>> _demoOrganisations = [
    {'id': 1, 'name': 'Smart Slots HQ'},
    {'id': 2, 'name': 'Corporate Rentals'},
  ];

  static final List<Map<String, dynamic>> _demoBookings = [
    {
      'id': 1,
      'resource_name': 'Boardroom A',
      'resource_category': 'Boardroom',
      'booking_type': 'Boardroom',
      'resource_type': 'Boardroom',
      'status': 'Issued',
      'start_time': DateTime.now().add(const Duration(days: 1, hours: 2)).toIso8601String(),
      'end_time': DateTime.now().add(const Duration(days: 1, hours: 4)).toIso8601String(),
      'qr_token': 'DEMO-QR-1',
      'organisation_name': 'Smart Slots HQ',
    },
    {
      'id': 2,
      'resource_name': 'Executive Vehicle',
      'resource_category': 'Vehicle',
      'booking_type': 'Vehicle',
      'resource_type': 'Vehicle',
      'status': 'Verified',
      'start_time': DateTime.now().subtract(const Duration(days: 1, hours: 3)).toIso8601String(),
      'end_time': DateTime.now().subtract(const Duration(days: 1, hours: 1)).toIso8601String(),
      'qr_token': 'DEMO-QR-2',
      'organisation_name': 'Smart Slots Transport',
    },
  ];

  static final List<Map<String, dynamic>> _demoSchedule = [
    {'time': '09:00 AM', 'available': true},
    {'time': '11:00 AM', 'available': true},
    {'time': '02:00 PM', 'available': false},
    {'time': '04:00 PM', 'available': true},
  ];

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
