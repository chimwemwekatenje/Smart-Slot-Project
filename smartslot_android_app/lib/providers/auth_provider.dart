import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  Map<String, dynamic>? _user;
  bool _loading = false;

  Map<String, dynamic>? get user => _user;
  bool get loading => _loading;
  bool get isLoggedIn => _user != null;
  String get role => _user?['role'] ?? '';
  bool get isExternal => role == 'External';
  bool get isEmployee => role == 'Employee';
  bool get isOrgAdmin => role == 'OrganisationAdmin';
  int? get organisationId => _user?['organisation'] as int?;

  Future<void> loadSession() async {
    _user = await ApiService.getUser();
    notifyListeners();
  }

  Future<String?> login(String username, String password) async {
    _loading = true;
    notifyListeners();

    if (username == 'mary_external' && password == 'pass1234') {
      final demoUser = {
        'id': 999,
        'username': 'mary_external',
        'email': 'mary.external@example.com',
        'first_name': 'Mary',
        'last_name': 'External',
        'role': 'External',
      };
      await ApiService.saveToken('demo_token');
      await ApiService.saveUser(demoUser);
      ApiService.activateDemoMode();
      _user = demoUser;
      _loading = false;
      notifyListeners();
      return null;
    }

    try {
      final res = await ApiService.post(
        '/api/auth/login/',
        {'username': username, 'password': password},
        auth: false,
      ).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        await ApiService.saveToken(data['access']);
        await ApiService.saveUser(data['user']);
        _user = data['user'];
        return null;
      } else if (res.statusCode == 401) {
        final err = jsonDecode(res.body);
        return err['detail'] ?? 'Invalid username or password';
      } else {
        final err = jsonDecode(res.body);
        return err['detail'] ?? 'Login failed';
      }
    } on SocketException catch (_) {
      return 'Connection error: Cannot reach server.\nCheck Network Configuration in Settings or use demo credentials.';
    } on TimeoutException catch (_) {
      return 'Connection timeout: Server not responding.\nCheck your network and server status.';
    } catch (e) {
      return 'Connection error: ${e.toString()}\nGo to Settings → Network Configuration.';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<String?> register(Map<String, dynamic> data) async {
    _loading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/api/auth/register/', data, auth: false)
          .timeout(const Duration(seconds: 10));
      if (res.statusCode == 201) {
        return null;
      } else {
        final err = jsonDecode(res.body);
        final msg = err.values.first;
        return msg is List ? msg.first : msg.toString();
      }
    } on SocketException catch (_) {
      return 'Connection error: Cannot reach server.\nCheck Network Configuration in Settings.';
    } on TimeoutException catch (_) {
      return 'Connection timeout: Server not responding.\nCheck your network and server status.';
    } catch (e) {
      return 'Connection error: ${e.toString()}\nGo to Settings → Network Configuration.';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await ApiService.clearSession();
    _user = null;
    notifyListeners();
  }

  Future<void> updateUser(Map<String, dynamic> updates) async {
    if (_user == null) return;
    _user = {..._user!, ...updates};
    await ApiService.saveUser(_user!);
    notifyListeners();
  }
}
