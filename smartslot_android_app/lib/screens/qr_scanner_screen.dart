import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../theme.dart';

class QrScannerScreen extends StatefulWidget {
  const QrScannerScreen({super.key});

  @override
  State<QrScannerScreen> createState() => _QrScannerScreenState();
}

class _QrScannerScreenState extends State<QrScannerScreen> {
  bool _isProcessing = false;

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_isProcessing) return;
    
    final List<Barcode> barcodes = capture.barcodes;
    if (barcodes.isEmpty) return;

    final String? code = barcodes.first.rawValue;
    if (code == null) return;

    setState(() => _isProcessing = true);

    try {
      // 1. Decode token
      final decoded = utf8.decode(base64Decode(code));
      final Map<String, dynamic> data = jsonDecode(decoded);
      
      final bookingId = data['id'];
      
      // 2. Verify in Supabase
      final booking = await Supabase.instance.client
          .from('bookings')
          .select('*, resource:resources(name)')
          .eq('id', bookingId)
          .maybeSingle();

      if (!mounted) return;

      if (booking == null) {
        _showResult(context, 'Invalid Booking', 'This booking does not exist.', isError: true);
      } else {
        // 3. Check-in (update status)
        await Supabase.instance.client
            .from('bookings')
            .update({'status': 'confirmed'}) // or 'completed' depending on logic
            .eq('id', bookingId);
            
        _showResult(
          context, 
          'Verified Successfully!', 
          'Booking for ${booking['resource']['name']}\nUser: ${booking['guest_name'] ?? 'Registered User'}', 
          isError: false
        );
      }
    } catch (e) {
      if (mounted) {
        _showResult(context, 'Error', 'Invalid QR code format.', isError: true);
      }
    } finally {
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) setState(() => _isProcessing = false);
      });
    }
  }

  void _showResult(BuildContext context, String title, String message, {required bool isError}) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: Text(title, style: TextStyle(color: isError ? AppColors.error : AppColors.primary)),
        content: Text(message, style: const TextStyle(color: AppColors.textPrimary)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('OK', style: TextStyle(color: AppColors.primary)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scan Booking QR')),
      body: Stack(
        children: [
          MobileScanner(
            controller: MobileScannerController(
              detectionSpeed: DetectionSpeed.noDuplicates,
              facing: CameraFacing.back,
            ),
            onDetect: _onDetect,
          ),
          // Scanner Overlay
          Center(
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.primary, width: 4),
                borderRadius: BorderRadius.circular(20),
              ),
            ),
          ),
          if (_isProcessing)
            Container(
              color: Colors.black54,
              child: const Center(
                child: CircularProgressIndicator(color: AppColors.primary),
              ),
            ),
        ],
      ),
    );
  }
}
