import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../services/api_service.dart';
import '../theme.dart';

// ─── Main stepper screen ──────────────────────────────────────────────────────

class ExternalBookingScreen extends StatefulWidget {
  final Map<String, dynamic> resource;
  const ExternalBookingScreen({super.key, required this.resource});

  @override
  State<ExternalBookingScreen> createState() => _ExternalBookingScreenState();
}

class _ExternalBookingScreenState extends State<ExternalBookingScreen> {
  int _step = 0; // 0=details, 1=timeslot, 2=payment

  // Step 1 — personal details
  final _detailsKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _reasonCtrl = TextEditingController();

  // Step 2 — time slot (same timetable logic)
  late DateTime _weekStart;
  List<dynamic> _bookings = [];
  bool _loadingSchedule = true;
  DateTime? _selectedStart;
  DateTime? _selectedEnd;
  final _dateFmt = DateFormat('EEE d MMM');
  final _timeFmt = DateFormat('HH:mm');

  // Step 3 — payment
  final _payKey = GlobalKey<FormState>();
  final _cardNameCtrl = TextEditingController();
  final _cardNumCtrl = TextEditingController();
  final _expiryCtrl = TextEditingController();
  final _cvvCtrl = TextEditingController();
  bool _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _weekStart = now.subtract(Duration(days: now.weekday - 1));
    _weekStart = DateTime(_weekStart.year, _weekStart.month, _weekStart.day);
    _loadSchedule();
  }

  @override
  void dispose() {
    _nameCtrl.dispose(); _phoneCtrl.dispose(); _emailCtrl.dispose();
    _reasonCtrl.dispose(); _cardNameCtrl.dispose(); _cardNumCtrl.dispose();
    _expiryCtrl.dispose(); _cvvCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadSchedule() async {
    setState(() => _loadingSchedule = true);
    try {
      final id = widget.resource['id'];
      final weekStr = DateFormat('yyyy-MM-dd').format(_weekStart);
      final res = await ApiService.get('/api/resources/$id/schedule/?week_start=$weekStr');
      if (res.statusCode == 200) setState(() => _bookings = jsonDecode(res.body));
    } catch (_) {}
    setState(() => _loadingSchedule = false);
  }

  bool _isBooked(DateTime slot) {
    for (final b in _bookings) {
      final start = DateTime.parse(b['start_time']).toLocal();
      final end = DateTime.parse(b['end_time']).toLocal();
      if (slot.isAfter(start.subtract(const Duration(minutes: 1))) && slot.isBefore(end)) return true;
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
        _selectedStart = null; _selectedEnd = null;
      } else if (slot.isAfter(_selectedStart!)) {
        _selectedEnd = slot.add(const Duration(hours: 1));
      } else {
        _selectedStart = slot;
        _selectedEnd = slot.add(const Duration(hours: 1));
      }
    });
  }

  Future<void> _submitPayment() async {
    if (!_payKey.currentState!.validate()) return;
    setState(() { _submitting = true; _error = null; });
    try {
      final res = await ApiService.post('/api/bookings/', {
        'resource': widget.resource['id'],
        'start_time': _selectedStart!.toUtc().toIso8601String(),
        'end_time': _selectedEnd!.toUtc().toIso8601String(),
        'custom_data': {
          'full_name': _nameCtrl.text.trim(),
          'phone': _phoneCtrl.text.trim(),
          'email': _emailCtrl.text.trim(),
          'reason': _reasonCtrl.text.trim(),
          'payment_method': 'Card',
          'card_last4': _cardNumCtrl.text.trim().replaceAll(' ', '').length >= 4
              ? _cardNumCtrl.text.trim().replaceAll(' ', '').substring(
                  _cardNumCtrl.text.trim().replaceAll(' ', '').length - 4)
              : '****',
        },
      });
      if (!mounted) return;
      if (res.statusCode == 201) {
        final booking = jsonDecode(res.body);
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => ExternalReceiptScreen(
              booking: booking,
              resource: widget.resource,
              fullName: _nameCtrl.text.trim(),
              phone: _phoneCtrl.text.trim(),
              email: _emailCtrl.text.trim(),
              reason: _reasonCtrl.text.trim(),
            ),
          ),
        );
      } else {
        final err = jsonDecode(res.body);
        final msg = err is Map ? err.values.first : err.toString();
        setState(() => _error = msg is List ? msg.first : msg.toString());
      }
    } catch (e) {
      setState(() => _error = 'Connection error. Check your network.');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_step == 0 ? 'Your Details' : _step == 1 ? 'Select Time' : 'Payment'),
      ),
      body: Column(
        children: [
          // Step indicator
          _StepIndicator(current: _step),
          Expanded(
            child: _step == 0
                ? _DetailsStep(
                    formKey: _detailsKey,
                    nameCtrl: _nameCtrl,
                    phoneCtrl: _phoneCtrl,
                    emailCtrl: _emailCtrl,
                    reasonCtrl: _reasonCtrl,
                  )
                : _step == 1
                    ? _TimeStep(
                        weekStart: _weekStart,
                        loading: _loadingSchedule,
                        bookings: _bookings,
                        isBooked: _isBooked,
                        isSelected: _isSelected,
                        onSlotTap: _onSlotTap,
                        selectedStart: _selectedStart,
                        selectedEnd: _selectedEnd,
                        dateFmt: _dateFmt,
                        timeFmt: _timeFmt,
                        onPrevWeek: () {
                          setState(() {
                            _weekStart = _weekStart.subtract(const Duration(days: 7));
                            _selectedStart = null; _selectedEnd = null;
                          });
                          _loadSchedule();
                        },
                        onNextWeek: () {
                          setState(() {
                            _weekStart = _weekStart.add(const Duration(days: 7));
                            _selectedStart = null; _selectedEnd = null;
                          });
                          _loadSchedule();
                        },
                      )
                    : _PaymentStep(
                        formKey: _payKey,
                        cardNameCtrl: _cardNameCtrl,
                        cardNumCtrl: _cardNumCtrl,
                        expiryCtrl: _expiryCtrl,
                        cvvCtrl: _cvvCtrl,
                        resource: widget.resource,
                        selectedStart: _selectedStart,
                        selectedEnd: _selectedEnd,
                        error: _error,
                      ),
          ),
          // Bottom nav
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              color: AppColors.surface,
              border: Border(top: BorderSide(color: AppColors.border)),
            ),
            child: Row(children: [
              if (_step > 0)
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => setState(() => _step--),
                    child: const Text('Back'),
                  ),
                ),
              if (_step > 0) const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: ElevatedButton(
                  onPressed: _submitting
                      ? null
                      : () {
                          if (_step == 0) {
                            if (_detailsKey.currentState!.validate()) setState(() => _step = 1);
                          } else if (_step == 1) {
                            if (_selectedStart == null) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('Please select a time slot')),
                              );
                            } else {
                              setState(() => _step = 2);
                            }
                          } else {
                            _submitPayment();
                          }
                        },
                  child: _submitting
                      ? const SizedBox(height: 20, width: 20,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : Text(_step == 2 ? 'Pay & Confirm' : 'Next'),
                ),
              ),
            ]),
          ),
        ],
      ),
    );
  }
}

