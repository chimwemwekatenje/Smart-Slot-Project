import 'dart:convert';
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
    try {
      final res = await ApiService.post(
        '/api/auth/login/',
        {'username': username, 'password': password},
        auth: false,
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        await ApiService.saveToken(data['access']);
        await ApiService.saveUser(data['user']);
        _user = data['user'];
        return null;
      } else {
        final err = jsonDecode(res.body);
        return err['detail'] ?? 'Login failed';
      }
    } catch (e) {
      return 'Connection error. Check your network.';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<String?> register(Map<String, dynamic> data) async {
    _loading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/api/auth/register/', data, auth: false);
      if (res.statusCode == 201) {
        return null;
      } else {
        final err = jsonDecode(res.body);
        final msg = err.values.first;
        return msg is List ? msg.first : msg.toString();
      }
    } catch (e) {
      return 'Connection error. Check your network.';
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
}
