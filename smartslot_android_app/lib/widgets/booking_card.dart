import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../theme.dart';

class BookingCard extends StatelessWidget {
  final Map<String, dynamic> booking;
  final VoidCallback? onTap;

  const BookingCard({super.key, required this.booking, this.onTap});

  Color _statusColor(String status) {
    switch (status) {
      case 'Pending':
        return AppColors.warning;
      case 'Issued':
        return AppColors.primary;
      case 'Verified':
        return AppColors.success;
      case 'Completed':
        return AppColors.textMuted;
      case 'Cancelled':
        return AppColors.error;
      case 'NoShow':
        return AppColors.error;
      default:
        return AppColors.textMuted;
    }
  }

  @override
  Widget build(BuildContext context) {
    final status = booking['status'] ?? 'Pending';
    final statusColor = _statusColor(status);
    final fmt = DateFormat('dd MMM yyyy, hh:mm a');

    DateTime? start, end;
    try {
      start = DateTime.parse(booking['start_time']);
      end = DateTime.parse(booking['end_time']);
    } catch (_) {}

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      booking['resource_name'] ?? 'Resource',
                      style: Theme.of(context).textTheme.titleLarge,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusColor.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(6),
                      border:
                          Border.all(color: statusColor.withOpacity(0.5)),
                    ),
                    child: Text(
                      status,
                      style: TextStyle(
                          color: statusColor,
                          fontSize: 12,
                          fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Chip(label: Text(booking['resource_category'] ?? '')),
              const SizedBox(height: 8),
              if (start != null)
                _InfoRow(
                    icon: Icons.play_circle_outline,
                    text: fmt.format(start.toLocal())),
              if (end != null)
                _InfoRow(
                    icon: Icons.stop_circle_outlined,
                    text: fmt.format(end.toLocal())),
              if (booking['resource_price'] != null) ...[
                const SizedBox(height: 4),
                _InfoRow(
                  icon: Icons.payments_outlined,
                  text: double.tryParse(
                              booking['resource_price'].toString()) ==
                          0
                      ? 'Free'
                      : 'MWK ${booking['resource_price']}',
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String text;
  const _InfoRow({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        children: [
          Icon(icon, color: AppColors.textMuted, size: 15),
          const SizedBox(width: 6),
          Text(text,
              style: const TextStyle(
                  color: AppColors.textMuted, fontSize: 13)),
        ],
      ),
    );
  }
}
