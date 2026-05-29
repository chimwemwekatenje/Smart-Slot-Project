import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/theme_provider.dart';
import '../theme.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _isPrivate = false;
  bool _pushNotifications = true;
  bool _emailNotifications = true;
  bool _alertsEnabled = true;
  bool _twoFactor = false;
  String _language = 'English';
  String _region = 'United States';
  String _dataUsage = 'Balanced';
  late final TextEditingController _serverController;

  void _showBottomSheet(String title, Widget content) {
    final theme = Theme.of(context);
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: theme.cardColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 12),
            Container(
              width: 60,
              height: 4,
              decoration: BoxDecoration(
                color: theme.dividerColor,
                borderRadius: BorderRadius.circular(99),
              ),
            ),
            const SizedBox(height: 16),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: theme.textTheme.headlineMedium),
                  const SizedBox(height: 16),
                  content,
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ],
        ),
      ),
    );

  }

  void _confirmAction({required String title, required String message, required VoidCallback onConfirm}) {
    showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              onConfirm();
            },
            child: Text('Confirm', style: TextStyle(color: Theme.of(context).colorScheme.error)),
          ),
        ],
      ),
    );
  }

  @override
  void initState() {
    super.initState();
    _serverController = TextEditingController(text: ApiService.baseUrl);
  }

  @override
  void dispose() {
    _serverController.dispose();
    super.dispose();
  }

  void _showServerUrlSheet() {
    final theme = Theme.of(context);
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: theme.cardColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 12),
            Container(width: 60, height: 4, decoration: BoxDecoration(color: theme.dividerColor, borderRadius: BorderRadius.circular(99))),
            const SizedBox(height: 16),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Server URL', style: theme.textTheme.headlineMedium),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _serverController,
                    decoration: const InputDecoration(labelText: 'API base URL (e.g. http://192.168.1.43:8000)'),
                    keyboardType: TextInputType.url,
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () async {
                            final url = _serverController.text.trim();
                            Navigator.pop(context);
                            final scaffold = ScaffoldMessenger.of(context);
                            scaffold.showSnackBar(const SnackBar(content: Text('Testing server...')));
                            final ok = await ApiService.validateAndSaveBaseUrl(url);
                            scaffold.hideCurrentSnackBar();
                            if (ok) {
                              setState(() {});
                              scaffold.showSnackBar(const SnackBar(content: Text('Server saved and validated.')));
                            } else {
                              scaffold.showSnackBar(const SnackBar(content: Text('Could not reach server.')));
                            }
                          },
                          child: const Text('Test & Save'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final textTheme = theme.textTheme;
    final themeProvider = context.watch<ThemeProvider>();
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Account', style: textTheme.titleLarge),
            const SizedBox(height: 12),
            _buildTile(
              icon: Icons.lock_outline,
              title: 'Change password',
              subtitle: 'Keep your account secure',
              onTap: () => _showBottomSheet(
                'Change Password',
                const _PasswordForm(),
              ),
            ),
            _buildTile(
              icon: Icons.email_outlined,
              title: 'Update email',
              subtitle: auth.user?['email'] ?? 'No email set',
              onTap: () => _showBottomSheet(
                'Update Email',
                const _EmailForm(),
              ),
            ),
            _buildTile(
              icon: Icons.delete_outline,
              title: 'Delete account',
              subtitle: 'Remove your account permanently',
              trailing: const Icon(Icons.chevron_right),
              onTap: () => _confirmAction(
                title: 'Delete Account',
                message: 'This action cannot be undone. Do you want to continue?',
                onConfirm: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Account deletion is not yet connected.')),
                  );
                },
              ),
            ),
            _buildTile(
              icon: Icons.logout,
              title: 'Logout',
              subtitle: 'Sign out of the app',
              trailing: const Icon(Icons.chevron_right),
              onTap: () async {
                await auth.logout();
                if (context.mounted) {
                  Navigator.pushNamedAndRemoveUntil(context, '/login', (_) => false);
                }
              },
            ),
            const SizedBox(height: 24),
            Text('Privacy', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            SwitchListTile(
              tileColor: theme.cardColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
              value: _isPrivate,
              onChanged: (value) => setState(() => _isPrivate = value),
              title: const Text('Private account'),
              subtitle: const Text('Only approved followers can see your activity.'),
              secondary: const Icon(Icons.shield_outlined),
            ),
            _buildTile(
              icon: Icons.block_outlined,
              title: 'Block/report users',
              subtitle: 'Manage blocked users and reports',
              trailing: const Icon(Icons.chevron_right),
              onTap: () => _showBottomSheet(
                'Block or Report',
                const _ReportForm(),
              ),
            ),
            const SizedBox(height: 24),
            Text('Notifications', style: textTheme.titleLarge),
            const SizedBox(height: 12),
            SwitchListTile(
              tileColor: theme.cardColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
              activeColor: colorScheme.primary,
              value: _pushNotifications,
              onChanged: (value) => setState(() => _pushNotifications = value),
              title: const Text('Push notifications'),
              secondary: const Icon(Icons.notifications_active_outlined),
            ),
            SwitchListTile(
              tileColor: theme.cardColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
              activeColor: colorScheme.primary,
              value: _emailNotifications,
              onChanged: (value) => setState(() => _emailNotifications = value),
              title: const Text('Email updates'),
              secondary: const Icon(Icons.email_outlined),
            ),
            SwitchListTile(
              tileColor: theme.cardColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
              activeColor: colorScheme.primary,
              value: _alertsEnabled,
              onChanged: (value) => setState(() => _alertsEnabled = value),
              title: const Text('Alerts'),
              secondary: const Icon(Icons.warning_amber_outlined),
            ),
            const SizedBox(height: 24),
            Text('Security', style: textTheme.titleLarge),
            const SizedBox(height: 12),
            SwitchListTile(
              tileColor: theme.cardColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
              activeColor: colorScheme.primary,
              value: _twoFactor,
              onChanged: (value) => setState(() => _twoFactor = value),
              title: const Text('Two-factor authentication'),
              subtitle: const Text('Extra protection for your account'),
              secondary: const Icon(Icons.security_outlined),
            ),
            _buildTile(
              icon: Icons.devices_outlined,
              title: 'Login activity',
              subtitle: 'Review devices and sessions',
              trailing: const Icon(Icons.chevron_right),
              onTap: () => _showBottomSheet(
                'Login Activity',
                const _LoginActivity(),
              ),
            ),
            const SizedBox(height: 24),
            Text('Preferences', style: textTheme.titleLarge),
            const SizedBox(height: 12),
            SwitchListTile(
              tileColor: theme.cardColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
              activeColor: colorScheme.primary,
              value: themeProvider.isDark,
              onChanged: (_) => themeProvider.toggle(),
              title: const Text('Dark mode'),
              secondary: const Icon(Icons.nights_stay_outlined),
            ),
            _buildTile(
              icon: Icons.language_outlined,
              title: 'Language',
              subtitle: _language,
              trailing: const Icon(Icons.chevron_right),
              onTap: () => _showSelectionSheet(
                title: 'Language',
                options: const ['English', 'Spanish', 'French', 'Portuguese'],
                selected: _language,
                onSelected: (value) => setState(() => _language = value),
              ),
            ),
            _buildTile(
              icon: Icons.public_outlined,
              title: 'Region',
              subtitle: _region,
              trailing: const Icon(Icons.chevron_right),
              onTap: () => _showSelectionSheet(
                title: 'Region',
                options: const ['United States', 'Nigeria', 'Kenya', 'South Africa'],
                selected: _region,
                onSelected: (value) => setState(() => _region = value),
              ),
            ),
            _buildTile(
              icon: Icons.data_usage_outlined,
              title: 'Data usage',
              subtitle: _dataUsage,
              trailing: const Icon(Icons.chevron_right),
              onTap: () => _showSelectionSheet(
                title: 'Data Usage',
                options: const ['Balanced', 'Low', 'High'],
                selected: _dataUsage,
                onSelected: (value) => setState(() => _dataUsage = value),
              ),
            ),
            const SizedBox(height: 24),
            Text('Support', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            _buildTile(
              icon: Icons.help_outline,
              title: 'Help / FAQ',
              subtitle: 'Common questions and answers',
              onTap: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Help content is not yet connected.')),
                );
              },
            ),
            _buildTile(
              icon: Icons.support_agent,
              title: 'Contact support',
              subtitle: 'Send a support request',
              onTap: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Support chat is not yet connected.')),
                );
              },
            ),
            _buildTile(
              icon: Icons.bug_report_outlined,
              title: 'Report a problem',
              subtitle: 'Tell us what went wrong',
              onTap: () {
                _showBottomSheet(
                  'Report a Problem',
                  const _ReportForm(),
                );
              },
            ),
            const SizedBox(height: 12),
            _buildTile(
              icon: Icons.cloud_outlined,
              title: 'Server URL',
              subtitle: ApiService.baseUrl,
              trailing: const Icon(Icons.chevron_right),
              onTap: _showServerUrlSheet,
            ),
            const SizedBox(height: 24),
            Text('Legal', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            _buildTile(
              icon: Icons.description_outlined,
              title: 'Terms & Conditions',
              subtitle: 'Read the app terms',
            ),
            _buildTile(
              icon: Icons.privacy_tip_outlined,
              title: 'Privacy Policy',
              subtitle: 'How we handle your data',
            ),
            const SizedBox(height: 24),
            Text('App version', style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 8),
            Text('SmartSlot 2.0.0', style: Theme.of(context).textTheme.bodyLarge),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildTile({
    required IconData icon,
    required String title,
    required String subtitle,
    Widget? trailing,
    VoidCallback? onTap,
  }) {
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 6),
        leading: Icon(icon, color: theme.colorScheme.primary),
        title: Text(title, style: textTheme.titleLarge),
        subtitle: Text(subtitle, style: textTheme.bodyMedium),
        trailing: trailing ?? Icon(Icons.chevron_right, color: textTheme.bodyMedium?.color),
        onTap: onTap,
      ),
    );
  }

  void _showSelectionSheet({
    required String title,
    required List<String> options,
    required String selected,
    required void Function(String) onSelected,
  }) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(height: 12),
          Container(
            width: 60,
            height: 4,
            decoration: BoxDecoration(
              color: Theme.of(context).dividerColor,
              borderRadius: BorderRadius.circular(99),
            ),
          ),
          const SizedBox(height: 16),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: 16),
                for (final option in options)
                  RadioListTile<String>(
                    title: Text(option),
                    value: option,
                    groupValue: selected,
                    onChanged: (value) {
                      if (value != null) {
                        onSelected(value);
                        Navigator.pop(context);
                      }
                    },
                  ),
                const SizedBox(height: 16),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _PasswordForm extends StatefulWidget {
  const _PasswordForm();

  @override
  State<_PasswordForm> createState() => _PasswordFormState();
}

