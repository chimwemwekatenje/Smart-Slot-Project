import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../theme.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _firstNameCtrl = TextEditingController();
  final _lastNameCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();

  // Employee-specific
  int? _selectedOrgId;
  List<Map<String, dynamic>> _organisations = [];

  bool _obscure = true;
  // 'external' or 'employee'
  String _accountType = 'external';
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadOrgs();
  }

  Future<void> _loadOrgs() async {
    try {
      final res = await ApiService.get('/api/organisations/');
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as List;
        setState(() => _organisations =
            data.map((o) => {'id': o['id'], 'name': o['name']}).toList());
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    _usernameCtrl.dispose();
    _emailCtrl.dispose();
    _firstNameCtrl.dispose();
    _lastNameCtrl.dispose();
    _passwordCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_accountType == 'employee' && _selectedOrgId == null) {
      setState(() => _error = 'Please select your organisation');
      return;
    }
    setState(() => _error = null);
    final auth = context.read<AuthProvider>();
    final data = {
      'username': _usernameCtrl.text.trim(),
      'email': _emailCtrl.text.trim(),
      'first_name': _firstNameCtrl.text.trim(),
      'last_name': _lastNameCtrl.text.trim(),
      'password': _passwordCtrl.text,
      'phone': _phoneCtrl.text.trim(),
      'role': _accountType == 'employee' ? 'Employee' : 'External',
      if (_accountType == 'employee' && _selectedOrgId != null)
        'organisation_id': _selectedOrgId,
    };
    final err = await auth.register(data);
    if (!mounted) return;
    if (err != null) {
      setState(() => _error = err);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Account created! Please sign in.'),
          backgroundColor: AppColors.success,
        ),
      );
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      appBar: AppBar(title: const Text('Create Account')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Account type selector
              _AccountTypeSelector(
                selected: _accountType,
                onChanged: (v) => setState(() {
                  _accountType = v;
                  _selectedOrgId = null;
                }),
              ),
              const SizedBox(height: 24),
              if (_error != null)
                _ErrorBanner(message: _error!),
              Row(children: [
                Expanded(
                  child: TextFormField(
                    controller: _firstNameCtrl,
                    decoration: const InputDecoration(labelText: 'First Name'),
                    validator: (v) => v!.isEmpty ? 'Required' : null,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextFormField(
                    controller: _lastNameCtrl,
                    decoration: const InputDecoration(labelText: 'Last Name'),
                    validator: (v) => v!.isEmpty ? 'Required' : null,
                  ),
                ),
              ]),
              const SizedBox(height: 16),
              TextFormField(
                controller: _usernameCtrl,
                decoration: const InputDecoration(
                  labelText: 'Username',
                  prefixIcon: Icon(Icons.person_outline, color: AppColors.textMuted),
                ),
                validator: (v) => v!.isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _emailCtrl,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  prefixIcon: Icon(Icons.email_outlined, color: AppColors.textMuted),
                ),
                validator: (v) =>
                    v!.isEmpty || !v.contains('@') ? 'Valid email required' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _phoneCtrl,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'Phone (optional)',
                  prefixIcon: Icon(Icons.phone_outlined, color: AppColors.textMuted),
                ),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _passwordCtrl,
                obscureText: _obscure,
                decoration: InputDecoration(
                  labelText: 'Password',
                  prefixIcon: const Icon(Icons.lock_outline, color: AppColors.textMuted),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscure ? Icons.visibility_off : Icons.visibility,
                      color: AppColors.textMuted,
                    ),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                ),
                validator: (v) => v!.length < 8 ? 'Minimum 8 characters' : null,
              ),
              // Employee: pick organisation
              if (_accountType == 'employee') ...[
                const SizedBox(height: 20),
                _organisations.isEmpty
                    ? Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          borderRadius: BorderRadius.circular(8),
                          border: const Border.fromBorderSide(
                              BorderSide(color: AppColors.border)),
                        ),
                        child: const Row(children: [
                          SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: AppColors.primary)),
                          SizedBox(width: 12),
                          Text('Loading organisations...',
                              style: TextStyle(color: AppColors.textMuted)),
                        ]),
                      )
                    : DropdownButtonFormField<int>(
                        initialValue: _selectedOrgId,
                        dropdownColor: AppColors.surface,
                        decoration: const InputDecoration(
                          labelText: 'Select Your Organisation',
                          prefixIcon: Icon(Icons.business_outlined,
                              color: AppColors.textMuted),
                        ),
                        items: _organisations
                            .map((o) => DropdownMenuItem<int>(
                                  value: o['id'] as int,
                                  child: Text(o['name']),
                                ))
                            .toList(),
                        onChanged: (v) => setState(() => _selectedOrgId = v),
                        validator: (_) => _accountType == 'employee' &&
                                _selectedOrgId == null
                            ? 'Select your organisation'
                            : null,
                      ),
              ],
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: auth.loading ? null : _submit,
                child: auth.loading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2))
                    : const Text('Create Account'),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('Already have an account? ',
                      style: Theme.of(context).textTheme.bodyMedium),
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: const Text('Sign In',
                        style: TextStyle(
                            color: AppColors.primary,
                            fontWeight: FontWeight.w600)),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _AccountTypeSelector extends StatelessWidget {
  final String selected;
  final ValueChanged<String> onChanged;
  const _AccountTypeSelector(
      {required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('I am signing up as...',
            style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(
            child: _TypeCard(
              icon: Icons.public,
              title: 'External User',
              subtitle: 'Browse & contact organisations',
              selected: selected == 'external',
              onTap: () => onChanged('external'),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _TypeCard(
              icon: Icons.badge_outlined,
              title: 'Employee',
              subtitle: 'Book resources at my organisation',
              selected: selected == 'employee',
              onTap: () => onChanged('employee'),
            ),
          ),
        ]),
      ],
    );
  }
}

class _TypeCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;
  const _TypeCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: selected
              ? AppColors.primary.withValues(alpha: 0.12)
              : AppColors.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: selected ? AppColors.primary : AppColors.border,
            width: selected ? 2 : 1,
          ),
        ),
        child: Column(
          children: [
            Icon(icon,
                color: selected ? AppColors.primary : AppColors.textMuted,
                size: 28),
            const SizedBox(height: 8),
            Text(title,
                textAlign: TextAlign.center,
                style: TextStyle(
                    color: selected
                        ? AppColors.primary
                        : AppColors.textPrimary,
                    fontWeight: FontWeight.w600,
                    fontSize: 13)),
            const SizedBox(height: 4),
            Text(subtitle,
                textAlign: TextAlign.center,
                style: const TextStyle(
                    color: AppColors.textMuted, fontSize: 11)),
          ],
        ),
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  final String message;
  const _ErrorBanner({required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: AppColors.error.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.error.withValues(alpha: 0.4)),
      ),
      child: Text(message, style: const TextStyle(color: AppColors.error)),
    );
  }
}
