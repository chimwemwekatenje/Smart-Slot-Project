import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../services/api_service.dart';
import '../services/pdf_receipt_service.dart';
import '../theme.dart';

class QRScannerScreen extends StatefulWidget {
  const QRScannerScreen({super.key});

  @override
  State<QRScannerScreen> createState() => _QRScannerScreenState();
}

class _QRScannerScreenState extends State<QRScannerScreen> {
  final MobileScannerController _camera = MobileScannerController();
  bool _isProcessing = false;
  String? _lastScannedCode;

  static final _dateFmt = DateFormat('EEE d MMM yyyy, HH:mm');
  static final _timeFmt = DateFormat('HH:mm');

  @override
  void dispose() {
    _camera.dispose();
    super.dispose();
  }

  // ── Main scan handler ────────────────────────────────────────────────────────

  Future<void> _onScan(String qrToken) async {
    if (_isProcessing || qrToken == _lastScannedCode) return;
    setState(() { _isProcessing = true; _lastScannedCode = qrToken; });

    try {
      // 1. Fetch booking details
      final detailsResp = await ApiService.get('/api/verification/booking/?qr_token=$qrToken');

      if (!mounted) return;

      if (detailsResp.statusCode != 200) {
        final err = jsonDecode(detailsResp.body);
        _showError(err['detail'] ?? 'Booking not found');
        return;
      }

      final booking = jsonDecode(detailsResp.body) as Map<String, dynamic>;

      // 2. Show booking details + confirm dialog
      final confirm = await _showBookingPreview(booking);
      if (!mounted || confirm != true) return;

      // 3. Verify the booking
      final verifyResp = await ApiService.post('/api/verification/verify/', {'qr_token': qrToken});
      if (!mounted) return;

      if (verifyResp.statusCode == 200) {
        final data = jsonDecode(verifyResp.body) as Map<String, dynamic>;
        final verifiedBooking = data['booking'] as Map<String, dynamic>;
        // Show full receipt with PDF download
        await _showVerifiedReceipt(verifiedBooking, data['detail'] as String? ?? 'Booking verified!');
      } else {
        final err = jsonDecode(verifyResp.body);
        _showError(err['detail'] ?? 'Verification failed');
      }
    } catch (e) {
      if (mounted) _showError('Connection error: $e');
    } finally {
      if (mounted) {
        setState(() => _isProcessing = false);
        // Allow re-scan after 4 seconds
        Future.delayed(const Duration(seconds: 4), () {
          if (mounted) setState(() => _lastScannedCode = null);
        });
      }
    }
  }

  // ── Booking preview dialog (before verification) ─────────────────────────────

