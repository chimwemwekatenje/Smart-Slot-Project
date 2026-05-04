import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../theme.dart';
import '../widgets/booking_card.dart';
import '../widgets/resource_card.dart';
import 'resource_detail_screen.dart';
import 'qr_scanner_screen.dart';

class OrgPanelScreen extends StatefulWidget {
  const OrgPanelScreen({super.key});

  @override
  State<OrgPanelScreen> createState() => _OrgPanelScreenState();
}

class _OrgPanelScreenState extends State<OrgPanelScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  List<dynamic> _resources = [];
  List<dynamic> _bookings = [];
  bool _loadingRes = true;
  bool _loadingBook = true;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 2, vsync: this);
    _loadResources();
    _loadBookings();
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _loadResources() async {
    setState(() => _loadingRes = true);
    try {
      final auth = context.read<AuthProvider>();
      if (auth.organisationId == null) return;
      
      final data = await Supabase.instance.client
          .from('resources')
          .select()
          .eq('organisation_id', auth.organisationId!);
          
      if (mounted) setState(() => _resources = data);
    } catch (_) {}
    setState(() => _loadingRes = false);
  }

  Future<void> _loadBookings() async {
    setState(() => _loadingBook = true);
    try {
      final auth = context.read<AuthProvider>();
      if (auth.organisationId == null) return;
      
      final data = await Supabase.instance.client
          .from('bookings')
          .select('*, resource:resources(name), user:profiles(full_name, email)')
          .eq('organisation_id', auth.organisationId!);
          
      if (mounted) setState(() => _bookings = data);
    } catch (_) {}
    setState(() => _loadingBook = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Organisation Panel'),
        bottom: TabBar(
          controller: _tabs,
          indicatorColor: AppColors.primary,
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textMuted,
          tabs: const [
            Tab(text: 'Resources'),
            Tab(text: 'Bookings'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabs,
        children: [
          // Resources tab
          _loadingRes
              ? const Center(
                  child: CircularProgressIndicator(color: AppColors.primary))
              : _resources.isEmpty
                  ? _EmptyState(
                      icon: Icons.meeting_room_outlined,
                      message:
                          'No resources yet.\nAdd resources from the web admin panel.',
                    )
                  : RefreshIndicator(
                      onRefresh: _loadResources,
                      color: AppColors.primary,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _resources.length,
                        itemBuilder: (ctx, i) => ResourceCard(
                          resource: _resources[i],
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => ResourceDetailScreen(
                                  resource: _resources[i]),
                            ),
                          ),
                        ),
                      ),
                    ),

          // Bookings tab
          _loadingBook
              ? const Center(
                  child: CircularProgressIndicator(color: AppColors.primary))
              : _bookings.isEmpty
                  ? _EmptyState(
                      icon: Icons.calendar_today_outlined,
                      message: 'No bookings for your organisation yet.',
                    )
                  : RefreshIndicator(
                      onRefresh: _loadBookings,
                      color: AppColors.primary,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _bookings.length,
                        itemBuilder: (ctx, i) =>
                            BookingCard(booking: _bookings[i]),
                      ),
                    ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const QrScannerScreen()),
        ),
        backgroundColor: AppColors.primary,
        icon: const Icon(Icons.qr_code_scanner, color: Colors.white),
        label: const Text('Verify QR', style: TextStyle(color: Colors.white)),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final IconData icon;
  final String message;
  const _EmptyState({required this.icon, required this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: AppColors.textMuted, size: 56),
            const SizedBox(height: 16),
            Text(message,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium),
          ],
        ),
      ),
    );
  }
}
