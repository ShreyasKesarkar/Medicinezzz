import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'medicines_provider.dart';
import '../../core/network/api_service.dart';
import '../../core/theme/app_theme.dart';
import 'package:intl/intl.dart';

class MedicineDetailsScreen extends ConsumerWidget {
  final String medicineId;

  const MedicineDetailsScreen({super.key, required this.medicineId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detailsAsync = ref.watch(medicineDetailsProvider(medicineId));
    final theme = Theme.of(context);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text("Medication Details"),
      ),
      body: detailsAsync.when(
        data: (details) {
          final med = details;
          final String status = med["status"] ?? "ACTIVE";
          final schedules = med["schedules"] as List? ?? [];
          final instructions = med["instructions"] as List? ?? [];
          final notes = med["notes"] as List? ?? [];
          
          // Check ending soon
          bool isEndingSoon = false;
          String? plannedEndDateStr;
          if (schedules.isNotEmpty) {
            final activeSched = schedules.first;
            plannedEndDateStr = activeSched["planned_end_date"];
            if (plannedEndDateStr != null && status == "ACTIVE") {
              final end = DateTime.parse(plannedEndDateStr);
              final diff = end.difference(DateTime.now()).inDays;
              if (diff >= 0 && diff <= 2) {
                isEndingSoon = true;
              }
            }
          }

          return RefreshIndicator(
            onRefresh: () => ref.refresh(medicineDetailsProvider(medicineId).future),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              physics: const AlwaysScrollableScrollPhysics(),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Main Info Card
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        children: [
                          const Icon(Icons.medication, size: 64, color: AppTheme.primaryTealLight),
                          const SizedBox(height: 16),
                          Text(
                            med["name"] ?? "",
                            style: theme.textTheme.titleLarge,
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            med["medicine_type_name"] ?? "General Medicine",
                            style: theme.textTheme.bodyMedium,
                          ),
                          const SizedBox(height: 16),
                          _buildStatusBadge(status),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  // Ending soon Warning
                  if (isEndingSoon) ...[
                    Card(
                      color: AppTheme.colorPending.withOpacity(0.15),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                        side: const BorderSide(color: AppTheme.colorPending, width: 1.5),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: [
                            const Icon(Icons.warning_amber_rounded, color: AppTheme.colorPending, size: 28),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    "Ending Soon",
                                    style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.colorPending),
                                  ),
                                  Text(
                                    "Scheduled to end on ${DateFormat('MMM dd, yyyy').format(DateTime.parse(plannedEndDateStr!))}.",
                                    style: const TextStyle(fontSize: 13),
                                  )
                                ],
                              ),
                            )
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Action Buttons based on status
                  _buildLifecycleActions(context, ref, status),
                  const SizedBox(height: 24),
                  
                  // Schedules
                  _buildSectionTitle("Schedules"),
                  if (schedules.isEmpty)
                    const Text("No schedule configured.")
                  else
                    ...schedules.map((s) => _buildScheduleCard(s)),
                  const SizedBox(height: 24),
                  
                  // Instructions
                  _buildSectionTitle("Instructions"),
                  _buildAddButton(context, ref, "Add Instruction", () => _showAddInstructionDialog(context, ref)),
                  const SizedBox(height: 8),
                  if (instructions.isEmpty)
                    const Text("No instructions recorded.")
                  else
                    ...instructions.map((i) => _buildInstructionCard(i)),
                  const SizedBox(height: 24),
                  
                  // Notes
                  _buildSectionTitle("Notes"),
                  _buildAddButton(context, ref, "Add Note", () => _showAddNoteDialog(context, ref)),
                  const SizedBox(height: 8),
                  if (notes.isEmpty)
                    const Text("No notes recorded.")
                  else
                    ...notes.map((n) => _buildNoteCard(n)),
                  const SizedBox(height: 48),
                ],
              ),
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: AppTheme.colorSkipped),
              const SizedBox(height: 16),
              Text(err.toString()),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
    Color color;
    IconData icon;
    switch (status) {
      case 'ACTIVE':
        color = AppTheme.colorTaken;
        icon = Icons.check_circle;
        break;
      case 'PAUSED':
        color = AppTheme.colorPaused;
        icon = Icons.pause_circle_filled;
        break;
      case 'FINISHED':
        color = AppTheme.colorFinished;
        icon = Icons.archive;
        break;
      default:
        color = AppTheme.colorPending;
        icon = Icons.help;
    }
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 6),
          Text(status, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _buildLifecycleActions(BuildContext context, WidgetRef ref, String status) {
    return Card(
      color: AppTheme.surfaceDark,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (status == 'ACTIVE') ...[
              ElevatedButton.icon(
                onPressed: () => _showPauseDialog(context, ref),
                icon: const Icon(Icons.pause),
                label: const Text("PAUSE MEDICATION"),
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.colorPaused),
              ),
              const SizedBox(height: 8),
              ElevatedButton.icon(
                onPressed: () => _showFinishDialog(context, ref),
                icon: const Icon(Icons.check_circle_outline),
                label: const Text("FINISH MEDICATION"),
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.colorFinished),
              ),
            ] else if (status == 'PAUSED') ...[
              ElevatedButton.icon(
                onPressed: () => _resumeMedicine(context, ref),
                icon: const Icon(Icons.play_arrow),
                label: const Text("RESUME MEDICATION"),
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.colorTaken),
              ),
              const SizedBox(height: 8),
              ElevatedButton.icon(
                onPressed: () => _showFinishDialog(context, ref),
                icon: const Icon(Icons.check_circle_outline),
                label: const Text("FINISH MEDICATION"),
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.colorFinished),
              ),
            ] else if (status == 'FINISHED') ...[
              ElevatedButton.icon(
                onPressed: () => _showUndoFinishDialog(context, ref),
                icon: const Icon(Icons.undo),
                label: const Text("UNDO FINISH STATE"),
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryTeal),
              ),
            ]
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        title.toUpperCase(),
        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, letterSpacing: 1.5, color: AppTheme.primaryTealLight),
      ),
    );
  }

  Widget _buildAddButton(BuildContext context, WidgetRef ref, String label, VoidCallback onTap) {
    return Align(
      alignment: Alignment.centerLeft,
      child: TextButton.icon(
        onPressed: onTap,
        icon: const Icon(Icons.add, size: 16),
        label: Text(label),
        style: TextButton.styleFrom(foregroundColor: AppTheme.primaryTealLight, padding: EdgeInsets.zero),
      ),
    );
  }

  Widget _buildScheduleCard(Map<String, dynamic> schedule) {
    // schedule contains version details directly
    final repeat = schedule["frequency"] ?? "DAILY";
    final timeStr = schedule["schedule_time"] ?? "--:--";
    final amount = schedule["dosage_amount"] ?? "0";
    final unit = schedule["dosage_unit_name"] ?? "";
    final start = schedule["start_date"] ?? "";
    final end = schedule["planned_end_date"];
    
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      color: AppTheme.backgroundDark,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              children: [
                const Icon(Icons.repeat, color: Colors.white54, size: 20),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    "$repeat at $timeStr",
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ),
                Text(
                  "$amount $unit",
                  style: const TextStyle(color: AppTheme.primaryTealLight, fontWeight: FontWeight.bold, fontSize: 16),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text("Start: ${DateFormat('MMM dd, yyyy').format(DateTime.parse(start))}", style: const TextStyle(fontSize: 12, color: Colors.white60)),
                if (end != null)
                  Text("End: ${DateFormat('MMM dd, yyyy').format(DateTime.parse(end))}", style: const TextStyle(fontSize: 12, color: Colors.white60))
                else
                  const Text("End: Continuous", style: TextStyle(fontSize: 12, color: Colors.white60)),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildInstructionCard(Map<String, dynamic> instruction) {
    final date = DateTime.parse(instruction["effective_from"]);
    final remark = instruction["remark"] ?? "No remark";
    final type = instruction["instruction_type"] ?? "INSTRUCTION";
    
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceDark,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.surfaceDarkBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(type, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppTheme.primaryTealLight)),
              Text(DateFormat('MMM dd, hh:mm a').format(date.toLocal()), style: const TextStyle(fontSize: 11, color: Colors.white38)),
            ],
          ),
          const SizedBox(height: 4),
          Text(remark, style: const TextStyle(fontSize: 14, color: Colors.white70)),
        ],
      ),
    );
  }

  Widget _buildNoteCard(Map<String, dynamic> note) {
    final date = DateTime.parse(note["created_at"]);
    final text = note["note"] ?? "";
    
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceDark,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.surfaceDarkBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Align(
            alignment: Alignment.topRight,
            child: Text(DateFormat('MMM dd, hh:mm a').format(date.toLocal()), style: const TextStyle(fontSize: 11, color: Colors.white38)),
          ),
          Text(text, style: const TextStyle(fontSize: 14, color: Colors.white70)),
        ],
      ),
    );
  }

  void _showPauseDialog(BuildContext context, WidgetRef ref) {
    final remarkController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Pause Medication"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text("Are you sure you want to pause this medicine? Doses and notifications will be suppressed."),
            const SizedBox(height: 16),
            TextField(
              controller: remarkController,
              decoration: const InputDecoration(
                labelText: "Pause Reason (Optional)",
                hintText: "e.g., Vacation, Doctor pause, etc.",
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
                await api.pauseMedicine(medicineId, remark: remarkController.text.trim());
                ref.refresh(medicineDetailsProvider(medicineId));
                ref.refresh(medicinesListProvider);
              } catch (e) {
                _showError(context, e.toString());
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.colorPaused),
            child: const Text("PAUSE"),
          ),
        ],
      ),
    );
  }

  Future<void> _resumeMedicine(BuildContext context, WidgetRef ref) async {
    final api = ref.read(apiServiceProvider);
    try {
      await api.resumeMedicine(medicineId);
      ref.refresh(medicineDetailsProvider(medicineId));
      ref.refresh(medicinesListProvider);
    } catch (e) {
      _showError(context, e.toString());
    }
  }

  void _showFinishDialog(BuildContext context, WidgetRef ref) {
    final remarkController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Finish Medication"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text("This medicine will be moved to Finished Medications. Existing history and records will remain."),
            const SizedBox(height: 16),
            TextField(
              controller: remarkController,
              decoration: const InputDecoration(
                labelText: "Remark (Optional)",
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
                await api.finishMedicine(medicineId);
                ref.refresh(medicineDetailsProvider(medicineId));
                ref.refresh(medicinesListProvider);
              } catch (e) {
                _showError(context, e.toString());
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.colorFinished),
            child: const Text("FINISH"),
          ),
        ],
      ),
    );
  }

  void _showUndoFinishDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Undo Finished State"),
        content: const Text(
          "WARNING: This medicine will become active again. The previous finish action will remain in the history timeline.",
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
                await api.undoFinishMedicine(medicineId);
                ref.refresh(medicineDetailsProvider(medicineId));
                ref.refresh(medicinesListProvider);
              } catch (e) {
                _showError(context, e.toString());
              }
            },
            child: const Text("CONFIRM"),
          ),
        ],
      ),
    );
  }

  void _showAddInstructionDialog(BuildContext context, WidgetRef ref) {
    final textController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Add Instruction"),
        content: TextField(
          controller: textController,
          decoration: const InputDecoration(
            labelText: "Instruction remark",
            hintText: "e.g., Take after food",
          ),
          maxLines: 2,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("CANCEL"),
          ),
          ElevatedButton(
            onPressed: () async {
              if (textController.text.isEmpty) return;
              Navigator.pop(context);
              final api = ref.read(apiServiceProvider);
              try {
                await api.createInstruction(medicineId, "RESUME", remark: textController.text.trim());
                ref.refresh(medicineDetailsProvider(medicineId));
              } catch (e) {
                _showError(context, e.toString());
              }
            },
            child: const Text("SAVE"),
          ),
        ],
      ),
    );
  }

  void _showAddNoteDialog(BuildContext context, WidgetRef ref) {
    final textController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Add Note"),
        content: TextField(
          controller: textController,
          decoration: const InputDecoration(
            labelText: "Note text",
          ),
          maxLines: 2,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("CANCEL"),
          ),
          ElevatedButton(
            onPressed: () async {
              if (textController.text.isEmpty) return;
              Navigator.pop(context);
              final api = ref.read(apiServiceProvider);
              try {
                await api.createNote(medicineId, textController.text.trim());
                ref.refresh(medicineDetailsProvider(medicineId));
              } catch (e) {
                _showError(context, e.toString());
              }
            },
            child: const Text("SAVE"),
          ),
        ],
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
