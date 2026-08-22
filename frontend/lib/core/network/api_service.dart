import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dio_client.dart';

final dioClientProvider = Provider<DioClient>((ref) {
  return DioClient();
});

final apiServiceProvider = Provider<ApiService>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return ApiService(dioClient.dio);
});

class ApiService {
  final Dio _dio;

  ApiService(this._dio);

  Future<Map<String, dynamic>> getMe() async {
    final response = await _dio.get("/me");
    return response.data["data"];
  }

  Future<List<dynamic>> getTimeline(String dateIso) async {
    final response = await _dio.get("/timeline", queryParameters: {"date": dateIso});
    return response.data["data"];
  }

  Future<List<dynamic>> getMedicines({String? status}) async {
    final response = await _dio.get("/medicines", queryParameters: status != null ? {"status": status} : null);
    return response.data["data"];
  }

  Future<List<dynamic>> getMedicineTypes() async {
    final response = await _dio.get("/medicines/types");
    return response.data["data"];
  }

  Future<List<dynamic>> getDosageUnits() async {
    final response = await _dio.get("/medicines/units");
    return response.data["data"];
  }

  Future<Map<String, dynamic>> getMedicineDetails(String id) async {
    final response = await _dio.get("/medicines/$id");
    return response.data["data"];
  }

  Future<Map<String, dynamic>> createMedicine(Map<String, dynamic> data) async {
    final response = await _dio.post("/medicines", data: data);
    return response.data["data"];
  }

  Future<void> editMedicine(String id, Map<String, dynamic> data) async {
    await _dio.patch("/medicines/$id", data: data);
  }

  Future<void> pauseMedicine(String id, {String? remark}) async {
    await _dio.post("/medicines/$id/pause", data: remark != null ? {"remark": remark} : null);
  }

  Future<void> resumeMedicine(String id) async {
    await _dio.post("/medicines/$id/resume");
  }

  Future<void> finishMedicine(String id) async {
    await _dio.post("/medicines/$id/finish");
  }

  Future<void> undoFinishMedicine(String id) async {
    await _dio.post("/medicines/$id/undo-finish");
  }

  Future<Map<String, dynamic>> takeDose(String doseId, {String? remark}) async {
    final response = await _dio.post("/doses/$doseId/take", data: remark != null ? {"remark": remark} : null);
    return response.data["data"];
  }

  Future<Map<String, dynamic>> skipDose(String doseId, {String? remark}) async {
    final response = await _dio.post("/doses/$doseId/skip", data: remark != null ? {"remark": remark} : null);
    return response.data["data"];
  }

  Future<Map<String, dynamic>> correctDose(String doseId, String status, {String? remark}) async {
    final response = await _dio.post("/doses/$doseId/correct", data: {
      "status": status,
      "remark": remark,
    });
    return response.data["data"];
  }

  Future<List<dynamic>> getHistory({String? medicineId, String? eventType, String? medicineTypeId, int limit = 50, int offset = 0}) async {
    final queryParams = <String, dynamic>{
      "limit": limit,
      "offset": offset,
    };
    if (medicineId != null) queryParams["medicine_id"] = medicineId;
    if (eventType != null) queryParams["event_type"] = eventType;
    if (medicineTypeId != null) queryParams["medicine_type_id"] = medicineTypeId;
    
    final response = await _dio.get("/history", queryParameters: queryParams);
    return response.data["data"];
  }

  Future<List<dynamic>> getInstructions(String medicineId) async {
    final response = await _dio.get("/medicines/$medicineId/instructions");
    return response.data["data"];
  }

  Future<Map<String, dynamic>> createInstruction(String medicineId, String type, {String? remark}) async {
    final response = await _dio.post("/medicines/$medicineId/instructions", data: {
      "instruction_type": type,
      "remark": remark,
    });
    return response.data["data"];
  }

  Future<List<dynamic>> getNotes(String medicineId) async {
    final response = await _dio.get("/medicines/$medicineId/notes");
    return response.data["data"];
  }

  Future<Map<String, dynamic>> createNote(String medicineId, String note) async {
    final response = await _dio.post("/medicines/$medicineId/notes", data: {
      "note": note,
    });
    return response.data["data"];
  }
}
