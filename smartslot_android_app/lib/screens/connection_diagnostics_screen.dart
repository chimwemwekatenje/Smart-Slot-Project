import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';

class ConnectionDiagnosticsScreen extends StatefulWidget {
  const ConnectionDiagnosticsScreen({super.key});

  @override
  State<ConnectionDiagnosticsScreen> createState() => _ConnectionDiagnosticsScreenState();
}

class _ConnectionDiagnosticsScreenState extends State<ConnectionDiagnosticsScreen> {
  late Future<Map<String, dynamic>> _diagnostics;

  @override
  void initState() {
    super.initState();
    _diagnostics = _runDiagnostics();
  }

  Future<Map<String, dynamic>> _runDiagnostics() async {
    final errors = <String>[];
    final results = {
      'api_url': ApiService.baseUrl,
      'server_reachable': false,
      'api_responsive': false,
      'errors': errors,
    };

    try {
      final res = await ApiService.get('/api/organisations/?limit=1').timeout(const Duration(seconds: 5));
      results['server_reachable'] = res.statusCode == 200;
      if (res.statusCode != 200) {
        errors.add('Server responded with status ${res.statusCode}.');
      }
    } on TimeoutException catch (_) {
      errors.add('Server timed out after 5 seconds.');
    } on SocketException catch (_) {
      errors.add('Unable to connect to server. Check your network.');
    } catch (e) {
      errors.add('Failed to reach server: ${e.toString()}');
    }

    return results;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Connection Diagnostics'),
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _diagnostics,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }

          final data = snapshot.data ?? {};
          final apiUrl = data['api_url'] as String? ?? 'Unknown';
          final serverReachable = data['server_reachable'] as bool? ?? false;
          final errors = data['errors'] as List? ?? [];

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildStatusCard(
                  'Server URL',
                  apiUrl,
                  serverReachable ? Colors.green : Colors.orange,
                ),
                const SizedBox(height: 16),
                _buildStatusCard(
                  'Server Status',
                  serverReachable ? 'Reachable' : 'Unreachable',
                  serverReachable ? Colors.green : Colors.red,
                ),
                const SizedBox(height: 24),
                const Text(
                  'Troubleshooting Steps',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                ..._buildTroubleshootingSteps(serverReachable),
                if (errors.isNotEmpty) ...[
                  const SizedBox(height: 24),
                  const Text(
                    'Errors',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.error),
                  ),
                  const SizedBox(height: 12),
                  ...errors.map((e) => Text('• $e')),
                ],
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: () {
                      Navigator.pop(context);
                      Navigator.pushNamed(context, '/settings');
                    },
                    icon: const Icon(Icons.settings),
                    label: const Text('Open Network Settings'),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildStatusCard(String title, String value, Color statusColor) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: statusColor,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  List<Widget> _buildTroubleshootingSteps(bool isConnected) {
    final steps = [
      '1. Verify your device is connected to the internet',
      '2. Check the server URL in Settings → Network Configuration',
      '3. Ensure the backend server is running (port 8000)',
      '4. If on physical device, ensure device and server are on same network',
      '5. Try using a different Network Profile from Settings',
      '6. Restart the app and try again',
    ];

    if (isConnected) {
      return [
        const Card(
          color: Color(0x1A4CAF50),
          child: Padding(
            padding: EdgeInsets.all(12),
            child: Row(
              children: [
                Icon(Icons.check_circle, color: Colors.green),
                SizedBox(width: 8),
                Expanded(
                  child: Text('Server is reachable. You should be able to login now.'),
                ),
              ],
            ),
          ),
        ),
      ];
    }

    return steps
        .map((step) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Text(step, style: const TextStyle(fontSize: 13)),
            ))
        .toList();
  }
}