// ─── Step indicator ───────────────────────────────────────────────────────────

class _StepIndicator extends StatelessWidget {
  final int current;
  const _StepIndicator({required this.current});

  @override
  Widget build(BuildContext context) {
    final labels = ['Details', 'Time Slot', 'Payment'];
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 20),
      color: AppColors.surface,
      child: Row(
        children: List.generate(labels.length * 2 - 1, (i) {
          if (i.isOdd) {
            return Expanded(
              child: Container(
                height: 2,
                color: i ~/ 2 < current ? AppColors.primary : AppColors.border,
              ),
            );
          }
          final idx = i ~/ 2;
          final done = idx < current;
          final active = idx == current;
          return Column(mainAxisSize: MainAxisSize.min, children: [
            Container(
              width: 28, height: 28,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: done || active ? AppColors.primary : AppColors.border,
              ),
              child: Center(
                child: done
                    ? const Icon(Icons.check, size: 14, color: Colors.white)
                    : Text('${idx + 1}',
                        style: TextStyle(
                            color: active ? Colors.white : AppColors.textMuted,
                            fontSize: 12, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 4),
            Text(labels[idx],
                style: TextStyle(
                    fontSize: 10,
                    color: active ? AppColors.primary : AppColors.textMuted,
                    fontWeight: active ? FontWeight.w600 : FontWeight.normal)),
          ]);
        }),
      ),
    );
  }
}