  Future<bool?> _showBookingPreview(Map<String, dynamic> booking) {
    final start = DateTime.tryParse(booking['start_time'] ?? '')?.toLocal();
    final end = DateTime.tryParse(booking['end_time'] ?? '')?.toLocal();
    final status = booking['status'] as String? ?? '';
    final statusColor = _statusColor(status);

    return showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Verify Booking'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Status chip
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: statusColor.withValues(alpha: 0.5)),
                ),
                child: Text(status,
                    style: TextStyle(color: statusColor, fontWeight: FontWeight.w600, fontSize: 12)),
              ),
              const SizedBox(height: 14),
              _previewRow('Resource', booking['resource_name']),
              _previewRow('Category', booking['resource_category']),
              _previewRow('Booked By', booking['booked_by']),
              _previewRow('Organisation', booking['organisation_name']),
              if (start != null) _previewRow('From', _dateFmt.format(start)),
              if (end != null) _previewRow('To', _timeFmt.format(end)),
              const SizedBox(height: 14),
              const Text('Do you want to verify this booking?',
                  style: TextStyle(fontWeight: FontWeight.bold)),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
            child: const Text('Verify', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  // ── Verified receipt bottom sheet (with PDF download) ────────────────────────

  Future<void> _showVerifiedReceipt(Map<String, dynamic> booking, String message) async {
    final customData = (booking['custom_data'] as Map?)?.cast<String, dynamic>() ?? {};
    final start = DateTime.tryParse(booking['start_time'] ?? '')?.toLocal();
    final end = DateTime.tryParse(booking['end_time'] ?? '')?.toLocal();
    final qrToken = (booking['qr_token'] as String?)?.isNotEmpty == true
        ? booking['qr_token'] as String
        : 'BOOKING-${booking['id']}';

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.85,
        maxChildSize: 0.95,
        minChildSize: 0.5,
        builder: (_, scrollCtrl) => SingleChildScrollView(
          controller: scrollCtrl,
          padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Handle
              Center(
                child: Container(width: 40, height: 4,
                    decoration: BoxDecoration(color: Theme.of(ctx).dividerColor,
                        borderRadius: BorderRadius.circular(2))),
              ),
              const SizedBox(height: 16),

              // Success banner
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.success.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppColors.success.withValues(alpha: 0.4)),
                ),
                child: Row(children: [
                  const Icon(Icons.check_circle, color: AppColors.success, size: 24),
                  const SizedBox(width: 10),
                  Expanded(child: Text(message,
                      style: const TextStyle(color: AppColors.success, fontWeight: FontWeight.w600))),
                ]),
              ),
              const SizedBox(height: 20),

              // QR code
              Center(
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: QrImageView(
                      data: qrToken, version: QrVersions.auto,
                      size: 160, backgroundColor: Colors.white),
                ),
              ),
              const SizedBox(height: 6),
              Center(
                child: Text('Booking #${booking['id']}',
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
              ),
              const SizedBox(height: 20),

              // Receipt details
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Theme.of(ctx).colorScheme.surface,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.fromBorderSide(BorderSide(color: Theme.of(ctx).dividerColor)),
                ),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('BOOKING RECEIPT',
                      style: TextStyle(color: AppColors.textMuted, fontSize: 10,
                          letterSpacing: 1.2, fontWeight: FontWeight.w600)),
                  const Divider(height: 16),
                  _receiptRow(ctx, 'Resource', booking['resource_name'] ?? '-'),
                  _receiptRow(ctx, 'Category', booking['resource_category'] ?? '-'),
                  _receiptRow(ctx, 'Organisation', booking['organisation_name'] ?? '-'),
                  _receiptRow(ctx, 'Booked By', booking['booked_by'] ?? '-'),
                  if (customData['department'] != null)
                    _receiptRow(ctx, 'Department', customData['department']),
                  if (customData['reason'] != null)
                    _receiptRow(ctx, 'Reason', customData['reason']),
                  const Divider(height: 16),
                  if (start != null) _receiptRow(ctx, 'From', _dateFmt.format(start)),
                  if (end != null) _receiptRow(ctx, 'To', _timeFmt.format(end)),
                  const Divider(height: 16),
                  _receiptRow(ctx, 'Status', booking['status'] ?? 'Verified',
                      valueColor: AppColors.success),
                ]),
              ),
              const SizedBox(height: 20),

              // Download PDF button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.download_outlined),
                  label: const Text('Download PDF Receipt'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  onPressed: () => PdfReceiptService.downloadReceipt(ctx, booking),
                ),
              ),
              const SizedBox(height: 10),

              // Close button
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Close'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── Error dialog ─────────────────────────────────────────────────────────────

  void _showError(String message) {
    if (!mounted) return;
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(children: [
          Icon(Icons.error, color: AppColors.error, size: 28),
          SizedBox(width: 10),
          Text('Error'),
        ]),
        content: Text(message),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK')),
        ],
      ),
    );
  }

  // ── Helpers ──────────────────────────────────────────────────────────────────

  Color _statusColor(String status) {
    switch (status) {
      case 'Verified': return AppColors.success;
      case 'Issued': return AppColors.primary;
      case 'Completed': return AppColors.textMuted;
      case 'Cancelled': return AppColors.error;
      default: return AppColors.textMuted;
    }
  }

  Widget _previewRow(String label, dynamic value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 3),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SizedBox(width: 100,
          child: Text('$label:', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13))),
      Expanded(child: Text(value?.toString() ?? '-', style: const TextStyle(fontSize: 13))),
    ]),
  );

  Widget _receiptRow(BuildContext ctx, String label, String value, {Color? valueColor}) =>
      Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(width: 100,
              child: Text(label,
                  style: TextStyle(color: Theme.of(ctx).textTheme.bodyMedium?.color, fontSize: 12))),
          Expanded(
              child: Text(value,
                  style: TextStyle(
                      color: valueColor ?? Theme.of(ctx).textTheme.bodyLarge?.color,
                      fontSize: 12, fontWeight: FontWeight.w600))),
        ]),
      );

  // ── Build ────────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan QR Code'),
        actions: [
          IconButton(
            icon: const Icon(Icons.flash_on),
            onPressed: () => _camera.toggleTorch(),
            tooltip: 'Toggle torch',
          ),
          IconButton(
            icon: const Icon(Icons.flip_camera_ios),
            onPressed: () => _camera.switchCamera(),
            tooltip: 'Flip camera',
          ),
        ],
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: _camera,
            onDetect: (capture) {
              for (final barcode in capture.barcodes) {
                final code = barcode.rawValue;
                if (code != null && !_isProcessing) {
                  _onScan(code);
                  break;
                }
              }
            },
          ),

          // Processing overlay
          if (_isProcessing)
            Container(
              color: Colors.black54,
              child: const Center(
                child: Card(
                  child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text('Processing...'),
                    ]),
                  ),
                ),
              ),
            ),

          // Scan hint
          Positioned(
            bottom: 32, left: 0, right: 0,
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                decoration: BoxDecoration(
                    color: Colors.black87, borderRadius: BorderRadius.circular(24)),
                child: const Text('Align QR code within frame',
                    style: TextStyle(color: Colors.white)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
