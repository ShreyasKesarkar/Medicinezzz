import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/api_service.dart';
import '../../shared/models/medicine_models.dart';

final medicinesStatusFilterProvider = StateProvider<String?>((ref) => null);

final medicinesListProvider = FutureProvider<List<Medicine>>((ref) async {
  final apiService = ref.watch(apiServiceProvider);
  final statusFilter = ref.watch(medicinesStatusFilterProvider);
  
  final list = await apiService.getMedicines(status: statusFilter);
  return list.map((m) => Medicine.fromJson(m)).toList();
});

final allMedicinesProvider = FutureProvider<List<Medicine>>((ref) async {
  final apiService = ref.watch(apiServiceProvider);
  final list = await apiService.getMedicines();
  return list.map((m) => Medicine.fromJson(m)).toList();
});

final medicineDetailsProvider = FutureProvider.family<Map<String, dynamic>, String>((ref, id) async {
  final apiService = ref.watch(apiServiceProvider);
  return await apiService.getMedicineDetails(id);
});

final medicineTypesListProvider = FutureProvider<List<MedicineType>>((ref) async {
  final apiService = ref.watch(apiServiceProvider);
  final list = await apiService.getMedicineTypes();
  return list.map((t) => MedicineType.fromJson(t)).toList();
});

final dosageUnitsListProvider = FutureProvider<List<DosageUnit>>((ref) async {
  final apiService = ref.watch(apiServiceProvider);
  final list = await apiService.getDosageUnits();
  return list.map((u) => DosageUnit.fromJson(u)).toList();
});
