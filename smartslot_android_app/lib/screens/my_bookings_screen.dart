import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/booking_card.dart';

class MyBookingsScreen extends StatefulWidget {
  const MyBookingsScreen({super.key});

  @override
  State<MyBookingsScreen> createState() => _MyBookingsScreenState();
}

class _MyBookingsScreenState extends State<MyBookingsScreen>
    with SingleTickerProviderStateMixin {
  List<dynamic> _bookings = [];
  bool _loading = true;
  String? _error;
  late TabController _tabs;

  final _statuses = ['All', 'Pending', 'Issued', 'Verified', 'Completed', 'Cancelled'];

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: _statuses.length, vsync: this);
    _load();
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final res = await ApiService.get('/api/bookings/my/');
      if (res.statusCode == 200) {
        setState(() => _bookings = jsonDecode(res.body));
      } else {
        setState(() => _error = 'Failed to load bookings');
      }
    } catch (e) {
      setState(() => _error = 'Connection error');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _cancel(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Cancel Booking'),
        content: const Text('Are you sure you want to cancel this booking?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('No')),
          TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Yes, Cancel',
                  style: TextStyle(color: AppColors.error))),
        ],
      ),
    );
    if (confirm != true) return;
    final res = await ApiService.patch('/api/bookings/$id/', {'status': 'Cancelled'});
    if (res.statusCode == 200) {
      _load();
    }
  }

  void _showQr(Map<String, dynamic> booking) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Booking QR Code',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(booking['resource_name'] ?? '',
                style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 24),
            QrImageView(
              data: booking['qr_token'] ?? booking['id'].toString(),
              version: QrVersions.auto,
              size: 220,
              backgroundColor: Colors.white,
              padding: const EdgeInsets.all(12),
            ),
            const SizedBox(height: 16),
            Text('Show this at the entrance for check-in',
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  List<dynamic> _filtered(String status) {
    if (status == 'All') return _bookings;
    return _bookings.where((b) => b['status'] == status).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Bookings'),
        bottom: TabBar(
          controller: _tabs,
          isScrollable: true,
          indicatorColor: AppColors.primary,
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textMuted,
          tabs: _statuses.map((s) => Tab(text: s)).toList(),
        ),
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(color: AppColors.primary))
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_error!,
                          style: Theme.of(context).textTheme.bodyMedium),
                      const SizedBox(height: 12),
                      OutlinedButton(
                          onPressed: _load, child: const Text('Retry')),
                    ],
                  ),
                )
              : TabBarView(
                  controller: _tabs,
                  children: _statuses.map((status) {
                    final list = _filtered(status);
                    if (list.isEmpty) {
                      return Center(
                        child: Text('No $status bookings',
                            style: Theme.of(context).textTheme.bodyMedium),
                      );
                    }
                    return RefreshIndicator(
                      onRefresh: _load,
                      color: AppColors.primary,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: list.length,
                        itemBuilder: (ctx, i) {
                          final b = list[i];
                          return BookingCard(
                            booking: b,
                            onTap: () => _showBookingActions(b),
                          );
                        },
                      ),
                    );
                  }).toList(),
                ),
    );
  }

  void _showBookingActions(Map<String, dynamic> booking) {
    final status = booking['status'];
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                  color: AppColors.border,
                  borderRadius: BorderRadius.circular(2)),
            ),
            const SizedBox(height: 16),
            if (status == 'Issued' || status == 'Verified')
              ListTile(
                leading: const Icon(Icons.qr_code, color: AppColors.primary),
                title: const Text('Show QR Code'),
                onTap: () {
                  Navigator.pop(context);
                  _showQr(booking);
                },
              ),
            if (status == 'Pending')
              ListTile(
                leading: const Icon(Icons.cancel_outlined,
                    color: AppColors.error),
                title: const Text('Cancel Booking',
                    style: TextStyle(color: AppColors.error)),
                onTap: () {
                  Navigator.pop(context);
                  _cancel(booking['id']);
                },
              ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}