// ─── Step 1: Personal details ─────────────────────────────────────────────────

class _DetailsStep extends StatelessWidget {
  final GlobalKey<FormState> formKey;
  final TextEditingController nameCtrl, phoneCtrl, emailCtrl, reasonCtrl;

  const _DetailsStep({
    required this.formKey, required this.nameCtrl, required this.phoneCtrl,
    required this.emailCtrl, required this.reasonCtrl,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Form(
        key: formKey,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text('Your Details', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 4),
          const Text('We need these to confirm your booking.',
              style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
          const SizedBox(height: 20),
          TextFormField(
            controller: nameCtrl,
            decoration: const InputDecoration(
              labelText: 'Full Name',
              prefixIcon: Icon(Icons.person_outline, color: AppColors.textMuted),
            ),
            validator: (v) => v!.trim().isEmpty ? 'Required' : null,
          ),
          const SizedBox(height: 14),
          TextFormField(
            controller: phoneCtrl,
            keyboardType: TextInputType.phone,
            decoration: const InputDecoration(
              labelText: 'Phone Number',
              prefixIcon: Icon(Icons.phone_outlined, color: AppColors.textMuted),
            ),
            validator: (v) => v!.trim().isEmpty ? 'Required' : null,
          ),
          const SizedBox(height: 14),
          TextFormField(
            controller: emailCtrl,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(
              labelText: 'Email Address',
              prefixIcon: Icon(Icons.email_outlined, color: AppColors.textMuted),
            ),
            validator: (v) => v!.trim().isEmpty || !v.contains('@') ? 'Valid email required' : null,
          ),
          const SizedBox(height: 14),
          TextFormField(
            controller: reasonCtrl,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Reason for booking',
              hintText: 'e.g. Annual conference, product launch, team meeting...',
              alignLabelWithHint: true,
              prefixIcon: Padding(
                padding: EdgeInsets.only(bottom: 44),
                child: Icon(Icons.notes_outlined, color: AppColors.textMuted),
              ),
            ),
            validator: (v) => v!.trim().isEmpty ? 'Required' : null,
          ),
        ]),
      ),
    );
  }
}

// ─── Step 2: Time slot (reuses timetable) ─────────────────────────────────────

class _TimeStep extends StatelessWidget {
  final DateTime weekStart;
  final bool loading;
  final List<dynamic> bookings;
  final bool Function(DateTime) isBooked;
  final bool Function(DateTime) isSelected;
  final void Function(DateTime) onSlotTap;
  final DateTime? selectedStart;
  final DateTime? selectedEnd;
  final DateFormat dateFmt, timeFmt;
  final VoidCallback onPrevWeek, onNextWeek;

  const _TimeStep({
    required this.weekStart, required this.loading, required this.bookings,
    required this.isBooked, required this.isSelected, required this.onSlotTap,
    required this.selectedStart, required this.selectedEnd,
    required this.dateFmt, required this.timeFmt,
    required this.onPrevWeek, required this.onNextWeek,
  });

