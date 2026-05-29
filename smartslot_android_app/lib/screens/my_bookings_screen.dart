import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../services/api_service.dart';
import '../services/pdf_receipt_service.dart';
import '../theme.dart';
import '../transitions.dart';
import 'booking_detail_screen.dart';

class MyBookingsScreen extends StatefulWidget {
  const MyBookingsScreen({super.key});
  @override
  State<MyBookingsScreen> createState() => _MyBookingsScreenState();
}

class _MyBookingsScreenState extends State<MyBookingsScreen> with TickerProviderStateMixin {
  List<dynamic> _bookings = [];
  bool _loading = true;
  String? _error;
  late TabController _tabs;
  late List<String> _filters;
  late AnimationController _statsAnimController;
  int _selectedFilter = 0;

  @override
  void initState() {
    super.initState();
    _filters = ['All Bookings', 'Boardrooms', 'Vehicles', 'Halls', 'Others'];
    _tabs = TabController(length: _filters.length, vsync: this);
    _statsAnimController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _load();
  }

  @override
  void dispose() {
    _tabs.dispose();
    _statsAnimController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await ApiService.get('/api/bookings/my/');
      if (res.statusCode == 200) {
        setState(() => _bookings = jsonDecode(res.body));
        _statsAnimController.forward(from: 0.0);
      } else {
        setState(() => _error = 'Failed to load bookings');
      }
    } catch (e) { setState(() => _error = 'Connection error'); }
    finally { setState(() => _loading = false); }
  }

  int _countByStatus(String status) {
    if (status == 'All Bookings') return _bookings.length;
    final typeMap = {
      'Boardrooms': 'Boardroom',
      'Vehicles': 'Vehicle',
      'Halls': 'Hall',
      'Others': 'Other'
    };
    final bookingType = typeMap[status];
    return _bookings.where((b) => b['booking_type'] == bookingType || b['resource_type'] == bookingType).length;
  }

  int _countByStatusType(String statusType) {
    return _bookings.where((b) => b['status'] == statusType).length;
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
    final res = await ApiService.patch('/api/bookings/$id/', {'status': 'Cancelled'});
    if (res.statusCode == 200) _load();
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

  List<dynamic> _filtered(String filter) {
    if (filter == 'All Bookings') return _bookings;
    final typeMap = {
      'Flights': 'Flight',
      'Hotel': 'Hotel',
      'Trains': 'Train',
      'Villas & Apt': 'Apartment'
    };
    final bookingType = typeMap[filter];
    return _bookings.where((b) => b['booking_type'] == bookingType || b['resource_type'] == bookingType).isNotEmpty 
      ? _bookings.where((b) => b['booking_type'] == bookingType || b['resource_type'] == bookingType).toList()
      : [];
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
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        elevation: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('My Bookings'),
            Text(
              'Manage and track of your bookings',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.textTheme.bodySmall?.color?.withOpacity(0.7),
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () {},
          ),
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(
              child: Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: colorScheme.primary.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(Icons.person_outline, color: colorScheme.primary, size: 20),
              ),
            ),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
          : _error != null
              ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text(_error!, style: theme.textTheme.bodyMedium),
                  const SizedBox(height: 12),
                  OutlinedButton(onPressed: _load, child: const Text('Retry')),
                ]))
              : SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                                                    // header removed to match app context (style retained)
                            const SizedBox(height: 16),
                            GridView(
                              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                                crossAxisCount: 2,
                                childAspectRatio: 1.1,
                                crossAxisSpacing: 12,
                                mainAxisSpacing: 12,
                              ),
                              shrinkWrap: true,
                              physics: const NeverScrollableScrollPhysics(),
                              children: [
                                _buildStatCard(
                                  theme,
                                  colorScheme,
                                  _countByStatusType('Issued'),
                                  'Upcoming',
                                  Icons.schedule_outlined,
                                  colorScheme.primary,
                                  0,
                                ),
                                _buildStatCard(
                                  theme,
                                  colorScheme,
                                  _countByStatusType('Completed'),
                                  'Completed',
                                  Icons.check_circle_outline,
                                  Colors.green,
                                  1,
                                ),
                                _buildStatCard(
                                  theme,
                                  colorScheme,
                                  _countByStatusType('Cancelled'),
                                  'Cancelled',
                                  Icons.cancel_outlined,
                                  Colors.red,
                                  2,
                                ),
                                _buildStatCard(
                                  theme,
                                  colorScheme,
                                  _bookings.length,
                                  'Total Bookings',
                                  Icons.inbox_outlined,
                                  Colors.orange,
                                  3,
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 20),
                        child: SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                            children: List.generate(
                              _filters.length,
                              (index) => Padding(
                                padding: const EdgeInsets.only(right: 8),
                                child: AnimatedContainer(
                                  duration: const Duration(milliseconds: 300),
                                  child: FilterChip(
                                    selected: _selectedFilter == index,
                                    onSelected: (selected) {
                                      setState(() => _selectedFilter = index);
                                      _tabs.animateTo(index);
                                    },
                                    backgroundColor: isDark
                                        ? Colors.grey.shade800
                                        : Colors.grey.shade200,
                                    selectedColor: colorScheme.primary,
                                    label: Text(
                                      _filters[index],
                                      style: TextStyle(
                                        color: _selectedFilter == index
                                            ? Colors.white
                                            : (isDark
                                                ? Colors.white70
                                                : Colors.grey.shade700),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 20),
                        child: Text(
                          _countByStatus(_filters[_selectedFilter]) > 0
                              ? 'Your Bookings'
                              : 'No bookings',
                          style: theme.textTheme.titleMedium,
                        ),
                      ),
                      const SizedBox(height: 12),
                      _buildBookingsList(),
                      const SizedBox(height: 20),
                    ],
                  ),
                ),
    );
  }

  Widget _buildStatCard(ThemeData theme, ColorScheme colorScheme, int count, String label, IconData icon, Color iconColor, int index) {
    return ScaleTransition(
      scale: Tween<double>(begin: 0.8, end: 1.0).animate(
        CurvedAnimation(
          parent: _statsAnimController,
          curve: Interval(index * 0.15, 0.7 + (index * 0.1), curve: Curves.easeOut),
        ),
      ),
      child: GestureDetector(
        onTap: () {},
        child: Container(
          decoration: BoxDecoration(
            color: theme.cardColor,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: theme.dividerColor,
              width: 0.5,
            ),
            boxShadow: [
              BoxShadow(
                color: iconColor.withOpacity(0.1),
                blurRadius: 16,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: iconColor.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, color: iconColor, size: 20),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      count.toString(),
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: colorScheme.primary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      label,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.textTheme.bodySmall?.color?.withOpacity(0.6),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBookingsList() {
    final list = _filtered(_filters[_selectedFilter]);
    
    if (list.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.calendar_today_outlined,
                color: AppColors.textMuted,
                size: 48,
              ),
              const SizedBox(height: 12),
              Text(
                'No ${_filters[_selectedFilter]} bookings',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _load,
      color: AppColors.primary,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: list.length,
        itemBuilder: (ctx, i) => AnimatedOpacity(
          opacity: 1.0,
          duration: Duration(milliseconds: 300 + (i * 100)),
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0.3, 0),
              end: Offset.zero,
            ).animate(
              CurvedAnimation(
                parent: _statsAnimController,
                curve: Interval(0.3 + (i * 0.1), 1.0, curve: Curves.easeOut),
              ),
            ),
            child: Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: GestureDetector(
                onTap: () => Navigator.push(context, SlideUpRoute(page: BookingDetailScreen(booking: list[i]))),
                onLongPress: () => _showBookingActions(list[i]),
                child: _BookingTile(
                  booking: list[i],
                  onDetails: () => Navigator.push(context, SlideUpRoute(page: BookingDetailScreen(booking: list[i]))),
                  onManage: () => _showBookingActions(list[i]),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _BookingTile extends StatelessWidget {
  final Map<String, dynamic> booking;
  final VoidCallback onDetails;
  final VoidCallback onManage;

  const _BookingTile({required this.booking, required this.onDetails, required this.onManage});

  String _getStatusLabel(String? status) {
    switch (status) {
      case 'Issued':
        return 'Upcoming';
      case 'Completed':
        return 'Completed';
      case 'Cancelled':
        return 'Cancelled';
      default:
        return status ?? 'Pending';
    }
  }

  Color _getStatusColor(BuildContext context, String? status) {
    final theme = Theme.of(context);
    switch (status) {
      case 'Issued':
        return const Color(0xFF00C46F);
      case 'Completed':
        return const Color(0xFF00C46F);
      case 'Cancelled':
        return Colors.red.shade400;
      default:
        return theme.colorScheme.primary;
    }
  }

  Widget _categoryFallback(Map<String, dynamic> booking, ThemeData theme) {
    final category = (booking['resource_category'] ?? booking['resource_type'] ?? '').toString().toLowerCase();
    final name = (booking['resource_name'] ?? '').toString().toLowerCase();
    String? assetPath;

    if (category.contains('board') || category.contains('meeting') || category.contains('room') || name.contains('board') || name.contains('room')) {
      assetPath = 'assets/images/boardroom.avif';
    } else if (category.contains('vehicle') || name.contains('hilux') || name.contains('toyota') || name.contains('pajero') || name.contains('corolla')) {
      assetPath = 'assets/images/vehicle.avif';
    } else if (name.contains('laptop') || name.contains('computer')) {
      assetPath = 'assets/images/laptops.avif';
    } else if (name.contains('generator')) {
      assetPath = 'assets/images/generator.avif';
    } else if (name.contains('camera') || name.contains('canon') || name.contains('r50')) {
      assetPath = 'assets/images/laptops.avif'; // equipment fallback
    } else if (name.contains('projector') || name.contains('sony') || name.contains('epson')) {
      assetPath = 'assets/images/laptops.avif'; // equipment fallback
    } else if (name.contains('chair')) {
      assetPath = 'assets/images/chairs.jpg';
    }

    if (assetPath != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: Image.asset(
          assetPath,
          fit: BoxFit.cover,
          width: 80,
          height: 80,
          errorBuilder: (_, __, ___) => _iconFallback(category, theme),
        ),
      );
    }
    return _iconFallback(category, theme);
  }

  Widget _iconFallback(String category, ThemeData theme) {
    IconData icon;
    if (category.contains('vehicle') || category.contains('car')) {
      icon = Icons.directions_car_outlined;
    } else if (category.contains('hall') || category.contains('event')) {
      icon = Icons.event_outlined;
    } else if (category.contains('laptop') || category.contains('equipment')) {
      icon = Icons.laptop_outlined;
    } else {
      icon = Icons.meeting_room_outlined;
    }
    return Icon(icon, color: theme.colorScheme.primary, size: 40);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final status = booking['status'];
    final statusColor = _getStatusColor(context, status);

    return GestureDetector(
      onTap: onDetails,
      child: Container(
        decoration: BoxDecoration(
          color: theme.cardColor,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: theme.dividerColor,
            width: 0.5,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Row(
                children: [
                  Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      color: theme.colorScheme.primary.withOpacity(0.1),
                    ),
                    child: () {
                      final rawImage = booking['photo_url'] as String?
                          ?? booking['image_url'] as String?;
                      final imageUrl = rawImage != null && rawImage.isNotEmpty
                          ? rawImage
                          : null;
                      if (imageUrl != null) {
                        return ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.network(
                            imageUrl,
                            fit: BoxFit.cover,
                            width: 80,
                            height: 80,
                            errorBuilder: (_, __, ___) => _categoryFallback(booking, theme),
                          ),
                        );
                      }
                      return _categoryFallback(booking, theme);
                    }(),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Text(
                                booking['resource_name'] ?? 'Unknown',
                                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: statusColor.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                _getStatusLabel(status),
                                style: theme.textTheme.labelSmall?.copyWith(
                                  color: statusColor,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          booking['organisation_name'] ?? booking['location'] ?? '',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.textTheme.bodySmall?.color?.withOpacity(0.6),
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _DetailItem(
                      label: 'Date',
                      value: () {
                        final raw = booking['start_time'] as String?;
                        if (raw == null || raw.isEmpty) return 'N/A';
                        final dt = DateTime.tryParse(raw)?.toLocal();
                        if (dt == null) return raw;
                        final months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                        return '${dt.day} ${months[dt.month - 1]} ${dt.year}';
                      }(),
                    ),
                  ),
                  Expanded(
                    child: _DetailItem(
                      label: 'Booking ID',
                      value: 'BK-${booking['id']}',
                    ),
                  ),
                  Expanded(
                    child: _DetailItem(
                      label: 'Type',
                      value: booking['resource_category'] ?? booking['resource_type'] ?? booking['booking_type'] ?? 'N/A',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    () {
                      final price = double.tryParse(booking['resource_price']?.toString() ?? '');
                      if (price == null) return 'Free';
                      if (price == 0) return 'Free';
                      return 'MWK ${price.toStringAsFixed(2)}';
                    }(),
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  Row(
                    children: [
                      OutlinedButton.icon(
                        onPressed: onDetails,
                        icon: const Icon(Icons.visibility_outlined, size: 16),
                        label: const Text('View Details'),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        ),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton(
                        onPressed: onManage,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: theme.colorScheme.primary,
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        ),
                        child: const Text('Manage'),
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DetailItem extends StatelessWidget {
  final String label;
  final String value;

  const _DetailItem({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.textTheme.bodySmall?.color?.withOpacity(0.5),
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: theme.textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w500,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ],
    );
  }
}
