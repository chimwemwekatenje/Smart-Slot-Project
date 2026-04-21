import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../services/api_service.dart';
import '../theme.dart';
import 'booking_form_screen.dart';
import 'external_booking_screen.dart';

class ResourceDetailScreen extends StatelessWidget {
  final Map<String, dynamic> resource;
  final bool isExternal;
  final bool isEmployee;

  const ResourceDetailScreen({
    super.key,
    required this.resource,
    this.isExternal = false,
    this.isEmployee = false,
  });

  @override
  Widget build(BuildContext context) {
    final price = double.tryParse(resource['price']?.toString() ?? '0') ?? 0;
    final photoPath = resource['photo'];
    final photoUrl = photoPath != null && photoPath.toString().isNotEmpty
        ? '${ApiService.baseUrl}/media/$photoPath'
        : null;
    final orgName = resource['organisation_name'] ?? 'Unknown Organisation';

    return Scaffold(
      appBar: AppBar(title: Text(resource['name'] ?? 'Resource')),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (photoUrl != null)
              CachedNetworkImage(
                imageUrl: photoUrl,
                height: 220,
                width: double.infinity,
                fit: BoxFit.cover,
                errorWidget: (_, _, _) => _placeholder(),
              )
            else
              _placeholder(),
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(resource['name'] ?? '',
                            style: Theme.of(context).textTheme.headlineMedium),
                      ),
                      const SizedBox(width: 12),
                      if (!isEmployee)
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 14, vertical: 6),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                                color:
                                    AppColors.primary.withValues(alpha: 0.5)),
                          ),
                          child: Text(
                            price == 0
                                ? 'Free'
                                : 'MWK ${price.toStringAsFixed(0)}',
                            style: const TextStyle(
                                color: AppColors.primary,
                                fontWeight: FontWeight.bold,
                                fontSize: 16),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Chip(label: Text(resource['category'] ?? '')),
                  const Divider(height: 28),
                  _OrgInfoCard(orgName: orgName, isExternal: isExternal),
                  const SizedBox(height: 16),
                  if (resource['description'] != null &&
                      resource['description'].toString().isNotEmpty) ...[
                    Text('About',
                        style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 8),
                    Text(resource['description'],
                        style: Theme.of(context)
                            .textTheme
                            .bodyLarge
                            ?.copyWith(height: 1.6)),
                    const SizedBox(height: 24),
                  ],
                  if (isExternal)
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.payment_outlined),
                        label: const Text('Book & Pay'),
                        onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                ExternalBookingScreen(resource: resource),
                          ),
                        ),
                      ),
                    )
                  else
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.calendar_today_outlined),
                        label: const Text('Book This Resource'),
                        onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                BookingFormScreen(resource: resource),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _placeholder() {
    return Container(
      height: 180,
      width: double.infinity,
      color: AppColors.border,
      child: const Icon(Icons.meeting_room_outlined,
          color: AppColors.textMuted, size: 64),
    );
  }
}

class _OrgInfoCard extends StatelessWidget {
  final String orgName;
  final bool isExternal;
  const _OrgInfoCard({required this.orgName, required this.isExternal});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isExternal
              ? AppColors.primary.withValues(alpha: 0.4)
              : AppColors.border,
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.business_outlined,
                color: AppColors.primary, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isExternal ? 'Provided by' : 'Organisation',
                  style: const TextStyle(
                      color: AppColors.textMuted, fontSize: 11),
                ),
                Text(orgName,
                    style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
