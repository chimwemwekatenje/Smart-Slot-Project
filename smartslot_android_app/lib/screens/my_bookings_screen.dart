import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../services/api_service.dart';
import '../services/pdf_receipt_service.dart';
import '../theme.dart';
import '../widgets/booking_card.dart';

class MyBookingsScreen extends StatefulWidget {
  const MyBookingsScreen({super.key});
  @override
  State<MyBookingsScreen> createState() => _MyBookingsScreenState();
}

class _MyBookingsScreenState extends State<MyBookingsScreen> with SingleTickerProviderStateMixin {
  List<dynamic> _bookings = [];
  bool _loading = true;
  String? _error;
  late TabController _tabs;
  late List<String> _statuses;

  @override
  void initState() {
    super.initState();
    _statuses = ['All', 'Verified', 'Completed', 'Cancelled'];
    _tabs = TabController(length: _statuses.length, vsync: this);
    _load();
  }

  @override
  void dispose() { _tabs.dispose(); super.dispose(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await ApiService.get('/api/bookings/my/');
      if (res.statusCode == 200) {
        setState(() => _bookings = jsonDecode(res.body));
      } else {
        setState(() => _error = 'Failed to load bookings');
      }
    } catch (e) { setState(() => _error = 'Connection error'); }
    finally { setState(() => _loading = false); }
  }

  Future<void> _cancel(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Cancel Booking'),
        content: const Text('Are you sure you want to cancel this booking?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('No')),
          TextButton(onPressed: () => Navigator.pop(context, true),
              child: const Text('Yes, Cancel', style: TextStyle(color: AppColors.error))),
        ],
      ),
    );
    if (confirm != true) return;
    try {
      final res = await ApiService.patch('/api/bookings/$id/', {'status': 'Cancelled'});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final String msg = data['message'] ?? 'Booking cancelled successfully.';
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(msg),
              backgroundColor: AppColors.success,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
        _load();
      } else {
        String errMsg = 'Failed to cancel booking';
        try {
          final errData = jsonDecode(res.body);
          if (errData['detail'] != null) {
            errMsg = errData['detail'];
          }
        } catch (_) {}
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(errMsg),
              backgroundColor: AppColors.error,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Connection error while cancelling booking.'),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  Future<void> _delete(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete Booking'),
        content: const Text('This will permanently remove this booking. This cannot be undone.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true),
              child: const Text('Delete', style: TextStyle(color: AppColors.error))),
        ],
      ),
    );
    if (confirm != true) return;
    final res = await ApiService.delete('/api/bookings/$id/delete/');
    if (res.statusCode == 204) _load();
  }

  void _showQr(Map<String, dynamic> booking) {
    final qrData = (booking['qr_token'] as String?)?.isNotEmpty == true
        ? booking['qr_token'] as String
        : 'BOOKING-${booking['id']}';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.only(left: 24, right: 24, top: 20,
              bottom: MediaQuery.of(ctx).viewInsets.bottom + 20),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Container(width: 40, height: 4,
                decoration: BoxDecoration(color: Theme.of(ctx).dividerColor, borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 16),
            Text('Booking QR Code', style: Theme.of(ctx).textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(booking['resource_name'] ?? '', style: Theme.of(ctx).textTheme.bodyMedium),
            const SizedBox(height: 4),
            Text('Booking #${booking['id']}',
                style: TextStyle(color: Theme.of(ctx).textTheme.bodyMedium?.color, fontSize: 12)),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
              child: QrImageView(data: qrData, version: QrVersions.auto, size: 180, backgroundColor: Colors.white),
            ),
            const SizedBox(height: 12),
            Text('Show this at the entrance for check-in',
                style: Theme.of(ctx).textTheme.bodyMedium, textAlign: TextAlign.center),
            const SizedBox(height: 8),
          ]),
        ),
      ),
    );
  }

  List<dynamic> _filtered(String status) {
    if (status == 'All') return _bookings;
    return _bookings.where((b) => b['status'] == status).toList();
  }

  void _showBookingActions(Map<String, dynamic> booking) {
    final status = booking['status'];
    showModalBottomSheet(
      context: context,
      backgroundColor: Theme.of(context).colorScheme.surface,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const SizedBox(height: 8),
          Container(width: 40, height: 4,
              decoration: BoxDecoration(color: Theme.of(context).dividerColor, borderRadius: BorderRadius.circular(2))),
          const SizedBox(height: 16),
          if (status == 'Issued' || status == 'Verified')
            ListTile(
              leading: const Icon(Icons.qr_code, color: AppColors.primary),
              title: const Text('Show QR Code'),
              onTap: () { Navigator.pop(context); _showQr(booking); },
            ),
          // Download PDF receipt for any confirmed/active booking
          if (status == 'Issued' || status == 'Verified' || status == 'Completed')
            ListTile(
              leading: const Icon(Icons.download_outlined, color: AppColors.primary),
              title: const Text('Download PDF Receipt'),
              onTap: () {
                Navigator.pop(context);
                PdfReceiptService.downloadReceipt(context, booking);
              },
            ),
          if (status == 'Issued')
            ListTile(
              leading: const Icon(Icons.cancel_outlined, color: AppColors.warning),
              title: const Text('Cancel Booking', style: TextStyle(color: AppColors.warning)),
              onTap: () { Navigator.pop(context); _cancel(booking['id']); },
            ),
          if (status != null)
            ListTile(
              leading: const Icon(Icons.delete_outline, color: AppColors.error),
              title: const Text('Delete Booking', style: TextStyle(color: AppColors.error)),
              subtitle: const Text('Permanently remove from history',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
              onTap: () { Navigator.pop(context); _delete(booking['id']); },
            ),
          const SizedBox(height: 8),
        ]),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Bookings'),
        bottom: TabBar(
          controller: _tabs, isScrollable: true,
          indicatorColor: AppColors.primary, labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textMuted,
          tabs: _statuses.map((s) => Tab(text: s)).toList(),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
          : _error != null
              ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text(_error!, style: Theme.of(context).textTheme.bodyMedium),
                  const SizedBox(height: 12),
                  OutlinedButton(onPressed: _load, child: const Text('Retry')),
                ]))
              : TabBarView(
                  controller: _tabs,
                  children: _statuses.map((status) {
                    final list = _filtered(status);
                    if (list.isEmpty) {
                      return Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                        const Icon(Icons.calendar_today_outlined, color: AppColors.textMuted, size: 48),
                        const SizedBox(height: 12),
                        Text(status == 'All' ? 'No bookings yet' : 'No $status bookings',
                            style: Theme.of(context).textTheme.bodyMedium),
                      ]));
                    }
                    return RefreshIndicator(
                      onRefresh: _load, color: AppColors.primary,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: list.length,
                        itemBuilder: (ctx, i) => BookingCard(
                          booking: list[i], onTap: () => _showBookingActions(list[i])),
                      ),
                    );
                  }).toList(),
                ),
    );
  }
}
