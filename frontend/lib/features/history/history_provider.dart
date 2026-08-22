import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/api_service.dart';

class HistoryFilter {
  final String? medicineId;
  final String? eventType;
  final String? medicineTypeId;
  final int limit;
  final int offset;

  HistoryFilter({
    this.medicineId,
    this.eventType,
    this.medicineTypeId,
    this.limit = 50,
    this.offset = 0,
  });

  HistoryFilter copyWith({
    String? medicineId,
    String? eventType,
    String? medicineTypeId,
    int? limit,
    int? offset,
    bool clearMedicine = false,
    bool clearEventType = false,
    bool clearMedicineType = false,
  }) {
    return HistoryFilter(
      medicineId: clearMedicine ? null : (medicineId ?? this.medicineId),
      eventType: clearEventType ? null : (eventType ?? this.eventType),
      medicineTypeId: clearMedicineType ? null : (medicineTypeId ?? this.medicineTypeId),
      limit: limit ?? this.limit,
      offset: offset ?? this.offset,
    );
  }
}

final historyFilterProvider = StateProvider<HistoryFilter>((ref) => HistoryFilter());

final historyLogsProvider = FutureProvider<List<dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  final filter = ref.watch(historyFilterProvider);
  
  return await api.getHistory(
    medicineId: filter.medicineId,
    eventType: filter.eventType,
    medicineTypeId: filter.medicineTypeId,
    limit: filter.limit,
    offset: filter.offset,
  );
});
