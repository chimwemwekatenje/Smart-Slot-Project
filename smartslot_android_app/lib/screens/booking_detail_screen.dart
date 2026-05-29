import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../services/pdf_receipt_service.dart';
import '../theme.dart';

class BookingDetailScreen extends StatelessWidget {
  final Map<String, dynamic> booking;
  const BookingDetailScreen({super.key, required this.booking});

  void _showQr(BuildContext context) {
    final qrData = (booking['qr_token'] as String?)?.isNotEmpty == true
        ? booking['qr_token'] as String
        : 'BOOKING-${booking['id']}';
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Booking QR Code'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
              child: QrImageView(data: qrData, version: QrVersions.auto, size: 180, backgroundColor: Colors.white),
            ),
            const SizedBox(height: 12),
            Text('Booking #${booking['id']}', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close')),
        ],
      ),
    );
  }

  String _formatDateTime(String? raw) {
    if (raw == null || raw.isEmpty) return 'N/A';
    final dt = DateTime.tryParse(raw)?.toLocal();
    if (dt == null) return raw;
    return DateFormat('EEE d MMM yyyy, HH:mm').format(dt);
  }

  String _formatPrice(dynamic price) {
    if (price == null) return 'Free';
    final p = double.tryParse(price.toString()) ?? 0;
    if (p == 0) return 'Free';
    return 'MWK ${p.toStringAsFixed(2)}';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final status = booking['status'] ?? 'Pending';

    // Image — photo_url is already absolute from the serializer
    final rawImage = booking['photo_url'] as String?;
    final imageUrl = rawImage != null && rawImage.isNotEmpty ? rawImage : null;

    // Custom data (department, reason, guest info)
    final customData = booking['custom_data'] as Map<String, dynamic>? ?? {};

    final headingStyle = theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold);

    return Scaffold(
      appBar: AppBar(title: Text('Booking #${booking['id'] ?? ''}')),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Hero image ──────────────────────────────────────────────
            if (imageUrl != null)
              Image.network(
                imageUrl,
                height: 220,
                width: double.infinity,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => _imagePlaceholder(),
              )
            else
              _imagePlaceholder(),

            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // ── Resource name + status ───────────────────────────
                  Text(booking['resource_name'] ?? 'Unknown Resource', style: headingStyle),
                  const SizedBox(height: 8),
                  Text(
                    booking['organisation_name'] ?? '',
                    style: theme.textTheme.bodyMedium?.copyWith(color: AppColors.textMuted),
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 4,
                    children: [
                      _StatusChip(status: status),
                      if ((booking['resource_category'] ?? booking['resource_type']) != null)
                        Chip(label: Text(booking['resource_category'] ?? booking['resource_type'])),
                    ],
                  ),

                  const SizedBox(height: 24),
                  _sectionHeader(context, 'Booking Details'),
                  const SizedBox(height: 8),

                  // ── Core booking info ────────────────────────────────
                  _InfoRow(label: 'Booking ID', value: 'BK-${booking['id'] ?? 'N/A'}'),
                  _InfoRow(
                    label: 'From',
                    value: _formatDateTime(booking['start_time']),
                  ),
                  _InfoRow(
                    label: 'To',
                    value: _formatDateTime(booking['end_time']),
                  ),
                  _InfoRow(
                    label: 'Category',
                    value: booking['resource_category'] ?? booking['resource_type'] ?? 'N/A',
                  ),
                  _InfoRow(
                    label: 'Organisation',
                    value: booking['organisation_name'] ?? 'N/A',
                  ),
                  _InfoRow(
                    label: 'Booked by',
                    value: booking['booked_by'] ?? 'N/A',
                  ),
                  _InfoRow(
                    label: 'Amount',
                    value: _formatPrice(booking['resource_price']),
                  ),
                  _InfoRow(
                    label: 'Status',
                    value: status,
                  ),

                  // ── Custom data (department / reason / guest info) ───
                  if (customData.isNotEmpty) ...[
                    const SizedBox(height: 20),
                    _sectionHeader(context, 'Additional Info'),
                    const SizedBox(height: 8),
                    if (customData['department'] != null && customData['department'].toString().isNotEmpty)
                      _InfoRow(label: 'Department', value: customData['department']),
                    if (customData['reason'] != null && customData['reason'].toString().isNotEmpty)
                      _InfoRow(label: 'Reason', value: customData['reason']),
                    if (customData['full_name'] != null && customData['full_name'].toString().isNotEmpty)
                      _InfoRow(label: 'Guest Name', value: customData['full_name']),
                    if (customData['phone'] != null && customData['phone'].toString().isNotEmpty)
                      _InfoRow(label: 'Phone', value: customData['phone']),
                    if (customData['email'] != null && customData['email'].toString().isNotEmpty)
                      _InfoRow(label: 'Email', value: customData['email']),
                  ],

                  // ── Timestamps ───────────────────────────────────────
                  const SizedBox(height: 20),
                  _sectionHeader(context, 'Timestamps'),
                  const SizedBox(height: 8),
                  if (booking['issued_at'] != null)
                    _InfoRow(label: 'Issued at', value: _formatDateTime(booking['issued_at'])),
                  if (booking['verified_at'] != null)
                    _InfoRow(label: 'Verified at', value: _formatDateTime(booking['verified_at'])),
                  _InfoRow(label: 'Created', value: _formatDateTime(booking['created_at'])),

                  const SizedBox(height: 24),

                  // ── Actions ──────────────────────────────────────────
                  if (status == 'Issued' || status == 'Verified')
                    ElevatedButton.icon(
                      icon: const Icon(Icons.qr_code),
                      label: const Text('View QR Code'),
                      onPressed: () => _showQr(context),
                    ),
                  if (status == 'Issued' || status == 'Verified') const SizedBox(height: 12),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.download_outlined),
                    label: const Text('Download Receipt'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                    ),
                    onPressed: () => PdfReceiptService.downloadReceipt(context, booking),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _imagePlaceholder() {
    return Container(
      height: 220,
      color: AppColors.border,
      child: const Icon(Icons.meeting_room_outlined, color: AppColors.textMuted, size: 64),
    );
  }

  Widget _sectionHeader(BuildContext context, String title) {
    return Text(
      title,
      style: Theme.of(context).textTheme.titleMedium?.copyWith(
        fontWeight: FontWeight.bold,
        color: AppColors.primary,
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(color: AppColors.textMuted),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String status;
  const _StatusChip({required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    switch (status) {
      case 'Issued':
      case 'Verified':
      case 'Completed':
        color = Colors.green;
        break;
      case 'Cancelled':
        color = Colors.red;
        break;
      default:
        color = Theme.of(context).colorScheme.primary;
    }
    return Chip(
      label: Text(status),
      backgroundColor: color.withValues(alpha: 0.15),
      side: BorderSide(color: color.withValues(alpha: 0.4)),
    );
  }
}
