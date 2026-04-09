import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../theme.dart';

class BookingFormScreen extends StatefulWidget {
  final Map<String, dynamic> resource;
  const BookingFormScreen({super.key, required this.resource});

  @override
  State<BookingFormScreen> createState() => _BookingFormScreenState();
}

class _BookingFormScreenState extends State<BookingFormScreen> {
  late DateTime _weekStart;
  List<dynamic> _bookings = [];
  bool _loadingSchedule = true;

  DateTime? _selectedStart;
  DateTime? _selectedEnd;

  static const int _dayStart = 7;
  static const int _dayEnd = 20;

  final _dateFmt = DateFormat('EEE d MMM');
  final _timeFmt = DateFormat('HH:mm');

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _weekStart = now.subtract(Duration(days: now.weekday - 1));
    _weekStart = DateTime(_weekStart.year, _weekStart.month, _weekStart.day);
    _loadSchedule();
  }

  Future<void> _loadSchedule() async {
    setState(() => _loadingSchedule = true);
    try {
      final id = widget.resource['id'];
      final weekStr = DateFormat('yyyy-MM-dd').format(_weekStart);
      final res = await ApiService.get(
          '/api/resources/$id/schedule/?week_start=$weekStr');
      if (res.statusCode == 200) {
        setState(() => _bookings = jsonDecode(res.body));
      }
    } catch (_) {}
    setState(() => _loadingSchedule = false);
  }

  void _prevWeek() {
    setState(() {
      _weekStart = _weekStart.subtract(const Duration(days: 7));
      _selectedStart = null;
      _selectedEnd = null;
    });
    _loadSchedule();
  }

  void _nextWeek() {
    setState(() {
      _weekStart = _weekStart.add(const Duration(days: 7));
      _selectedStart = null;
      _selectedEnd = null;
    });
    _loadSchedule();
  }

  bool _isBooked(DateTime slot) {
    for (final b in _bookings) {
      final start = DateTime.parse(b['start_time']).toLocal();
      final end = DateTime.parse(b['end_time']).toLocal();
      if (slot.isAfter(start.subtract(const Duration(minutes: 1))) &&
          slot.isBefore(end)) {
        return true;
      }
    }
    return false;
  }

  bool _isSelected(DateTime slot) {
    if (_selectedStart == null) return false;
    final end = _selectedEnd ?? _selectedStart!.add(const Duration(hours: 1));
    return slot.isAtSameMomentAs(_selectedStart!) ||
        (slot.isAfter(_selectedStart!) && slot.isBefore(end));
  }

  void _onSlotTap(DateTime slot) {
    if (_isBooked(slot)) return;
    setState(() {
      if (_selectedStart == null) {
        _selectedStart = slot;
        _selectedEnd = slot.add(const Duration(hours: 1));
      } else if (slot.isAtSameMomentAs(_selectedStart!)) {
        _selectedStart = null;
        _selectedEnd = null;
      } else if (slot.isAfter(_selectedStart!)) {
        _selectedEnd = slot.add(const Duration(hours: 1));
      } else {
        _selectedStart = slot;
        _selectedEnd = slot.add(const Duration(hours: 1));
      }
    });
  }

  void _onConfirmTap() {
    if (_selectedStart == null) return;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => _BookingDetailsSheet(
        resource: widget.resource,
        selectedStart: _selectedStart!,
        selectedEnd: _selectedEnd!,
        onBooked: (booking) {
          Navigator.pop(context); // close sheet
          _showReceipt(booking);
        },
      ),
    );
  }

  void _showReceipt(Map<String, dynamic> booking) {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => BookingReceiptScreen(booking: booking),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isEmployee = context.read<AuthProvider>().isEmployee;
    final weekEnd = _weekStart.add(const Duration(days: 6));

    return Scaffold(
      appBar: AppBar(title: const Text('Book Resource')),
      body: Column(
        children: [
          // Resource summary
          Container(
            margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(10),
              border: const Border.fromBorderSide(
                  BorderSide(color: AppColors.border)),
            ),
            child: Row(children: [
              const Icon(Icons.meeting_room_outlined,
                  color: AppColors.primary, size: 28),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(widget.resource['name'] ?? '',
                        style: Theme.of(context).textTheme.titleLarge),
                    Text(widget.resource['category'] ?? '',
                        style: Theme.of(context).textTheme.bodyMedium),
                  ],
                ),
              ),
              if (!isEmployee) ...[
                const SizedBox(width: 8),
                Text(
                  () {
                    final p = double.tryParse(
                            widget.resource['price']?.toString() ?? '0') ??
                        0;
                    return p == 0 ? 'Free' : 'MWK ${p.toStringAsFixed(0)}';
                  }(),
                  style: const TextStyle(
                      color: AppColors.primary, fontWeight: FontWeight.bold),
                ),
              ],
            ]),
          ),

          // Week navigation
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(children: [
              IconButton(
                onPressed: _prevWeek,
                icon: const Icon(Icons.chevron_left, color: AppColors.primary),
                padding: EdgeInsets.zero,
              ),
              Expanded(
                child: Text(
                  '${_dateFmt.format(_weekStart)} – ${_dateFmt.format(weekEnd)}',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w600),
                ),
              ),
              IconButton(
                onPressed: _nextWeek,
                icon:
                    const Icon(Icons.chevron_right, color: AppColors.primary),
                padding: EdgeInsets.zero,
              ),
            ]),
          ),

          // Legend
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(children: [
              _LegendDot(color: AppColors.surface, label: 'Available'),
              const SizedBox(width: 16),
              _LegendDot(
                  color: AppColors.error.withValues(alpha: 0.7),
                  label: 'Booked'),
              const SizedBox(width: 16),
              _LegendDot(color: AppColors.primary, label: 'Your selection'),
            ]),
          ),
          const SizedBox(height: 8),

          // Timetable
          Expanded(
            child: _loadingSchedule
                ? const Center(
                    child:
                        CircularProgressIndicator(color: AppColors.primary))
                : _Timetable(
                    weekStart: _weekStart,
                    dayStart: _dayStart,
                    dayEnd: _dayEnd,
                    isBooked: _isBooked,
                    isSelected: _isSelected,
                    onSlotTap: _onSlotTap,
                    timeFmt: _timeFmt,
                    dateFmt: _dateFmt,
                  ),
          ),

          // Bottom bar
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              color: AppColors.surface,
              border: Border(top: BorderSide(color: AppColors.border)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (_selectedStart != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Row(children: [
                      const Icon(Icons.schedule,
                          color: AppColors.primary, size: 16),
                      const SizedBox(width: 6),
                      Text(
                        '${DateFormat('EEE d MMM, HH:mm').format(_selectedStart!)} → ${_timeFmt.format(_selectedEnd!)}',
                        style: const TextStyle(
                            color: AppColors.primary,
                            fontWeight: FontWeight.w600),
                      ),
                    ]),
                  )
                else
                  const Padding(
                    padding: EdgeInsets.only(bottom: 10),
                    child: Text(
                      'Tap a slot to select your booking time',
                      style: TextStyle(
                          color: AppColors.textMuted, fontSize: 13),
                    ),
                  ),
                ElevatedButton(
                  onPressed: _selectedStart == null ? null : _onConfirmTap,
                  child: const Text('Confirm Booking'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Bottom sheet: department + reason form ───────────────────────────────────

class _BookingDetailsSheet extends StatefulWidget {
  final Map<String, dynamic> resource;
  final DateTime selectedStart;
  final DateTime selectedEnd;
  final void Function(Map<String, dynamic> booking) onBooked;

  const _BookingDetailsSheet({
    required this.resource,
    required this.selectedStart,
    required this.selectedEnd,
    required this.onBooked,
  });

  @override
  State<_BookingDetailsSheet> createState() => _BookingDetailsSheetState();
}

class _BookingDetailsSheetState extends State<_BookingDetailsSheet> {
  final _formKey = GlobalKey<FormState>();
  final _deptCtrl = TextEditingController();
  final _reasonCtrl = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _deptCtrl.dispose();
    _reasonCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = null; });
    try {
      final res = await ApiService.post('/api/bookings/', {
        'resource': widget.resource['id'],
        'start_time': widget.selectedStart.toUtc().toIso8601String(),
        'end_time': widget.selectedEnd.toUtc().toIso8601String(),
        'custom_data': {
          'department': _deptCtrl.text.trim(),
          'reason': _reasonCtrl.text.trim(),
        },
      });
      if (!mounted) return;
      if (res.statusCode == 201) {
        widget.onBooked(jsonDecode(res.body));
      } else {
        final err = jsonDecode(res.body);
        final msg = err is Map ? err.values.first : err.toString();
        setState(() => _error = msg is List ? msg.first : msg.toString());
      }
    } catch (e) {
      setState(() => _error = 'Connection error. Check your network.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final fmt = DateFormat('EEE d MMM, HH:mm');
    return Padding(
      padding: EdgeInsets.only(
        left: 20, right: 20, top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Handle
            Center(
              child: Container(
                width: 40, height: 4,
                decoration: BoxDecoration(
                    color: AppColors.border,
                    borderRadius: BorderRadius.circular(2)),
              ),
            ),
            const SizedBox(height: 16),
            Text('Booking Details',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            // Time summary
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(top: 8, bottom: 16),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                    color: AppColors.primary.withValues(alpha: 0.3)),
              ),
              child: Row(children: [
                const Icon(Icons.schedule,
                    color: AppColors.primary, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '${widget.resource['name']}  •  ${fmt.format(widget.selectedStart)} → ${DateFormat('HH:mm').format(widget.selectedEnd)}',
                    style: const TextStyle(
                        color: AppColors.primary,
                        fontSize: 13,
                        fontWeight: FontWeight.w500),
                  ),
                ),
              ]),
            ),
            if (_error != null)
              Container(
                padding: const EdgeInsets.all(10),
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: AppColors.error.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                      color: AppColors.error.withValues(alpha: 0.4)),
                ),
                child: Text(_error!,
                    style: const TextStyle(
                        color: AppColors.error, fontSize: 13)),
              ),
            TextFormField(
              controller: _deptCtrl,
              decoration: const InputDecoration(
                labelText: 'Department',
                hintText: 'e.g. Finance, HR, IT',
                prefixIcon: Icon(Icons.corporate_fare_outlined,
                    color: AppColors.textMuted),
              ),
              validator: (v) =>
                  v!.trim().isEmpty ? 'Please enter your department' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _reasonCtrl,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: 'Reason for booking',
                hintText: 'Briefly describe why you need this resource',
                alignLabelWithHint: true,
                prefixIcon: Padding(
                  padding: EdgeInsets.only(bottom: 44),
                  child: Icon(Icons.notes_outlined,
                      color: AppColors.textMuted),
                ),
              ),
              validator: (v) =>
                  v!.trim().isEmpty ? 'Please provide a reason' : null,
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _loading ? null : _submit,
              child: _loading
                  ? const SizedBox(
                      height: 20, width: 20,
                      child: CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2))
                  : const Text('Submit Booking'),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Receipt screen ───────────────────────────────────────────────────────────

