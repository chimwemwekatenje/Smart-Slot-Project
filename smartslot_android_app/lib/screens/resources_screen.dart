import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/resource_card.dart';
import 'resource_detail_screen.dart';

class ResourcesScreen extends StatefulWidget {
  const ResourcesScreen({super.key});

  @override
  State<ResourcesScreen> createState() => _ResourcesScreenState();
}

class _ResourcesScreenState extends State<ResourcesScreen> {
  List<dynamic> _resources = [];
  List<dynamic> _filtered = [];
  List<String> _categories = ['All'];
  bool _loading = true;
  String? _error;
  String _search = '';
  String _category = 'All';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await ApiService.get('/api/resources/');
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as List;
        final cats = <String>{'All'};
        for (final r in data) {
          if (r['category'] != null) cats.add(r['category']);
        }
        setState(() {
          _resources = data;
          _categories = cats.toList();
          _applyFilter();
        });
      } else {
        setState(() => _error = 'Failed to load resources');
      }
    } catch (e) {
      setState(() => _error = 'Connection error. Is the server running?');
    } finally {
      setState(() => _loading = false);
    }
  }

  void _applyFilter() {
    _filtered = _resources.where((r) {
      final matchSearch = _search.isEmpty ||
          r['name'].toString().toLowerCase().contains(_search.toLowerCase()) ||
          (r['description'] ?? '').toString().toLowerCase().contains(_search.toLowerCase());
      final matchCat = _category == 'All' || r['category'] == _category;
      return matchSearch && matchCat;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final isExternal = auth.isExternal;

    return Scaffold(
      appBar: AppBar(
        title: Text(isExternal ? 'Explore Resources' : 'Our Resources'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: AppColors.textMuted),
            onPressed: _load,
          ),
        ],
      ),
      body: Column(
        children: [
          // Context banner for external users
          if (isExternal)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                    color: AppColors.primary.withValues(alpha: 0.3)),
              ),
              child: const Row(children: [
                Icon(Icons.info_outline, color: AppColors.primary, size: 16),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Browse resources from all organisations. Tap a resource to view details and contact the organisation.',
                    style: TextStyle(color: AppColors.primary, fontSize: 12),
                  ),
                ),
              ]),
            ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              onChanged: (v) => setState(() {
                _search = v;
                _applyFilter();
              }),
              decoration: const InputDecoration(
                hintText: 'Search resources...',
                prefixIcon: Icon(Icons.search, color: AppColors.textMuted),
              ),
            ),
          ),
          SizedBox(
            height: 44,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _categories.length,
              itemBuilder: (ctx, i) {
                final cat = _categories[i];
                final selected = cat == _category;
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: FilterChip(
                    label: Text(cat),
                    selected: selected,
                    onSelected: (_) => setState(() {
                      _category = cat;
                      _applyFilter();
                    }),
                    selectedColor: AppColors.primary.withValues(alpha: 0.2),
                    checkmarkColor: AppColors.primary,
                    side: BorderSide(
                      color: selected ? AppColors.primary : AppColors.border,
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: _loading
                ? const Center(
                    child: CircularProgressIndicator(color: AppColors.primary))
                : _error != null
                    ? _ErrorState(message: _error!, onRetry: _load)
                    : _filtered.isEmpty
                        ? Center(
                            child: Text('No resources found',
                                style: Theme.of(context).textTheme.bodyMedium))
                        : RefreshIndicator(
                            onRefresh: _load,
                            color: AppColors.primary,
                            child: ListView.builder(
                              padding: const EdgeInsets.all(16),
                              itemCount: _filtered.length,
                              itemBuilder: (ctx, i) => ResourceCard(
                                resource: _filtered[i],
                                isExternal: isExternal,
                                isEmployee: !isExternal,
                                onTap: () => Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => ResourceDetailScreen(
                                      resource: _filtered[i],
                                      isExternal: isExternal,
                                      isEmployee: !isExternal,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
          ),
        ],
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorState({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.wifi_off, color: AppColors.textMuted, size: 48),
            const SizedBox(height: 16),
            Text(message,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 16),
            OutlinedButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
