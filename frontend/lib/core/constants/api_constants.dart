import 'package:flutter/foundation.dart';
import 'dart:io' show Platform;

class ApiConstants {
  static String get baseUrl {
    if (kDebugMode) {
      if (kIsWeb) {
        return "http://localhost:8000/api/v1";
      }
      try {
        if (Platform.isAndroid) {
          return "http://10.0.2.2:8000/api/v1";
        }
      } catch (_) {}
      return "http://localhost:8000/api/v1";
    } else {
      // TODO: Replace with your actual Render web service URL once deployed
      return "https://medicinezzz-backend.onrender.com/api/v1";
    }
  }

  static const String supabaseUrl = "https://xddmwrkjcxtffrnvwevq.supabase.co";
  static const String supabaseAnonKey = "sb_publishable_Kljlpz8q5_CxKxAcnewqgQ_bcimKf5D";
}
