import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/theme_provider.dart';
import '../theme.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final themeProvider = context.watch<ThemeProvider>();
    final user = auth.user;

    final fullName = _displayName(user);
    final username = user?['username']?.toString() ?? 'Unknown';
    final email = user?['email']?.toString() ?? 'Not set';
    final phone = user?['phone']?.toString() ?? 'Add phone';
    final location = user?['location']?.toString() ?? 'Unknown';
    final website = user?['website']?.toString() ?? 'No website';
    final bio = user?['bio']?.toString() ?? 'Passionate about smart booking, productivity, and seamless teamwork.';
    final avatarUrl = user?['avatar_url']?.toString() ?? user?['photo_url']?.toString() ?? user?['image_url']?.toString();

    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final textTheme = theme.textTheme;
    return Scaffold(
      appBar: AppBar(
        elevation: 0,
        title: const Text('Account'),
        actions: [
          IconButton(
            icon: Icon(Icons.settings_outlined, color: colorScheme.primary),
            onPressed: () => Navigator.pushNamed(context, '/settings'),
            tooltip: 'Settings',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    colorScheme.primary.withOpacity(0.18),
                    theme.scaffoldBackgroundColor,
                  ],
                ),
                borderRadius: BorderRadius.circular(28),
                border: Border.all(color: theme.dividerColor),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 28),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  CircleAvatar(
                    radius: 56,
                    backgroundColor: colorScheme.primary.withOpacity(0.18),
                    backgroundImage: avatarUrl != null && avatarUrl.isNotEmpty
                        ? NetworkImage(avatarUrl)
                        : null,
                    child: avatarUrl == null || avatarUrl.isEmpty
                        ? Text(
                            _initials(user),
                            style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: colorScheme.primary),
                          )
                        : null,
                  ),
                  const SizedBox(height: 16),
                  Text(fullName, style: textTheme.headlineMedium),
                  const SizedBox(height: 6),
                  Text('@$username', style: textTheme.bodyMedium),
                  const SizedBox(height: 16),
                  Text(bio, textAlign: TextAlign.center, style: textTheme.bodyMedium),
                ],
              ),
            ),
            const SizedBox(height: 20),
            _ProfileSection(
              title: 'Contact Info',
              children: [
                _DetailRow(icon: Icons.email_outlined, label: 'Email', value: email),
                _DetailRow(icon: Icons.phone_outlined, label: 'Phone', value: phone),
                _DetailRow(icon: Icons.location_on_outlined, label: 'Location', value: location),
                _DetailRow(icon: Icons.link_outlined, label: 'Website', value: website),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.edit_outlined),
                    label: const Text('Edit Profile'),
                    onPressed: () => Navigator.pushNamed(context, '/edit-profile'),
                  ),
                ),
                const SizedBox(width: 14),
                OutlinedButton.icon(
                  icon: const Icon(Icons.settings_outlined),
                  label: const Text('Settings'),
                  onPressed: () => Navigator.pushNamed(context, '/settings'),
                ),
              ],
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  String _displayName(Map<String, dynamic>? user) {
    if (user == null) return 'Guest User';
    final first = user['first_name']?.toString() ?? '';
    final last = user['last_name']?.toString() ?? '';
    final full = '$first $last'.trim();
    return full.isNotEmpty ? full : (user['username']?.toString() ?? 'Guest User');
  }

  String _initials(Map<String, dynamic>? user) {
    if (user == null) return '?';
    final first = user['first_name']?.toString() ?? '';
    final last = user['last_name']?.toString() ?? '';
    if (first.isNotEmpty && last.isNotEmpty) return '${first[0]}${last[0]}'.toUpperCase();
    final username = user['username']?.toString() ?? '?';
    return username.isNotEmpty ? username[0].toUpperCase() : '?';
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _InfoChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Chip(
      avatar: Icon(icon, size: 18, color: theme.colorScheme.primary),
      label: Text(label, style: theme.textTheme.bodyMedium),
      backgroundColor: theme.cardColor,
      side: BorderSide(color: theme.dividerColor),
      labelPadding: const EdgeInsets.symmetric(horizontal: 8),
    );
  }
}

class _ProfileSection extends StatelessWidget {
  final String title;
  final List<Widget> children;
  const _ProfileSection({required this.title, required this.children});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 18),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            ...children,
          ],
        ),
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  const _DetailRow({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: theme.colorScheme.primary.withOpacity(0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, size: 20, color: theme.colorScheme.primary),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: theme.textTheme.bodyMedium),
                const SizedBox(height: 4),
                Text(value, style: theme.textTheme.bodyLarge),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
