import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

class NotificationService {
  static final FlutterLocalNotificationsPlugin _notificationsPlugin =
      FlutterLocalNotificationsPlugin();

  static Future<void> init() async {
    if (kIsWeb) return;
    
    try {
      tz.initializeTimeZones();
      try {
        tz.setLocalLocation(tz.getLocation('Asia/Kolkata'));
      } catch (_) {
        tz.setLocalLocation(tz.UTC);
      }
      
      const AndroidInitializationSettings initializationSettingsAndroid =
          AndroidInitializationSettings('@mipmap/ic_launcher');
          
      const InitializationSettings initializationSettings = InitializationSettings(
        android: initializationSettingsAndroid,
      );
      
      await _notificationsPlugin.initialize(
        settings: initializationSettings,
        onDidReceiveNotificationResponse: (details) {
          debugPrint("Notification tapped: ${details.payload}");
        },
      );
    } catch (e) {
      debugPrint("Failed to initialize notifications: $e");
    }
  }

  static Future<void> showNotification({
    required int id,
    required String title,
    required String body,
    String? payload,
  }) async {
    if (kIsWeb) {
      debugPrint("Web Notification: $title - $body");
      return;
    }
    
    try {
      const AndroidNotificationDetails androidDetails = AndroidNotificationDetails(
        'medicine_tracker_channel',
        'Medication Reminders',
        channelDescription: 'Reminds you to take scheduled doses',
        importance: Importance.max,
        priority: Priority.high,
      );
      
      const NotificationDetails details = NotificationDetails(
        android: androidDetails,
      );
      
      await _notificationsPlugin.show(
        id: id,
        title: title,
        body: body,
        notificationDetails: details,
        payload: payload,
      );
    } catch (e) {
      debugPrint("Failed to show notification: $e");
    }
  }

  static Future<void> scheduleNotification({
    required int id,
    required String title,
    required String body,
    required DateTime scheduledDate,
    String? payload,
  }) async {
    if (kIsWeb) return;
    
    try {
      const AndroidNotificationDetails androidDetails = AndroidNotificationDetails(
        'medicine_tracker_channel',
        'Medication Reminders',
        channelDescription: 'Reminds you to take scheduled doses',
        importance: Importance.max,
        priority: Priority.high,
      );
      
      const NotificationDetails details = NotificationDetails(
        android: androidDetails,
      );
      
      await _notificationsPlugin.zonedSchedule(
        id: id,
        title: title,
        body: body,
        scheduledDate: tz.TZDateTime.from(scheduledDate, tz.local),
        notificationDetails: details,
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        payload: payload,
      );
    } catch (e) {
      debugPrint("Failed to schedule notification: $e");
    }
  }

  static Future<void> cancelAllNotifications() async {
    if (kIsWeb) return;
    try {
      await _notificationsPlugin.cancelAll();
    } catch (e) {
      debugPrint("Failed to cancel notifications: $e");
    }
  }
}
