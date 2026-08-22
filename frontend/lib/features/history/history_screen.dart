import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'history_provider.dart';
import '../medicines/medicines_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/widgets/loading_indicator.dart';
import 'package:intl/intl.dart';
import 'dart:convert';

class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  String _getReadableType(String eventType) {
    switch (eventType) {
      case 'MEDICINE_CREATED':
        return "Medication Created";
      case 'MEDICINE_UPDATED':
        return "Medication Updated";
      case 'SCHEDULE_CREATED':
        return "Schedule Created";
      case 'SCHEDULE_UPDATED':
        return "Dosage Schedule Updated";
      case 'SCHEDULE_ENDED':
        return "Schedule Terminated";
      case 'DOSE_CREATED':
        return "Dose Added";
      case 'DOSE_TAKEN':
        return "Medicine Taken";
      case 'DOSE_SKIPPED':
        return "Dose Skipped";
      case 'DOSE_NOT_REQUIRED':
        return "Dose Paused / Suppressed";
      case 'DOSE_CORRECTED':
        return "Dose Action Corrected";
      case 'PAUSE_STARTED':
        return "Medication Paused";
      case 'MEDICINE_RESUMED':
        return "Medication Resumed";
      case 'MEDICINE_FINISHED':
        return "Medication Finished";
      case 'FINISH_UNDONE':
        return "Finish Undo Recorded";
      case 'NOTE_ADDED':
        return "Note Added";
      case 'INSTRUCTION_ADDED':
        return "Instruction Added";
      default:
        return eventType.replaceAll("_", " ");
    }
  }

  IconData _getHistoryIcon(String eventType) {
    switch (eventType) {
      case 'MEDICINE_CREATED':
        return Icons.add_circle_outline;
      case 'DOSE_TAKEN':
        return Icons.check_circle_outline;
      case 'DOSE_SKIPPED':
        return Icons.remove_circle_outline;
      case 'DOSE_CORRECTED':
        return Icons.edit_outlined;
      case 'PAUSE_STARTED':
        return Icons.pause_circle_outline;
      case 'MEDICINE_RESUMED':
        return Icons.play_circle_outline;
      case 'MEDICINE_FINISHED':
        return Icons.archive_outlined;
      case 'FINISH_UNDONE':
        return Icons.unarchive_outlined;
      case 'NOTE_ADDED':
        return Icons.note_add_outlined;
      default:
        return Icons.history;
    }
  }

  Color _getHistoryColor(String eventType) {
    switch (eventType) {
      case 'DOSE_TAKEN':
        return AppTheme.colorTaken;
      case 'DOSE_SKIPPED':
        return AppTheme.colorSkipped;
      case 'DOSE_CORRECTED':
        return AppTheme.primaryTealLight;
      case 'PAUSE_STARTED':
        return AppTheme.colorPaused;
      case 'MEDICINE_FINISHED':
        return AppTheme.colorFinished;
      default:
        return Colors.white70;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(historyLogsProvider);
    final filter = ref.watch(historyFilterProvider);
    final medicinesAsync = ref.watch(allMedicinesProvider);
    final typesAsync = ref.watch(medicineTypesListProvider);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text("Medication History"),
      ),
      body: Column(
        children: [
          // Filter Bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Column(
              children: [
                Row(
                  children: [
                    // Medicine Filter Dropdown
                    Expanded(
                      child: medicinesAsync.when(
                        data: (medicines) => DropdownButtonFormField<String?>(
                          value: filter.medicineId,
                          decoration: const InputDecoration(
                            labelText: "Filter Medicine",
                            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          ),
                          items: [
                            const DropdownMenuItem(value: null, child: Text("All Medications")),
                            ...medicines.map((m) => DropdownMenuItem(value: m.id, child: Text(m.name))),
                          ],
                          onChanged: (val) {
                            ref.read(historyFilterProvider.notifier).state =
                                filter.copyWith(medicineId: val, clearMedicine: val == null);
                          },
                        ),
                        loading: () => const SizedBox(height: 48, child: Center(child: LinearProgressIndicator())),
                        error: (e, s) => const Text("Error loading filter"),
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Medicine Type Filter Dropdown
                    Expanded(
                      child: typesAsync.when(
                        data: (types) => DropdownButtonFormField<String?>(
                          value: filter.medicineTypeId,
                          decoration: const InputDecoration(
                            labelText: "Filter Type",
                            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          ),
                          items: [
                            const DropdownMenuItem(value: null, child: Text("All Types")),
                            ...types.map((t) => DropdownMenuItem(value: t.id, child: Text(t.name))),
                          ],
                          onChanged: (val) {
                            ref.read(historyFilterProvider.notifier).state =
                                filter.copyWith(medicineTypeId: val, clearMedicineType: val == null);
                          },
                        ),
                        loading: () => const SizedBox(height: 48, child: Center(child: LinearProgressIndicator())),
                        error: (e, s) => const Text("Error loading filter"),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                // Event Type Filter
                DropdownButtonFormField<String?>(
                  value: filter.eventType,
                  decoration: const InputDecoration(
                    labelText: "Filter Event",
                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                  items: const [
                    DropdownMenuItem(value: null, child: Text("All Events")),
                    DropdownMenuItem(value: "DOSE_TAKEN", child: Text("Dose Taken")),
                    DropdownMenuItem(value: "DOSE_SKIPPED", child: Text("Dose Skipped")),
                    DropdownMenuItem(value: "DOSE_CORRECTED", child: Text("Dose Correction")),
                    DropdownMenuItem(value: "PAUSE_STARTED", child: Text("Medication Paused")),
                    DropdownMenuItem(value: "MEDICINE_FINISHED", child: Text("Medication Finished")),
                  ],
                  onChanged: (val) {
                    ref.read(historyFilterProvider.notifier).state =
                        filter.copyWith(eventType: val, clearEventType: val == null);
                  },
                ),
              ],
            ),
          ),
          
          const Divider(color: AppTheme.surfaceDarkBorder, height: 16),
          
          // History Log List
          Expanded(
            child: RefreshIndicator(
              onRefresh: () => ref.refresh(historyLogsProvider.future),
              child: historyAsync.when(
                data: (logs) {
                  if (logs.isEmpty) {
                    return const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.history_toggle_off, size: 64, color: AppTheme.colorPaused),
                          SizedBox(height: 16),
                          Text("No medication history found.", style: TextStyle(fontSize: 16)),
                        ],
                      ),
                    );
                  }
                  return ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: logs.length,
                    itemBuilder: (context, index) {
                      final log = logs[index];
                      final date = DateTime.parse(log["event_time"]);
                      final color = _getHistoryColor(log["event_type"]);
                      
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        color: AppTheme.surfaceDark,
                        child: ListTile(
                          onTap: () => _showTechnicalLogs(context, log),
                          leading: CircleAvatar(
                            backgroundColor: color.withOpacity(0.15),
                            child: Icon(_getHistoryIcon(log["event_type"]), color: color, size: 20),
                          ),
                          title: Text(
                            _getReadableType(log["event_type"]),
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const SizedBox(height: 4),
                              Text(
                                "${log["medicine_name"] ?? "Medication Details"} (${log["medicine_type_name"] ?? 'General'})",
                                style: const TextStyle(color: AppTheme.primaryTealLight, fontWeight: FontWeight.w600, fontSize: 13),
                              ),
                              if (log["remark"] != null) ...[
                                const SizedBox(height: 4),
                                Text(
                                  "Remark: ${log['remark']}",
                                  style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: Colors.white60),
                                ),
                              ],
                            ],
                          ),
                          trailing: Text(
                            DateFormat('MMM dd, hh:mm a').format(date.toLocal()),
                            style: const TextStyle(fontSize: 11, color: Colors.white38),
                          ),
                        ),
                      );
                    },
                  );
                },
                loading: () => const ServerLoadingIndicator(message: "Loading history logs..."),
                error: (err, stack) => Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, size: 48, color: AppTheme.colorSkipped),
                        const SizedBox(height: 16),
                        Text(err.toString()),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: () => ref.refresh(historyLogsProvider),
                          child: const Text("RETRY"),
                        ),
                      ],
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

  void _showTechnicalLogs(BuildContext context, Map<String, dynamic> log) {
    final theme = Theme.of(context);
    final encoder = const JsonEncoder.withIndent('  ');
    
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.surfaceDark,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  "Technical Audit Log",
                  style: theme.textTheme.titleMedium,
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const Divider(color: AppTheme.surfaceDarkBorder),
            const SizedBox(height: 12),
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _buildLogMetadata("History ID", log["id"]),
                    _buildLogMetadata("Event Type", log["event_type"]),
                    _buildLogMetadata("Medicine ID", log["medicine_id"]),
                    if (log["schedule_id"] != null) _buildLogMetadata("Schedule ID", log["schedule_id"]),
                    if (log["dose_id"] != null) _buildLogMetadata("Dose ID", log["dose_id"]),
                    _buildLogMetadata("Recorded At", log["event_time"]),
                    if (log["remark"] != null) _buildLogMetadata("User Remark", log["remark"]),
                    
                    const SizedBox(height: 16),
                    if (log["previous_data"] != null) ...[
                      const Text("PREVIOUS STATE:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppTheme.colorSkipped)),
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppTheme.backgroundDark,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          encoder.convert(log["previous_data"]),
                          style: const TextStyle(fontFamily: 'monospace', fontSize: 12, color: Colors.white70),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],
                    
                    if (log["new_data"] != null) ...[
                      const Text("NEW STATE:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppTheme.colorTaken)),
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppTheme.backgroundDark,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          encoder.convert(log["new_data"]),
                          style: const TextStyle(fontFamily: 'monospace', fontSize: 12, color: Colors.white70),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLogMetadata(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: RichText(
        text: TextSpan(
          style: const TextStyle(color: Colors.white70, fontSize: 14),
          children: [
            TextSpan(text: "$label: ", style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryTealLight)),
            TextSpan(text: value),
          ],
        ),
      ),
    );
  }
}
