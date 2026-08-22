import 'package:dio/dio.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../constants/api_constants.dart';

class DioClient {
  final Dio _dio;

  DioClient() : _dio = Dio(BaseOptions(
    baseUrl: ApiConstants.baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    }
  )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final session = Supabase.instance.client.auth.currentSession;
        if (session != null) {
          options.headers["Authorization"] = "Bearer ${session.accessToken}";
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        if (e.response != null && e.response?.data is Map) {
          final errorData = e.response?.data["error"];
          if (errorData != null && errorData is Map) {
            final code = errorData["code"] ?? "ERROR";
            final message = errorData["message"] ?? "An unexpected error occurred.";
            
            return handler.reject(
              DioException(
                requestOptions: e.requestOptions,
                response: e.response,
                type: e.type,
                error: ApiException(code: code, message: message),
              ),
            );
          }
        }
        return handler.next(e);
      },
    ));
  }

  Dio get dio => _dio;
}

class ApiException implements Exception {
  final String code;
  final String message;

  ApiException({required this.code, required this.message});

  @override
  String toString() => message;
}
