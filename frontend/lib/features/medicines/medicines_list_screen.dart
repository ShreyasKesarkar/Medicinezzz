import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'medicines_provider.dart';
import '../../shared/models/medicine_models.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/widgets/loading_indicator.dart';
import 'package:intl/intl.dart';

class MedicinesListScreen extends ConsumerStatefulWidget {
  const MedicinesListScreen({super.key});

  @override
  ConsumerState<MedicinesListScreen> createState() => _MedicinesListScreenState();
}

class _MedicinesListScreenState extends ConsumerState<MedicinesListScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _tabController.addListener(() {
      if (_tabController.indexIsChanging) return;
      _updateStatusFilter();
    });
    // Set initial filter
    Future.microtask(() => ref.read(medicinesStatusFilterProvider.notifier).state = "ACTIVE");
  }

  void _updateStatusFilter() {
    String? status;
    switch (_tabController.index) {
      case 0:
        status = "ACTIVE";
        break;
      case 1:
        status = "PAUSED";
        break;
      case 2:
        status = "FINISHED";
        break;
    }
    ref.read(medicinesStatusFilterProvider.notifier).state = status;
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final medicinesAsync = ref.watch(medicinesListProvider);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text("Medications"),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.primaryTeal,
          labelColor: AppTheme.primaryTealLight,
          unselectedLabelColor: Colors.white60,
          tabs: const [
            Tab(text: "Active"),
            Tab(text: "Paused"),
            Tab(text: "Finished"),
          ],
        ),
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(medicinesListProvider.future),
        child: medicinesAsync.when(
          data: (list) {
            if (list.isEmpty) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.medication_liquid_outlined, size: 64, color: AppTheme.colorPaused),
                    const SizedBox(height: 16),
                    Text(
                      "No ${_tabController.index == 0 ? 'active' : _tabController.index == 1 ? 'paused' : 'finished'} medicines found.",
                      style: const TextStyle(fontSize: 16),
                    ),
                  ],
                ),
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: list.length,
              itemBuilder: (context, index) {
                final med = list[index];
                return _MedicineCard(medicine: med);
              },
            );
          },
          loading: () => const ServerLoadingIndicator(message: "Loading medications..."),
          error: (err, stack) => Center(
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: AppTheme.colorSkipped),
                  const SizedBox(height: 16),
                  Text(err.toString(), textAlign: TextAlign.center),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => ref.refresh(medicinesListProvider),
                    child: const Text("RETRY"),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.pushNamed(context, '/create-medicine').then((_) {
          ref.refresh(medicinesListProvider);
        }),
        backgroundColor: AppTheme.primaryTeal,
        foregroundColor: Colors.white,
        child: const Icon(Icons.add),
      ),
    );
  }
}

class _MedicineCard extends StatelessWidget {
  final Medicine medicine;

  const _MedicineCard({required this.medicine});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    // Check if ending soon (planned_end_date is close, e.g. within 3 days)
    bool isEndingSoon = false;
    // Since planned_end_date is not present directly in the simple Medicine model,
    // wait: does the getMedicines API return it?
    // Let's check backend/app/repositories/medicine_repository.py:
    // "SELECT m.*, t.name as medicine_type_name FROM medicines m..."
    // Yes! It returns finished_at, stopped_at, etc., but planned_end_date is on schedule_versions.
    // Wait, the detail view will show schedule details, but for the list view,
    // we can display basic info. If we want "ending soon" warnings in the list,
    // we can fetch details or return planned_end_date in the backend medicines list query,
    // but wait! We can also check if the status is PAUSED/FINISHED and show badge.
    
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () {
          Navigator.pushNamed(
            context, 
            '/medicine-details',
            arguments: medicine.id,
          );
        },
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppTheme.primaryTeal.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.medication_outlined, color: AppTheme.primaryTealLight),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      medicine.name,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      medicine.medicineTypeName ?? "General Medicine",
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Colors.white30),
            ],
          ),
        ),
      ),
    );
  }
}