class _PasswordFormState extends State<_PasswordForm> {
  final _formKey = GlobalKey<FormState>();
  final _currentController = TextEditingController();
  final _newController = TextEditingController();

  @override
  void dispose() {
    _currentController.dispose();
    _newController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _currentController,
            obscureText: true,
            decoration: const InputDecoration(labelText: 'Current password'),
            validator: (value) => value == null || value.isEmpty ? 'Required' : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _newController,
            obscureText: true,
            decoration: const InputDecoration(labelText: 'New password'),
            validator: (value) => value == null || value.length < 8 ? 'At least 8 characters' : null,
          ),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: () {
              if (_formKey.currentState?.validate() == true) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Password update is not connected yet.')),
                );
              }
            },
            child: const Text('Save password'),
          ),
        ],
      ),
    );
  }
}

class _EmailForm extends StatefulWidget {
  const _EmailForm();

  @override
  State<_EmailForm> createState() => _EmailFormState();
}

class _EmailFormState extends State<_EmailForm> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _emailController,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'New email address'),
            validator: (value) {
              if (value == null || value.isEmpty) return 'Required';
              if (!value.contains('@')) return 'Enter a valid email';
              return null;
            },
          ),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: () {
              if (_formKey.currentState?.validate() == true) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Email update is not connected yet.')),
                );
              }
            },
            child: const Text('Save email'),
          ),
        ],
      ),
    );
  }
}

