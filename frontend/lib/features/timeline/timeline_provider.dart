import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../core/network/api_service.dart';
import '../../shared/models/timeline_models.dart';
import '../notifications/notification_service.dart';

final selectedDateProvider = StateProvider<DateTime>((ref) => DateTime.now());

final timelineEventsProvider = FutureProvider<List<ClusteredEvent>>((ref) async {
  final apiService = ref.watch(apiServiceProvider);
  final selectedDate = ref.watch(selectedDateProvider);
  final dateStr = DateFormat('yyyy-MM-dd').format(selectedDate);
  
  final list = await apiService.getTimeline(dateStr);
  final events = list.map((e) => ClusteredEvent.fromJson(e)).toList();
  
  // Dynamically schedule local notifications in Android for future pending doses
  _scheduleLocalNotifications(events);
  
  return events;
});

void _scheduleLocalNotifications(List<ClusteredEvent> events) async {
  try {
    // 1. Cancel previously scheduled local notifications to avoid duplicates
    await NotificationService.cancelAllNotifications();
    
    // 2. Schedule notifications for future pending doses
    final now = DateTime.now();
    for (final event in events) {
      for (final dose in event.doses) {
        if (dose.status == 'PENDING' && dose.scheduledAt.isAfter(now)) {
          // Hash the UUID string into a unique 32-bit integer ID for the notification
          final notificationId = dose.id.hashCode;
          
          await NotificationService.scheduleNotification(
            id: notificationId,
            title: "Time for ${dose.medicineName}!",
            body: "Please take ${dose.dosageAmount} ${dose.dosageUnitName}.",
            scheduledDate: dose.scheduledAt,
            payload: dose.id,
          );
        }
      }
    }
  } catch (e) {
    print("Error scheduling local notifications: $e");
  }
}
