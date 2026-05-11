import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';

/// Generates and shares/prints a PDF booking receipt.
/// Call [downloadReceipt] from any screen that has a booking map.
class PdfReceiptService {
  static final _dateFmt = DateFormat('EEE d MMM yyyy, HH:mm');
  static final _timeFmt = DateFormat('HH:mm');

  /// Build the PDF document from a booking map.
  static pw.Document _buildPdf(Map<String, dynamic> booking) {
    final doc = pw.Document();

    final customData = (booking['custom_data'] as Map?)?.cast<String, dynamic>() ?? {};
    final start = DateTime.tryParse(booking['start_time'] ?? '')?.toLocal();
    final end = DateTime.tryParse(booking['end_time'] ?? '')?.toLocal();
    final qrToken = (booking['qr_token'] as String?)?.isNotEmpty == true
        ? booking['qr_token'] as String
        : 'BOOKING-${booking['id']}';

    doc.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(40),
        build: (pw.Context ctx) {
          return pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              // ── Header ──────────────────────────────────────────────────
              pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.start,
                    children: [
                      pw.Text(
                        'SmartSlot',
                        style: pw.TextStyle(
                          fontSize: 28,
                          fontWeight: pw.FontWeight.bold,
                          color: const PdfColor.fromInt(0xFF14B8A6),
                        ),
                      ),
                      pw.Text(
                        'Resource Booking System',
                        style: pw.TextStyle(
                          fontSize: 11,
                          color: const PdfColor.fromInt(0xFF64748B),
                        ),
                      ),
                    ],
                  ),
                  pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.end,
                    children: [
                      pw.Text(
                        'BOOKING RECEIPT',
                        style: pw.TextStyle(
                          fontSize: 14,
                          fontWeight: pw.FontWeight.bold,
                          color: const PdfColor.fromInt(0xFF1E293B),
                          letterSpacing: 1.5,
                        ),
                      ),
                      pw.Text(
                        'Booking #${booking['id'] ?? 'N/A'}',
                        style: pw.TextStyle(
                          fontSize: 11,
                          color: const PdfColor.fromInt(0xFF64748B),
                        ),
                      ),
                    ],
                  ),
                ],
              ),

              pw.SizedBox(height: 8),
              pw.Divider(color: const PdfColor.fromInt(0xFFE2E8F0), thickness: 1.5),
              pw.SizedBox(height: 16),

              // ── Status banner ────────────────────────────────────────────
              pw.Container(
                width: double.infinity,
                padding: const pw.EdgeInsets.symmetric(vertical: 10, horizontal: 16),
                decoration: pw.BoxDecoration(
                  color: const PdfColor.fromInt(0xFFDCFCE7),
                  borderRadius: pw.BorderRadius.circular(8),
                  border: pw.Border.all(color: const PdfColor.fromInt(0xFF86EFAC)),
                ),
                child: pw.Row(
                  children: [
                    pw.Text(
                      '✓  Booking Confirmed',
                      style: pw.TextStyle(
                        fontSize: 13,
                        fontWeight: pw.FontWeight.bold,
                        color: const PdfColor.fromInt(0xFF16A34A),
                      ),
                    ),
                  ],
                ),
              ),

              pw.SizedBox(height: 24),

              // ── Two-column layout: details + QR ─────────────────────────
              pw.Row(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  // Details column
                  pw.Expanded(
                    flex: 3,
                    child: pw.Column(
                      crossAxisAlignment: pw.CrossAxisAlignment.start,
                      children: [
                        _sectionTitle('Resource Details'),
                        pw.SizedBox(height: 8),
                        _detailRow('Resource', booking['resource_name'] ?? '-'),
                        _detailRow('Category', booking['resource_category'] ?? '-'),
                        _detailRow('Organisation', booking['organisation_name'] ?? '-'),
                        pw.SizedBox(height: 16),
                        _sectionTitle('Booking Details'),
                        pw.SizedBox(height: 8),
                        _detailRow('Booked By', booking['booked_by'] ?? '-'),
                        _detailRow('Department', customData['department'] ?? '-'),
                        _detailRow('Reason', customData['reason'] ?? '-'),
                        pw.SizedBox(height: 16),
                        _sectionTitle('Time Slot'),
                        pw.SizedBox(height: 8),
                        if (start != null)
                          _detailRow('From', _dateFmt.format(start)),
                        if (end != null)
                          _detailRow('To', _timeFmt.format(end)),
                        pw.SizedBox(height: 16),
                        _sectionTitle('Status'),
                        pw.SizedBox(height: 8),
                        _detailRow('Status', booking['status'] ?? 'Confirmed',
                            valueColor: const PdfColor.fromInt(0xFF16A34A)),
                      ],
                    ),
                  ),

                  pw.SizedBox(width: 24),

                  // QR column
                  pw.Expanded(
                    flex: 2,
                    child: pw.Column(
                      crossAxisAlignment: pw.CrossAxisAlignment.center,
                      children: [
                        _sectionTitle('Check-in QR Code'),
                        pw.SizedBox(height: 12),
                        pw.Container(
                          padding: const pw.EdgeInsets.all(8),
                          decoration: pw.BoxDecoration(
                            color: PdfColors.white,
                            border: pw.Border.all(
                              color: const PdfColor.fromInt(0xFFE2E8F0),
                            ),
                            borderRadius: pw.BorderRadius.circular(8),
                          ),
                          child: pw.BarcodeWidget(
                            barcode: pw.Barcode.qrCode(),
                            data: qrToken,
                            width: 140,
                            height: 140,
                          ),
                        ),
                        pw.SizedBox(height: 8),
                        pw.Text(
                          'Show at entrance for check-in',
                          style: pw.TextStyle(
                            fontSize: 9,
                            color: const PdfColor.fromInt(0xFF64748B),
                          ),
                          textAlign: pw.TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              pw.Spacer(),

              // ── Footer ───────────────────────────────────────────────────
              pw.Divider(color: const PdfColor.fromInt(0xFFE2E8F0)),
              pw.SizedBox(height: 8),
              pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Text(
                    'Generated by SmartSlot • ${DateFormat('d MMM yyyy').format(DateTime.now())}',
                    style: pw.TextStyle(
                      fontSize: 9,
                      color: const PdfColor.fromInt(0xFF94A3B8),
                    ),
                  ),
                  pw.Text(
                    'This is an official booking receipt',
                    style: pw.TextStyle(
                      fontSize: 9,
                      color: const PdfColor.fromInt(0xFF94A3B8),
                    ),
                  ),
                ],
              ),
            ],
          );
        },
      ),
    );

    return doc;
  }

  static pw.Widget _sectionTitle(String title) => pw.Text(
        title.toUpperCase(),
        style: pw.TextStyle(
          fontSize: 10,
          fontWeight: pw.FontWeight.bold,
          color: const PdfColor.fromInt(0xFF64748B),
          letterSpacing: 1.0,
        ),
      );

  static pw.Widget _detailRow(String label, String value,
      {PdfColor? valueColor}) =>
      pw.Padding(
        padding: const pw.EdgeInsets.symmetric(vertical: 3),
        child: pw.Row(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.SizedBox(
              width: 90,
              child: pw.Text(
                label,
                style: pw.TextStyle(
                  fontSize: 11,
                  color: const PdfColor.fromInt(0xFF64748B),
                ),
              ),
            ),
            pw.Expanded(
              child: pw.Text(
                value,
                style: pw.TextStyle(
                  fontSize: 11,
                  fontWeight: pw.FontWeight.bold,
                  color: valueColor ?? const PdfColor.fromInt(0xFF1E293B),
                ),
              ),
            ),
          ],
        ),
      );

  /// Opens the system share/print sheet with the PDF.
  static Future<void> downloadReceipt(
    BuildContext context,
    Map<String, dynamic> booking,
  ) async {
    try {
      final doc = _buildPdf(booking);
      final bytes = await doc.save();
      final resourceName = (booking['resource_name'] ?? 'booking')
          .toString()
          .replaceAll(RegExp(r'[^a-zA-Z0-9]'), '_');
      final fileName = 'SmartSlot_Receipt_${booking['id']}_$resourceName.pdf';

      await Printing.sharePdf(bytes: bytes, filename: fileName);
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not generate PDF: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
}