  @override
  Widget build(BuildContext context) {
    final weekEnd = weekStart.add(const Duration(days: 6));
    return Column(children: [
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Row(children: [
          IconButton(onPressed: onPrevWeek,
              icon: const Icon(Icons.chevron_left, color: AppColors.primary), padding: EdgeInsets.zero),
          Expanded(
            child: Text('${dateFmt.format(weekStart)} – ${dateFmt.format(weekEnd)}',
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600)),
          ),
          IconButton(onPressed: onNextWeek,
              icon: const Icon(Icons.chevron_right, color: AppColors.primary), padding: EdgeInsets.zero),
        ]),
      ),
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(children: [
          _Dot(color: AppColors.surface, label: 'Available'),
          const SizedBox(width: 16),
          _Dot(color: AppColors.error.withValues(alpha: 0.7), label: 'Booked'),
          const SizedBox(width: 16),
          _Dot(color: AppColors.primary, label: 'Selected'),
        ]),
      ),
      const SizedBox(height: 6),
      Expanded(
        child: loading
            ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
            : _TimetableGrid(
                weekStart: weekStart, dayStart: 7, dayEnd: 20,
                isBooked: isBooked, isSelected: isSelected, onSlotTap: onSlotTap),
      ),
      if (selectedStart != null)
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          color: AppColors.primary.withValues(alpha: 0.1),
          child: Row(children: [
            const Icon(Icons.schedule, color: AppColors.primary, size: 16),
            const SizedBox(width: 8),
            Text(
              '${DateFormat('EEE d MMM, HH:mm').format(selectedStart!)} → ${timeFmt.format(selectedEnd!)}',
              style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.w600, fontSize: 13),
            ),
          ]),
        ),
    ]);
  }
}

class _Dot extends StatelessWidget {
  final Color color; final String label;
  const _Dot({required this.color, required this.label});
  @override
  Widget build(BuildContext context) => Row(children: [
    Container(width: 12, height: 12,
        decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(3),
            border: Border.all(color: AppColors.border))),
    const SizedBox(width: 4),
    Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
  ]);
}

class _TimetableGrid extends StatelessWidget {
  final DateTime weekStart;
  final int dayStart, dayEnd;
  final bool Function(DateTime) isBooked, isSelected;
  final void Function(DateTime) onSlotTap;

  const _TimetableGrid({
    required this.weekStart, required this.dayStart, required this.dayEnd,
    required this.isBooked, required this.isSelected, required this.onSlotTap,
  });

  @override
  Widget build(BuildContext context) {
    final days = List.generate(7, (i) => weekStart.add(Duration(days: i)));
    final hours = List.generate(dayEnd - dayStart, (i) => dayStart + i);
    const timeColW = 44.0, slotH = 44.0, dayColW = 52.0;

    return SingleChildScrollView(
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            SizedBox(width: timeColW),
            ...days.map((d) {
              final today = DateTime.now();
              final isToday = d.year == today.year && d.month == today.month && d.day == today.day;
              return Container(
                width: dayColW,
                padding: const EdgeInsets.symmetric(vertical: 6),
                alignment: Alignment.center,
                decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.border))),
                child: Column(children: [
                  Text(DateFormat('EEE').format(d),
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
                          color: isToday ? AppColors.primary : AppColors.textMuted)),
                  Text(DateFormat('d').format(d),
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold,
                          color: isToday ? AppColors.primary : AppColors.textPrimary)),
                ]),
              );
            }),
          ]),
          ...hours.map((hour) => Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            SizedBox(width: timeColW, height: slotH,
              child: Padding(padding: const EdgeInsets.only(right: 6, top: 4),
                child: Text('${hour.toString().padLeft(2, '0')}:00',
                    textAlign: TextAlign.right,
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 11)))),
            ...days.map((day) {
              final slot = DateTime(day.year, day.month, day.day, hour);
              final booked = isBooked(slot);
              final selected = isSelected(slot);
              final isPast = slot.isBefore(DateTime.now());
              Color bg = selected ? AppColors.primary
                  : booked ? AppColors.error.withValues(alpha: 0.65)
                  : isPast ? AppColors.border.withValues(alpha: 0.4)
                  : AppColors.surface;
              return GestureDetector(
                onTap: (booked || isPast) ? null : () => onSlotTap(slot),
                child: Container(
                  width: dayColW, height: slotH,
                  decoration: BoxDecoration(color: bg,
                      border: Border.all(color: AppColors.border.withValues(alpha: 0.4), width: 0.5)),
                  child: booked ? const Center(child: Icon(Icons.block, size: 14, color: Colors.white54))
                      : selected ? const Center(child: Icon(Icons.check, size: 14, color: Colors.white))
                      : null,
                ),
              );
            }),
          ])),
        ]),
      ),
    );
  }
}

