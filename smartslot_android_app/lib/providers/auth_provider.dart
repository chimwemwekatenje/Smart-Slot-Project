import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
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
    final session = Supabase.instance.client.auth.currentSession;
    if (session != null) {
      await _fetchProfile(session.user.id);
    }
    notifyListeners();
  }

  Future<void> _fetchProfile(String userId) async {
    try {
      final data = await Supabase.instance.client
          .from('profiles')
          .select()
          .eq('id', userId)
          .single();
      _user = data;
    } catch (e) {
      debugPrint('Error fetching profile: $e');
    }
  }

  Future<String?> login(String email, String password) async {
    _loading = true;
    notifyListeners();
    try {
      final response = await Supabase.instance.client.auth.signInWithPassword(
        email: email,
        password: password,
      );
      if (response.user != null) {
        await _fetchProfile(response.user!.id);
        return null;
      }
      return 'Login failed';
    } on AuthException catch (e) {
      return e.message;
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
      final authResponse = await Supabase.instance.client.auth.signUp(
        email: data['email'],
        password: data['password'],
        data: {
          'full_name': '${data['first_name']} ${data['last_name']}',
          'username': data['username'],
          'role': data['role']?.toString().toLowerCase(),
          'organisation_id': data['organisation_id'],
        },
      );

      if (authResponse.user != null) {
        return null;
      }
      return 'Registration failed';
    } on AuthException catch (e) {
      return e.message;
    } catch (e) {
      return 'Connection error. Check your network.';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await Supabase.instance.client.auth.signOut();
    _user = null;
    notifyListeners();
  }
}
