import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'timeline_provider.dart';
import '../../core/network/api_service.dart';
import '../../shared/models/timeline_models.dart';
import '../../core/theme/app_theme.dart';

class TimelineScreen extends ConsumerWidget {
  const TimelineScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedDate = ref.watch(selectedDateProvider);
    final timelineEventsAsync = ref.watch(timelineEventsProvider);
    
    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(timelineEventsProvider.future),
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            // Calendar Strip Header
            SliverToBoxAdapter(
              child: Column(
                children: [
                  const SizedBox(height: 16),
                  _buildCalendarStrip(context, ref, selectedDate),
                  const Divider(color: AppTheme.surfaceDarkBorder, height: 24),
                ],
              ),
            ),
            
            // Timeline Content
            timelineEventsAsync.when(
              data: (events) {
                if (events.isEmpty) {
                  return const SliverFillRemaining(
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.spa_outlined, size: 64, color: AppTheme.colorPaused),
                          SizedBox(height: 16),
                          Text("No medicines scheduled for this day.", style: TextStyle(fontSize: 16)),
                        ],
                      ),
                    ),
                  );
                }
                return SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
                      final event = events[index];
                      return _EventClusterCard(event: event);
                    },
                    childCount: events.length,
                  ),
                );
              },
              loading: () => const SliverFillRemaining(
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (err, stack) => SliverFillRemaining(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, size: 48, color: AppTheme.colorSkipped),
                        const SizedBox(height: 16),
                        Text(
                          err.toString(),
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 15, color: Colors.white70),
                        ),
                        const SizedBox(height: 24),
                        ElevatedButton(
                          onPressed: () => ref.refresh(timelineEventsProvider),
                          child: const Text("RETRY"),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCalendarStrip(BuildContext context, WidgetRef ref, DateTime selectedDate) {
    // Generate dates: 4 days in past, today, and 10 days in future
    final today = DateTime.now();
    final dates = List.generate(15, (index) => today.subtract(const Duration(days: 4)).add(Duration(days: index)));
    
    return SizedBox(
      height: 90,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: dates.length,
        itemBuilder: (context, index) {
          final date = dates[index];
          final isSelected = DateFormat('yyyy-MM-dd').format(date) == DateFormat('yyyy-MM-dd').format(selectedDate);
          final isToday = DateFormat('yyyy-MM-dd').format(date) == DateFormat('yyyy-MM-dd').format(today);
          
          return GestureDetector(
            onTap: () {
              ref.read(selectedDateProvider.notifier).state = date;
            },
            child: Container(
              width: 58,
              margin: const EdgeInsets.only(right: 10),
              decoration: BoxDecoration(
                color: isSelected ? AppTheme.primaryTeal : AppTheme.surfaceDark,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: isSelected
                      ? Colors.transparent
                      : (isToday ? AppTheme.primaryTealLight : AppTheme.surfaceDarkBorder),
                  width: 1.5,
                ),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    DateFormat('E').format(date)[0],
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: isSelected ? Colors.white : const Color(0xFF94A3B8),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    DateFormat('d').format(date),
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: isSelected ? Colors.white : Colors.white,
                    ),
                  ),
                  if (isToday)
                    Container(
                      margin: const EdgeInsets.only(top: 4),
                      width: 5,
                      height: 5,
                      decoration: BoxDecoration(
                        color: isSelected ? Colors.white : AppTheme.primaryTealLight,
                        shape: BoxShape.circle,
                      ),
                    )
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

class _EventClusterCard extends ConsumerStatefulWidget {
  final ClusteredEvent event;

  const _EventClusterCard({required this.event});

  @override
  ConsumerState<_EventClusterCard> createState() => _EventClusterCardState();
}

class _EventClusterCardState extends ConsumerState<_EventClusterCard> {
  bool _isExpanded = true;

  @override
  Widget build(BuildContext context) {
    final eventTime = DateFormat('hh:mm a').format(widget.event.scheduledAt.toLocal());
    final count = widget.event.doses.length;
    
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        children: [
          ListTile(
            onTap: () => setState(() => _isExpanded = !_isExpanded),
            leading: const Icon(Icons.access_time_outlined, color: AppTheme.primaryTealLight),
            title: Text(
              eventTime,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
            subtitle: Text(
              "$count medicine${count > 1 ? 's' : ''} scheduled",
              style: const TextStyle(color: Colors.white70),
            ),
            trailing: Icon(
              _isExpanded ? Icons.expand_less : Icons.expand_more,
              color: Colors.white54,
            ),
          ),
          if (_isExpanded)
            Padding(
              padding: const EdgeInsets.only(left: 16, right: 16, bottom: 16),
              child: Column(
                children: widget.event.doses.map((dose) => _DoseTile(dose: dose)).toList(),
              ),
            )
        ],
      ),
    );
  }
}

class _DoseTile extends ConsumerWidget {
  final DoseDetails dose;

  const _DoseTile({required this.dose});

  Color _getStatusColor() {
    switch (dose.status) {
      case 'TAKEN':
        return AppTheme.colorTaken;
      case 'SKIPPED':
        return AppTheme.colorSkipped;
      case 'NOT_REQUIRED':
        return AppTheme.colorNotRequired;
      default:
        return AppTheme.colorPending;
    }
  }

  IconData _getStatusIcon() {
    switch (dose.status) {
      case 'TAKEN':
        return Icons.check_circle_outline;
      case 'SKIPPED':
        return Icons.remove_circle_outline;
      case 'NOT_REQUIRED':
        return Icons.info_outline;
      default:
        return Icons.help_outline;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final statusColor = _getStatusColor();
    final statusIcon = _getStatusIcon();
    
    return Container(
      margin: const EdgeInsets.only(top: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.backgroundDark,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.surfaceDarkBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      dose.medicineName,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      "${dose.dosageAmount} ${dose.dosageUnitName} • ${dose.medicineTypeName ?? 'General'}",
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              
              // Status Badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: statusColor.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: statusColor.withOpacity(0.5)),
                ),
                child: Row(
                  children: [
                    Icon(statusIcon, size: 14, color: statusColor),
                    const SizedBox(width: 4),
                    Text(
                      dose.status,
                      style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
            ],
          ),
          
          if (dose.statusRemark != null) ...[
            const SizedBox(height: 8),
            Text(
              "Remark: ${dose.statusRemark}",
              style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: Colors.white70),
            ),
          ],
          
          const SizedBox(height: 12),
          
          // Action Buttons
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              if (dose.status == 'PENDING') ...[
                IconButton(
                  icon: const Icon(Icons.remove_circle_outline_outlined, color: AppTheme.colorSkipped),
                  tooltip: "Skip Dose",
                  onPressed: () => _showSkipDialog(context, ref),
                ),
                const SizedBox(width: 8),
                ElevatedButton.icon(
                  onPressed: () => _takeDose(context, ref),
                  icon: const Icon(Icons.check, size: 18),
                  label: const Text("TAKE"),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.colorTaken,
                    minimumSize: const Size(100, 36),
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                  ),
                ),
              ] else if (dose.status == 'TAKEN' || dose.status == 'SKIPPED') ...[
                TextButton.icon(
                  onPressed: () => _showCorrectionDialog(context, ref),
                  icon: const Icon(Icons.edit_outlined, size: 16),
                  label: const Text("CORRECT ACTION"),
                  style: TextButton.styleFrom(foregroundColor: AppTheme.primaryTealLight),
                ),
              ] else if (dose.status == 'NOT_REQUIRED') ...[
                const Text(
                  "Not active at this time (Paused)",
                  style: TextStyle(fontSize: 12, color: Colors.white38),
                )
              ]
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _takeDose(BuildContext context, WidgetRef ref) async {
    final api = ref.read(apiServiceProvider);
    try {
      await api.takeDose(dose.id);
      ref.refresh(timelineEventsProvider);
    } catch (e) {
      _showError(context, e.toString());
    }
  }

  void _showSkipDialog(BuildContext context, WidgetRef ref) {
    final remarkController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Skip Dose"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text("Are you sure you want to skip this dose?"),
            const SizedBox(height: 16),
            TextField(
              controller: remarkController,
              decoration: const InputDecoration(
                labelText: "Remark (Optional)",
                hintText: "e.g., Doctor advised, Forgot, etc.",
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("CANCEL"),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              final api = ref.read(apiServiceProvider);
              try {
                await api.skipDose(dose.id, remark: remarkController.text.trim());
                ref.refresh(timelineEventsProvider);
              } catch (e) {
                _showError(context, e.toString());
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.colorSkipped),
            child: const Text("SKIP DOSE"),
          ),
        ],
      ),
    );
  }

  void _showCorrectionDialog(BuildContext context, WidgetRef ref) {
    final remarkController = TextEditingController();
    String selectedStatus = dose.status == 'TAKEN' ? 'SKIPPED' : 'TAKEN';
    
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text("Correct Action"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                "Change status from ${dose.status} to:",
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selectedStatus,
                decoration: const InputDecoration(labelText: "Correct Status"),
                items: const [
                  DropdownMenuItem(value: 'TAKEN', child: Text("TAKEN")),
                  DropdownMenuItem(value: 'SKIPPED', child: Text("SKIPPED")),
                  DropdownMenuItem(value: 'PENDING', child: Text("PENDING")),
                ],
                onChanged: (val) {
                  if (val != null) setDialogState(() => selectedStatus = val);
                },
              ),
              const SizedBox(height: 16),
              TextField(
                controller: remarkController,
                decoration: const InputDecoration(
                  labelText: "Correction Reason (Optional)",
                  hintText: "e.g., Marked by mistake",
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("CANCEL"),
            ),
            ElevatedButton(
              onPressed: () async {
                Navigator.pop(context);
                final api = ref.read(apiServiceProvider);
                try {
                  await api.correctDose(dose.id, selectedStatus, remark: remarkController.text.trim());
                  ref.refresh(timelineEventsProvider);
                } catch (e) {
                  _showError(context, e.toString());
                }
              },
              child: const Text("CORRECT"),
            ),
          ],
        ),
      ),
    );
  }

  void _showError(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppTheme.colorSkipped,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}
