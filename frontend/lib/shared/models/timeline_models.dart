class DoseDetails {
  final String id;
  final String eventId;
  final String medicineId;
  final String medicineName;
  final String? medicineTypeName;
  final String scheduleId;
  final String scheduleVersionId;
  final double dosageAmount;
  final String dosageUnitName;
  final DateTime scheduledAt;
  final String status;
  final DateTime? actualTakenAt;
  final DateTime? statusChangedAt;
  final String? statusRemark;

  DoseDetails({
    required this.id,
    required this.eventId,
    required this.medicineId,
    required this.medicineName,
    this.medicineTypeName,
    required this.scheduleId,
    required this.scheduleVersionId,
    required this.dosageAmount,
    required this.dosageUnitName,
    required this.scheduledAt,
    required this.status,
    this.actualTakenAt,
    this.statusChangedAt,
    this.statusRemark,
  });

  factory DoseDetails.fromJson(Map<String, dynamic> json) {
    return DoseDetails(
      id: json['id'],
      eventId: json['event_id'],
      medicineId: json['medicine_id'],
      medicineName: json['medicine_name'],
      medicineTypeName: json['medicine_type_name'],
      scheduleId: json['schedule_id'],
      scheduleVersionId: json['schedule_version_id'],
      dosageAmount: (json['dosage_amount'] as num).toDouble(),
      dosageUnitName: json['dosage_unit_name'],
      scheduledAt: _parseNaive(json['scheduled_at']),
      status: json['status'],
      actualTakenAt: json['actual_taken_at'] != null ? _parseNaive(json['actual_taken_at']) : null,
      statusChangedAt: json['status_changed_at'] != null ? _parseNaive(json['status_changed_at']) : null,
      statusRemark: json['status_remark'],
    );
  }
}

class ClusteredEvent {
  final String eventId;
  final DateTime scheduledAt;
  final List<DoseDetails> doses;

  ClusteredEvent({
    required this.eventId,
    required this.scheduledAt,
    required this.doses,
  });

  factory ClusteredEvent.fromJson(Map<String, dynamic> json) {
    return ClusteredEvent(
      eventId: json['event_id'],
      scheduledAt: _parseNaive(json['scheduled_at']),
      doses: (json['doses'] as List).map((d) => DoseDetails.fromJson(d)).toList(),
    );
  }
}

DateTime _parseNaive(String isoStr) {
  String clean = isoStr;
  if (clean.contains('+')) {
    clean = clean.split('+').first;
  } else if (clean.contains('-') && clean.indexOf('-') != clean.lastIndexOf('-')) {
    final lastDash = clean.lastIndexOf('-');
    if (lastDash > 10) { // after date part (YYYY-MM-DD)
      clean = clean.substring(0, lastDash);
    }
  } else if (clean.endsWith('Z')) {
    clean = clean.substring(0, clean.length - 1);
  }
  return DateTime.parse(clean);
}
