import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../core/network/api_service.dart';
import '../../shared/models/timeline_models.dart';

final selectedDateProvider = StateProvider<DateTime>((ref) => DateTime.now());

final timelineEventsProvider = FutureProvider<List<ClusteredEvent>>((ref) async {
  final apiService = ref.watch(apiServiceProvider);
  final selectedDate = ref.watch(selectedDateProvider);
  final dateStr = DateFormat('yyyy-MM-dd').format(selectedDate);
  
  final list = await apiService.getTimeline(dateStr);
  return list.map((e) => ClusteredEvent.fromJson(e)).toList();
});