// ─── Step 3: Payment ──────────────────────────────────────────────────────────

class _PaymentStep extends StatelessWidget {
  final GlobalKey<FormState> formKey;
  final TextEditingController cardNameCtrl, cardNumCtrl, expiryCtrl, cvvCtrl;
  final Map<String, dynamic> resource;
  final DateTime? selectedStart, selectedEnd;
  final String? error;

  const _PaymentStep({
    required this.formKey, required this.cardNameCtrl, required this.cardNumCtrl,
    required this.expiryCtrl, required this.cvvCtrl, required this.resource,
    required this.selectedStart, required this.selectedEnd, required this.error,
  });

  @override
  Widget build(BuildContext context) {
    final price = double.tryParse(resource['price']?.toString() ?? '0') ?? 0;
    final fmt = DateFormat('EEE d MMM, HH:mm');

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Form(
        key: formKey,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          // Order summary
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.primary.withValues(alpha: 0.3)),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('ORDER SUMMARY',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 11, letterSpacing: 1.2)),
              const SizedBox(height: 10),
              _SummaryRow(label: 'Resource', value: resource['name'] ?? ''),
              _SummaryRow(label: 'Organisation', value: resource['organisation_name'] ?? ''),
              if (selectedStart != null) _SummaryRow(label: 'From', value: fmt.format(selectedStart!)),
              if (selectedEnd != null) _SummaryRow(label: 'To', value: DateFormat('HH:mm').format(selectedEnd!)),
              const Divider(height: 16),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                const Text('Total', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold)),
                Text(
                  price == 0 ? 'Free' : 'MWK ${price.toStringAsFixed(2)}',
                  style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold, fontSize: 16),
                ),
              ]),
            ]),
          ),
          const SizedBox(height: 24),
          Text('Card Details', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 4),
          const Text('Your payment is secured and encrypted.',
              style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
          const SizedBox(height: 16),
          if (error != null)
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 14),
              decoration: BoxDecoration(
                color: AppColors.error.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.error.withValues(alpha: 0.4)),
              ),
              child: Text(error!, style: const TextStyle(color: AppColors.error, fontSize: 13)),
            ),
          TextFormField(
            controller: cardNameCtrl,
            decoration: const InputDecoration(
              labelText: 'Name on Card',
              prefixIcon: Icon(Icons.person_outline, color: AppColors.textMuted),
            ),
            validator: (v) => v!.trim().isEmpty ? 'Required' : null,
          ),
          const SizedBox(height: 14),
          TextFormField(
            controller: cardNumCtrl,
            keyboardType: TextInputType.number,
            maxLength: 19,
            decoration: const InputDecoration(
              labelText: 'Card Number',
              hintText: '1234 5678 9012 3456',
              prefixIcon: Icon(Icons.credit_card_outlined, color: AppColors.textMuted),
              counterText: '',
            ),
            validator: (v) {
              final digits = v!.replaceAll(' ', '');
              return digits.length < 16 ? 'Enter a valid 16-digit card number' : null;
            },
          ),
          const SizedBox(height: 14),
          Row(children: [
            Expanded(
              child: TextFormField(
                controller: expiryCtrl,
                keyboardType: TextInputType.number,
                maxLength: 5,
                decoration: const InputDecoration(
                  labelText: 'Expiry (MM/YY)',
                  hintText: '12/27',
                  prefixIcon: Icon(Icons.calendar_today_outlined, color: AppColors.textMuted),
                  counterText: '',
                ),
                validator: (v) => v!.trim().length < 5 ? 'Invalid' : null,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: TextFormField(
                controller: cvvCtrl,
                keyboardType: TextInputType.number,
                maxLength: 3,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'CVV',
                  hintText: '123',
                  prefixIcon: Icon(Icons.lock_outline, color: AppColors.textMuted),
                  counterText: '',
                ),
                validator: (v) => v!.trim().length < 3 ? 'Invalid' : null,
              ),
            ),
          ]),
          const SizedBox(height: 16),
          Row(children: const [
            Icon(Icons.lock_outline, color: AppColors.textMuted, size: 14),
            SizedBox(width: 6),
            Text('Payments processed securely via PayChangu',
                style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
          ]),
        ]),
      ),
    );
  }
}