class BookingReceiptScreen extends StatelessWidget {
  final Map<String, dynamic> booking;
  const BookingReceiptScreen({super.key, required this.booking});

  @override
  Widget build(BuildContext context) {
    final fmt = DateFormat('EEE d MMM yyyy, HH:mm');
    final customData = booking['custom_data'] as Map<String, dynamic>? ?? {};
    final qrToken = booking['qr_token'] ?? booking['id'].toString();
    final start = DateTime.tryParse(booking['start_time'] ?? '')?.toLocal();
    final end = DateTime.tryParse(booking['end_time'] ?? '')?.toLocal();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Booking Confirmed'),
        automaticallyImplyLeading: false,
        actions: [
          TextButton(
            onPressed: () =>
                Navigator.popUntil(context, (r) => r.isFirst),
            child: const Text('Done',
                style: TextStyle(color: AppColors.primary)),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Success banner
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.success.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                    color: AppColors.success.withValues(alpha: 0.4)),
              ),
              child: const Column(children: [
                Icon(Icons.check_circle_outline,
                    color: AppColors.success, size: 40),
                SizedBox(height: 8),
                Text('Booking Confirmed!',
                    style: TextStyle(
                        color: AppColors.success,
                        fontSize: 18,
                        fontWeight: FontWeight.bold)),
                SizedBox(height: 4),
                Text('Show the QR code below at the entrance',
                    style: TextStyle(
                        color: AppColors.textMuted, fontSize: 13)),
              ]),
            ),
            const SizedBox(height: 24),

