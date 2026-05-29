import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../theme.dart';

class EditProfileScreen extends StatefulWidget {
  const EditProfileScreen({super.key});

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _photoController;
  late TextEditingController _bioController;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final user = context.read<AuthProvider>().user;
    _photoController = TextEditingController(
      text: user?['avatar_url']?.toString() ?? user?['photo_url']?.toString() ?? user?['image_url']?.toString() ?? '',
    );
    _bioController = TextEditingController(
      text: user?['bio']?.toString() ?? '',
    );
  }

  @override
  void dispose() {
    _photoController.dispose();
    _bioController.dispose();
    super.dispose();
  }

  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    await context.read<AuthProvider>().updateUser({
      'avatar_url': _photoController.text.trim(),
      'bio': _bioController.text.trim(),
    });
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Profile updated successfully.')),
      );
      Navigator.pop(context);
    }
    setState(() => _saving = false);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final user = context.watch<AuthProvider>().user;
    final avatarUrl = _photoController.text.trim();
    return Scaffold(
      appBar: AppBar(title: const Text('Edit Profile')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (avatarUrl.isNotEmpty)
              ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: Image.network(
                  avatarUrl,
                  height: 180,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    height: 180,
                    color: AppColors.border,
                    child: const Center(child: Icon(Icons.broken_image, size: 48, color: AppColors.textMuted)),
                  ),
                ),
              )
            else
              Container(
                height: 180,
                decoration: BoxDecoration(
                  color: AppColors.border,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Center(
                  child: Icon(Icons.add_a_photo_outlined, size: 48, color: AppColors.textMuted),
                ),
              ),
            const SizedBox(height: 22),
            Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  TextFormField(
                    controller: _photoController,
                    decoration: const InputDecoration(
                      labelText: 'Photo URL',
                      hintText: 'https://example.com/avatar.jpg',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.url,
                    validator: (value) {
                      return null;
                    },
                    onChanged: (_) => setState(() {}),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _bioController,
                    decoration: const InputDecoration(
                      labelText: 'Bio',
                      hintText: 'A short summary about you',
                      border: OutlineInputBorder(),
                    ),
                    minLines: 3,
                    maxLines: 6,
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return 'Enter a short bio';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: _saving ? null : _saveProfile,
                    child: _saving
                        ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                        : const Text('Save Profile'),
                  ),
                  const SizedBox(height: 16),
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Cancel'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Card(
              margin: EdgeInsets.zero,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text('Account Info', style: theme.textTheme.titleLarge),
                    const SizedBox(height: 12),
                    if (user != null) ...[
                      Text('Username: ${user['username'] ?? 'Unknown'}', style: theme.textTheme.bodyMedium),
                      const SizedBox(height: 8),
                      Text('Email: ${user['email'] ?? 'Not set'}', style: theme.textTheme.bodyMedium),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