class _SummaryRow extends StatelessWidget {
  final String label, value;
  const _SummaryRow({required this.label, required this.value});
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 3),
    child: Row(children: [
      SizedBox(width: 100, child: Text(label,
          style: const TextStyle(color: AppColors.textMuted, fontSize: 13))),
      Expanded(child: Text(value,
          style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontWeight: FontWeight.w500))),
    ]),
  );
}

// ─── Receipt screen with PDF download ────────────────────────────────────────

class ExternalReceiptScreen extends StatelessWidget {
  final Map<String, dynamic> booking;
  final Map<String, dynamic> resource;
  final String fullName, phone, email, reason;

  const ExternalReceiptScreen({
    super.key, required this.booking, required this.resource,
    required this.fullName, required this.phone,
    required this.email, required this.reason,
  });

  Future<void> _downloadPdf(BuildContext context) async {
    final fmt = DateFormat('EEE d MMM yyyy, HH:mm');
    final start = DateTime.tryParse(booking['start_time'] ?? '')?.toLocal();
    final end = DateTime.tryParse(booking['end_time'] ?? '')?.toLocal();
    final price = double.tryParse(resource['price']?.toString() ?? '0') ?? 0;

    final pdf = pw.Document();
    pdf.addPage(pw.Page(
      pageFormat: PdfPageFormat.a4,
      build: (pw.Context ctx) => pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          // Header
          pw.Container(
            width: double.infinity,
            padding: const pw.EdgeInsets.all(20),
            decoration: pw.BoxDecoration(
              color: PdfColor.fromHex('14B8A6'),
              borderRadius: pw.BorderRadius.circular(8),
            ),
            child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
              pw.Text('SmartSlot', style: pw.TextStyle(fontSize: 28, fontWeight: pw.FontWeight.bold, color: PdfColors.white)),
              pw.Text('Booking Receipt', style: const pw.TextStyle(fontSize: 14, color: PdfColors.white)),
            ]),
          ),
          pw.SizedBox(height: 24),
          pw.Text('BOOKING DETAILS', style: pw.TextStyle(fontSize: 11, fontWeight: pw.FontWeight.bold, color: PdfColor.fromHex('94A3B8'), letterSpacing: 1.2)),
          pw.Divider(),
          _pdfRow('Booking ID', '#${booking['id']}'),
          _pdfRow('Resource', resource['name'] ?? ''),
          _pdfRow('Category', resource['category'] ?? ''),
          _pdfRow('Organisation', resource['organisation_name'] ?? ''),
          if (start != null) _pdfRow('From', fmt.format(start)),
          if (end != null) _pdfRow('To', DateFormat('HH:mm').format(end)),
          _pdfRow('Amount Paid', price == 0 ? 'Free' : 'MWK ${price.toStringAsFixed(2)}'),
          _pdfRow('Status', booking['status'] ?? 'Pending'),
          pw.SizedBox(height: 20),
          pw.Text('GUEST DETAILS', style: pw.TextStyle(fontSize: 11, fontWeight: pw.FontWeight.bold, color: PdfColor.fromHex('94A3B8'), letterSpacing: 1.2)),
          pw.Divider(),
          _pdfRow('Full Name', fullName),
          _pdfRow('Phone', phone),
          _pdfRow('Email', email),
          _pdfRow('Reason', reason),
          pw.SizedBox(height: 20),
          pw.Text('QR TOKEN', style: pw.TextStyle(fontSize: 11, fontWeight: pw.FontWeight.bold, color: PdfColor.fromHex('94A3B8'), letterSpacing: 1.2)),
          pw.Divider(),
          pw.Text(booking['qr_token'] ?? '', style: const pw.TextStyle(fontSize: 10)),
          pw.SizedBox(height: 30),
          pw.Center(
            child: pw.Text('Thank you for booking with SmartSlot',
                style: pw.TextStyle(color: PdfColor.fromHex('14B8A6'), fontWeight: pw.FontWeight.bold)),
          ),
        ],
      ),
    ));

    await Printing.layoutPdf(onLayout: (_) async => pdf.save());
  }

  pw.Widget _pdfRow(String label, String value) => pw.Padding(
    padding: const pw.EdgeInsets.symmetric(vertical: 4),
    child: pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
      pw.SizedBox(width: 120, child: pw.Text(label, style: pw.TextStyle(color: PdfColor.fromHex('64748B'), fontSize: 11))),
      pw.Expanded(child: pw.Text(value, style: pw.TextStyle(fontWeight: pw.FontWeight.bold, fontSize: 11))),
    ]),
  );

  @override
  Widget build(BuildContext context) {
    final fmt = DateFormat('EEE d MMM yyyy, HH:mm');
    final start = DateTime.tryParse(booking['start_time'] ?? '')?.toLocal();
    final end = DateTime.tryParse(booking['end_time'] ?? '')?.toLocal();
    final price = double.tryParse(resource['price']?.toString() ?? '0') ?? 0;
    final qrToken = booking['qr_token'] ?? booking['id'].toString();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Booking Confirmed'),
        automaticallyImplyLeading: false,
        actions: [
          TextButton(
            onPressed: () => Navigator.popUntil(context, (r) => r.isFirst),
            child: const Text('Done', style: TextStyle(color: AppColors.primary)),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(children: [
          // Success
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.success.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.success.withValues(alpha: 0.4)),
            ),
            child: const Column(children: [
              Icon(Icons.check_circle_outline, color: AppColors.success, size: 40),
              SizedBox(height: 8),
              Text('Payment Successful!',
                  style: TextStyle(color: AppColors.success, fontSize: 18, fontWeight: FontWeight.bold)),
              SizedBox(height: 4),
              Text('Your booking is confirmed. Show the QR code at the entrance.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
            ]),
          ),
          const SizedBox(height: 24),

          // QR
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
            child: QrImageView(
              data: qrToken,
              version: QrVersions.auto,
              size: 200,
              backgroundColor: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          Text('Booking #${booking['id']}',
              style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
          const SizedBox(height: 24),

          // Receipt
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(12),
              border: const Border.fromBorderSide(BorderSide(color: AppColors.border)),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('RECEIPT', style: TextStyle(color: AppColors.textMuted, fontSize: 11, letterSpacing: 1.2, fontWeight: FontWeight.w600)),
              const Divider(height: 20),
              _Row(label: 'Resource', value: resource['name'] ?? ''),
              _Row(label: 'Organisation', value: resource['organisation_name'] ?? ''),
              _Row(label: 'Guest', value: fullName),
              _Row(label: 'Phone', value: phone),
              _Row(label: 'Email', value: email),
              _Row(label: 'Reason', value: reason),
              const Divider(height: 20),
              if (start != null) _Row(label: 'From', value: fmt.format(start)),
              if (end != null) _Row(label: 'To', value: DateFormat('HH:mm').format(end)),
              const Divider(height: 20),
              _Row(label: 'Amount Paid',
                  value: price == 0 ? 'Free' : 'MWK ${price.toStringAsFixed(2)}',
                  valueColor: AppColors.primary),
              _Row(label: 'Status', value: booking['status'] ?? 'Pending', valueColor: AppColors.warning),
            ]),
          ),
          const SizedBox(height: 20),

          // Download PDF
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              icon: const Icon(Icons.download_outlined),
              label: const Text('Download PDF Receipt'),
              onPressed: () => _downloadPdf(context),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              icon: const Icon(Icons.home_outlined),
              label: const Text('Back to Home'),
              onPressed: () => Navigator.popUntil(context, (r) => r.isFirst),
            ),
          ),
        ]),
      ),
    );
  }
}

class _Row extends StatelessWidget {
  final String label, value;
  final Color? valueColor;
  const _Row({required this.label, required this.value, this.valueColor});
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SizedBox(width: 110, child: Text(label,
          style: const TextStyle(color: AppColors.textMuted, fontSize: 13))),
      Expanded(child: Text(value,
          style: TextStyle(color: valueColor ?? AppColors.textPrimary,
              fontSize: 13, fontWeight: FontWeight.w500))),
    ]),
  );
}