            // QR Code
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
              ),
              child: QrImageView(
                data: qrToken,
                version: QrVersions.auto,
                size: 200,
                backgroundColor: Colors.white,
              ),
            ),
            const SizedBox(height: 8),
            Text('Booking ID: #${booking['id']}',
                style: const TextStyle(
                    color: AppColors.textMuted, fontSize: 12)),
            const SizedBox(height: 24),

            // Receipt card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(12),
                border: const Border.fromBorderSide(
                    BorderSide(color: AppColors.border)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('BOOKING RECEIPT',
                      style: TextStyle(
                          color: AppColors.textMuted,
                          fontSize: 11,
                          letterSpacing: 1.2,
                          fontWeight: FontWeight.w600)),
                  const Divider(height: 20),
                  _ReceiptRow(
                      label: 'Resource',
                      value: booking['resource_name'] ?? '-'),
                  _ReceiptRow(
                      label: 'Category',
                      value: booking['resource_category'] ?? '-'),
                  _ReceiptRow(
                      label: 'Organisation',
                      value: booking['organisation_name'] ?? '-'),
                  _ReceiptRow(
                      label: 'Booked by',
                      value: booking['booked_by'] ?? '-'),
                  _ReceiptRow(
                      label: 'Department',
                      value: customData['department'] ?? '-'),
                  _ReceiptRow(
                      label: 'Reason',
                      value: customData['reason'] ?? '-'),
                  const Divider(height: 20),
                  if (start != null)
                    _ReceiptRow(label: 'From', value: fmt.format(start)),
                  if (end != null)
                    _ReceiptRow(
                        label: 'To',
                        value: DateFormat('HH:mm').format(end)),
                  const Divider(height: 20),
                  _ReceiptRow(
                    label: 'Status',
                    value: booking['status'] ?? 'Pending',
                    valueColor: AppColors.warning,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.home_outlined),
                label: const Text('Back to Home'),
                onPressed: () =>
                    Navigator.popUntil(context, (r) => r.isFirst),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ReceiptRow extends StatelessWidget {
  final String label;
  final String value;
  final Color? valueColor;
  const _ReceiptRow(
      {required this.label, required this.value, this.valueColor});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(label,
                style: const TextStyle(
                    color: AppColors.textMuted, fontSize: 13)),
          ),
          Expanded(
            child: Text(value,
                style: TextStyle(
                    color: valueColor ?? AppColors.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }
}

// ─── Timetable widget ─────────────────────────────────────────────────────────

class _Timetable extends StatelessWidget {
  final DateTime weekStart;
  final int dayStart;
  final int dayEnd;
  final bool Function(DateTime) isBooked;
  final bool Function(DateTime) isSelected;
  final void Function(DateTime) onSlotTap;
  final DateFormat timeFmt;
  final DateFormat dateFmt;

  const _Timetable({
    required this.weekStart,
    required this.dayStart,
    required this.dayEnd,
    required this.isBooked,
    required this.isSelected,
    required this.onSlotTap,
    required this.timeFmt,
    required this.dateFmt,
  });

  @override
  Widget build(BuildContext context) {
    final days = List.generate(7, (i) => weekStart.add(Duration(days: i)));
    final hours = List.generate(dayEnd - dayStart, (i) => dayStart + i);
    const timeColW = 44.0;
    const slotH = 44.0;
    const dayColW = 52.0;

    return SingleChildScrollView(
      scrollDirection: Axis.vertical,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Day headers
            Row(children: [
              SizedBox(width: timeColW),
              ...days.map((d) => Container(
                    width: dayColW,
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    alignment: Alignment.center,
                    decoration: const BoxDecoration(
                      border: Border(
                          bottom: BorderSide(color: AppColors.border)),
                    ),
                    child: Column(children: [
                      Text(
                        DateFormat('EEE').format(d),
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: _isToday(d)
                              ? AppColors.primary
                              : AppColors.textMuted,
                        ),
                      ),
                      Text(
                        DateFormat('d').format(d),
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: _isToday(d)
                              ? AppColors.primary
                              : AppColors.textPrimary,
                        ),
                      ),
                    ]),
                  )),
            ]),
            // Hour rows
            ...hours.map((hour) {
              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: timeColW,
                    height: slotH,
                    child: Padding(
                      padding: const EdgeInsets.only(right: 6, top: 4),
                      child: Text(
                        '${hour.toString().padLeft(2, '0')}:00',
                        textAlign: TextAlign.right,
                        style: const TextStyle(
                            color: AppColors.textMuted, fontSize: 11),
                      ),
                    ),
                  ),
                  ...days.map((day) {
                    final slot =
                        DateTime(day.year, day.month, day.day, hour);
                    final booked = isBooked(slot);
                    final selected = isSelected(slot);
                    final isPast = slot.isBefore(DateTime.now());

                    Color bg;
                    if (selected) {
                      bg = AppColors.primary;
                    } else if (booked) {
                      bg = AppColors.error.withValues(alpha: 0.65);
                    } else if (isPast) {
                      bg = AppColors.border.withValues(alpha: 0.4);
                    } else {
                      bg = AppColors.surface;
                    }

                    return GestureDetector(
                      onTap: (booked || isPast) ? null : () => onSlotTap(slot),
                      child: Container(
                        width: dayColW,
                        height: slotH,
                        decoration: BoxDecoration(
                          color: bg,
                          border: Border.all(
                              color:
                                  AppColors.border.withValues(alpha: 0.4),
                              width: 0.5),
                        ),
                        child: booked
                            ? const Center(
                                child: Icon(Icons.block,
                                    size: 14, color: Colors.white54))
                            : selected
                                ? const Center(
                                    child: Icon(Icons.check,
                                        size: 14, color: Colors.white))
                                : null,
                      ),
                    );
                  }),
                ],
              );
            }),
          ],
        ),
      ),
    );
  }

  bool _isToday(DateTime d) {
    final now = DateTime.now();
    return d.year == now.year && d.month == now.month && d.day == now.day;
  }
}

class _LegendDot extends StatelessWidget {
  final Color color;
  final String label;
  const _LegendDot({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Container(
        width: 12, height: 12,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(3),
          border: Border.all(color: AppColors.border),
        ),
      ),
      const SizedBox(width: 4),
      Text(label,
          style: const TextStyle(
              color: AppColors.textMuted, fontSize: 11)),
    ]);
  }
}
