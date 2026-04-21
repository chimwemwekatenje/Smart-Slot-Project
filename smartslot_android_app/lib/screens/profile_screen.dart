import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../theme.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            const SizedBox(height: 16),
            CircleAvatar(
              radius: 48,
              backgroundColor: AppColors.primary.withOpacity(0.2),
              child: Text(
                _initials(user),
                style: const TextStyle(
                    color: AppColors.primary,
                    fontSize: 28,
                    fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              _displayName(user),
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 4),
            Text(
              _roleLabel(auth.role),
              style: const TextStyle(color: AppColors.primary, fontSize: 14),
            ),
            if (auth.isExternal)
              const Padding(
                padding: EdgeInsets.only(top: 4),
                child: Text('External / Public User',
                    style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
              ),
            if (auth.isEmployee && user?['organisation_name'] != null)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.business_outlined,
                        size: 13, color: AppColors.textMuted),
                    const SizedBox(width: 4),
                    Text(user!['organisation_name'],
                        style: const TextStyle(
                            color: AppColors.textMuted, fontSize: 12)),
                  ],
                ),
              ),
            const SizedBox(height: 32),
            _InfoTile(
              icon: Icons.person_outline,
              label: 'Username',
              value: user?['username'] ?? '-',
            ),
            _InfoTile(
              icon: Icons.email_outlined,
              label: 'Email',
              value: user?['email'] ?? '-',
            ),
            if (user?['phone'] != null && user?['phone'].toString().isNotEmpty == true)
              _InfoTile(
                icon: Icons.phone_outlined,
                label: 'Phone',
                value: user?['phone'] ?? '',
              ),
            _InfoTile(
              icon: Icons.badge_outlined,
              label: 'Account Type',
              value: _roleLabel(auth.role),
            ),
            if (auth.isEmployee && user?['organisation_name'] != null)
              _InfoTile(
                icon: Icons.business_outlined,
                label: 'Organisation',
                value: user!['organisation_name'],
              ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.logout, color: AppColors.error),
                label: const Text('Sign Out',
                    style: TextStyle(color: AppColors.error)),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppColors.error),
                ),
                onPressed: () async {
                  final confirm = await showDialog<bool>(
                    context: context,
                    builder: (_) => AlertDialog(
                      backgroundColor: AppColors.surface,
                      title: const Text('Sign Out'),
                      content: const Text('Are you sure you want to sign out?'),
                      actions: [
                        TextButton(
                            onPressed: () => Navigator.pop(context, false),
                            child: const Text('Cancel')),
                        TextButton(
                            onPressed: () => Navigator.pop(context, true),
                            child: const Text('Sign Out',
                                style: TextStyle(color: AppColors.error))),
                      ],
                    ),
                  );
                  if (confirm == true && context.mounted) {
                    await auth.logout();
                    Navigator.pushReplacementNamed(context, '/login');
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _displayName(Map<String, dynamic>? user) {
    if (user == null) return '';
    final first = user['first_name']?.toString() ?? '';
    final last = user['last_name']?.toString() ?? '';
    final full = '$first $last'.trim();
    return full.isNotEmpty ? full : (user['username']?.toString() ?? '');
  }

  String _initials(Map<String, dynamic>? user) {
    if (user == null) return '?';
    final first = user['first_name']?.toString() ?? '';
    final last = user['last_name']?.toString() ?? '';
    if (first.isNotEmpty && last.isNotEmpty) {
      return '${first[0]}${last[0]}'.toUpperCase();
    }
    final username = user['username']?.toString() ?? '?';
    return username[0].toUpperCase();
  }

  String _roleLabel(String role) {
    switch (role) {
      case 'PlatformAdmin': return 'Platform Admin';
      case 'OrganisationAdmin': return 'Organisation Admin';
      case 'Receptionist': return 'Receptionist';
      case 'Employee': return 'Employee';
      case 'External': return 'External User';
      default: return role;
    }
  }
}

class _InfoTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  const _InfoTile(
      {required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(10),
        border: const Border.fromBorderSide(BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.textMuted, size: 20),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: const TextStyle(
                      color: AppColors.textMuted, fontSize: 12)),
              const SizedBox(height: 2),
              Text(value, style: Theme.of(context).textTheme.bodyLarge),
            ],
          ),
        ],
      ),
    );
  }
}
