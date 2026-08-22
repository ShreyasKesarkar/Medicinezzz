class Medicine {
  final String id;
  final String patientId;
  final String name;
  final String? medicineTypeId;
  final String? medicineTypeName;
  final String status;
  final String? previousMedicineId;
  final DateTime? finishedAt;
  final DateTime? stoppedAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  Medicine({
    required this.id,
    required this.patientId,
    required this.name,
    this.medicineTypeId,
    this.medicineTypeName,
    required this.status,
    this.previousMedicineId,
    this.finishedAt,
    this.stoppedAt,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Medicine.fromJson(Map<String, dynamic> json) {
    return Medicine(
      id: json['id'],
      patientId: json['patient_id'],
      name: json['name'],
      medicineTypeId: json['medicine_type_id'],
      medicineTypeName: json['medicine_type_name'],
      status: json['status'],
      previousMedicineId: json['previous_medicine_id'],
      finishedAt: json['finished_at'] != null ? DateTime.parse(json['finished_at']) : null,
      stoppedAt: json['stopped_at'] != null ? DateTime.parse(json['stopped_at']) : null,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}

class MedicineType {
  final String id;
  final String name;

  MedicineType({required this.id, required this.name});

  factory MedicineType.fromJson(Map<String, dynamic> json) {
    return MedicineType(
      id: json['id'],
      name: json['name'],
    );
  }
}

class DosageUnit {
  final String id;
  final String name;

  DosageUnit({required this.id, required this.name});

  factory DosageUnit.fromJson(Map<String, dynamic> json) {
    return DosageUnit(
      id: json['id'],
      name: json['name'],
    );
  }
}