class _ReportForm extends StatefulWidget {
  const _ReportForm();

  @override
  State<_ReportForm> createState() => _ReportFormState();
}

class _ReportFormState extends State<_ReportForm> {
  final _formKey = GlobalKey<FormState>();
  final _descriptionController = TextEditingController();

  @override
  void dispose() {
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _descriptionController,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'What happened?',
              alignLabelWithHint: true,
            ),
            validator: (value) => value == null || value.isEmpty ? 'Please describe the issue' : null,
          ),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: () {
              if (_formKey.currentState?.validate() == true) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Thank you. Report submitted.')),
                );
              }
            },
            child: const Text('Submit report'),
          ),
        ],
      ),
    );
  }
}

class _LoginActivity extends StatelessWidget {
  const _LoginActivity();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Recent login activity', style: Theme.of(context).textTheme.bodyLarge),
        const SizedBox(height: 16),
        _ActivityRow(label: 'This device', value: 'Chrome on Windows'),
        _ActivityRow(label: 'Last login', value: 'Today, 10:24 AM'),
        _ActivityRow(label: 'Other device', value: 'iPhone 14 Pro'),
        const SizedBox(height: 20),
        ElevatedButton(
          onPressed: () {
            Navigator.pop(context);
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Session management is not connected.')),
            );
          },
          child: const Text('Manage sessions'),
        ),
      ],
    );
  }
}

class _ActivityRow extends StatelessWidget {
  final String label;
  final String value;
  const _ActivityRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodyMedium),
          Text(value, style: Theme.of(context).textTheme.bodyLarge),
        ],
      ),
    );
  }
}
