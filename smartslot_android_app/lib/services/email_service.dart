import 'package:emailjs/emailjs.dart' as emailjs;
import 'package:intl/intl.dart';

const _serviceId = 'YOUR_SERVICE_ID';
const _templateId = 'YOUR_TEMPLATE_ID';
const _publicKey = 'YOUR_PUBLIC_KEY';

class EmailService {
  static Future<void> sendBookingReceipt({
    required Map<String, dynamic> booking,
    required Map<String, dynamic> resource,
    required String guestName,
    required String guestPhone,
    required String guestEmail,
    required String reason,
  }) async {
    if (_publicKey == 'YOUR_PUBLIC_KEY') return;
    final fmt = DateFormat('EEE d MMM yyyy, HH:mm');
    final start = DateTime.tryParse(booking['start_time'] ?? '')?.toLocal();
    final end = DateTime.tryParse(booking['end_time'] ?? '')?.toLocal();
    final price = double.tryParse(resource['price']?.toString() ?? '0') ?? 0;
    try {
      await emailjs.send(
        _serviceId, _templateId,
        {
          'to_email': guestEmail,
          'to_name': guestName,
          'booking_id': '${booking['id'] ?? 'N/A'}',
          'resource_name': resource['name'] ?? '',
          'resource_category': resource['category'] ?? '',
          'organisation': resource['organisation_name'] ?? '',
          'from_time': start != null ? fmt.format(start) : '-',
          'to_time': end != null ? DateFormat('HH:mm').format(end) : '-',
          'amount': price == 0 ? 'Free' : 'MWK ${price.toStringAsFixed(2)}',
          'status': booking['status'] ?? 'Issued',
          'guest_phone': guestPhone,
          'reason': reason,
          'qr_token': booking['qr_token'] ?? '',
        },
        const emailjs.Options(publicKey: _publicKey),
      );
    } catch (_) {}
  }
}
