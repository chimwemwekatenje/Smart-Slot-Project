import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../services/api_service.dart';
import '../theme.dart';

class ResourceCard extends StatelessWidget {
  final Map<String, dynamic> resource;
  final VoidCallback onTap;
  final bool isExternal;
  final bool isEmployee;

  const ResourceCard({
    super.key,
    required this.resource,
    required this.onTap,
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

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (photoUrl != null)
              ClipRRect(
                borderRadius:
                    const BorderRadius.vertical(top: Radius.circular(12)),
                child: CachedNetworkImage(
                  imageUrl: photoUrl,
                  height: 150,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  placeholder: (_, _) => _placeholder(height: 150),
                  errorWidget: (_, _, _) => _placeholder(height: 150),
                ),
              )
            else
              _placeholder(height: 110),
            Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(
                          resource['name'] ?? '',
                          style: Theme.of(context).textTheme.titleLarge,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      // Hide price for employees — it's their own org's resource
                      if (!isEmployee)
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(
                                color: AppColors.primary.withValues(alpha: 0.4)),
                          ),
                          child: Text(
                            price == 0
                                ? 'Free'
                                : 'MWK ${price.toStringAsFixed(0)}',
                            style: const TextStyle(
                                color: AppColors.primary,
                                fontSize: 12,
                                fontWeight: FontWeight.w600),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Chip(
                        label: Text(resource['category'] ?? ''),
                        padding: EdgeInsets.zero,
                        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      const Spacer(),
                      // External: show "Contact" badge; Employee: show "Book" badge
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: isExternal
                              ? AppColors.warning.withValues(alpha: 0.15)
                              : AppColors.success.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(
                            color: isExternal
                                ? AppColors.warning.withValues(alpha: 0.5)
                                : AppColors.success.withValues(alpha: 0.5),
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              isExternal
                                  ? Icons.contact_phone_outlined
                                  : Icons.event_available_outlined,
                              size: 12,
                              color: isExternal
                                  ? AppColors.warning
                                  : AppColors.success,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              isExternal ? 'Contact' : 'Book',
                              style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: isExternal
                                      ? AppColors.warning
                                      : AppColors.success),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  if (resource['description'] != null &&
                      resource['description'].toString().isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      resource['description'],
                      style: Theme.of(context).textTheme.bodyMedium,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                  const SizedBox(height: 8),
                  Row(children: [
                    const Icon(Icons.business_outlined,
                        size: 13, color: AppColors.textMuted),
                    const SizedBox(width: 4),
                    Text(
                      resource['organisation_name'] ?? '',
                      style: const TextStyle(
                          color: AppColors.textMuted, fontSize: 12),
                    ),
                  ]),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _placeholder({double height = 110}) {
    return ClipRRect(
      borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
      child: Container(
        height: height,
        width: double.infinity,
        color: AppColors.border,
        child: const Icon(Icons.meeting_room_outlined,
            color: AppColors.textMuted, size: 40),
      ),
    );
  }
}
