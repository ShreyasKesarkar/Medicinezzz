import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'medicines_provider.dart';
import '../../core/network/api_service.dart';
import '../../core/theme/app_theme.dart';
import 'package:intl/intl.dart';

class CreateMedicineScreen extends ConsumerStatefulWidget {
  const CreateMedicineScreen({super.key});

  @override
  ConsumerState<CreateMedicineScreen> createState() => _CreateMedicineScreenState();
}

class _CreateMedicineScreenState extends ConsumerState<CreateMedicineScreen> {
  final _formKey = GlobalKey<FormState>();
  
  final _nameController = TextEditingController();
  final _dosageController = TextEditingController(text: "1.0");
  final _intervalController = TextEditingController(text: "3");
  final _instructionController = TextEditingController();
  final _noteController = TextEditingController();
  final _remarkController = TextEditingController();
  
  // Custom type / unit helpers
  final _customTypeController = TextEditingController();
  final _customUnitController = TextEditingController();
  
  String? _selectedTypeId;
  String? _selectedUnitId;
  bool _isCustomType = false;
  bool _isCustomUnit = false;
  
  TimeOfDay _scheduleTime = const TimeOfDay(hour: 8, minute: 0);
  String _frequency = "DAILY"; // DAILY, WEEKLY, EVERY_N_DAYS
  int _weekday = 1; // 1=Mon, 7=Sun
  
  DateTime _startDate = DateTime.now();
  DateTime? _endDate;
  
  bool _isLoading = false;

  @override
  void dispose() {
    _nameController.dispose();
    _dosageController.dispose();
    _intervalController.dispose();
    _instructionController.dispose();
    _noteController.dispose();
    _remarkController.dispose();
    _customTypeController.dispose();
    _customUnitController.dispose();
    super.dispose();
  }

  Future<void> _selectTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _scheduleTime,
    );
    if (picked != null) {
      setState(() => _scheduleTime = picked);
    }
  }

  Future<void> _selectStartDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _startDate,
      firstDate: DateTime.now().subtract(const Duration(days: 30)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() => _startDate = picked);
    }
  }

  Future<void> _selectEndDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _endDate ?? _startDate.add(const Duration(days: 7)),
      firstDate: _startDate,
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() => _endDate = picked);
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);
    
    // Format schedule time as "HH:MM"
    final timeStr = "${_scheduleTime.hour.toString().padLeft(2, '0')}:${_scheduleTime.minute.toString().padLeft(2, '0')}";
    
    final Map<String, dynamic> payload = {
      "name": _nameController.text.trim(),
      "dosage_amount": double.parse(_dosageController.text),
      "schedule_time": timeStr,
      "frequency": _frequency,
      "start_date": DateFormat('yyyy-MM-dd').format(_startDate),
    };
    
    if (_isCustomType) {
      payload["medicine_type_name"] = _customTypeController.text.trim();
    } else {
      payload["medicine_type_id"] = _selectedTypeId;
    }
    
    if (_isCustomUnit) {
      payload["dosage_unit_name"] = _customUnitController.text.trim();
    } else {
      payload["dosage_unit_id"] = _selectedUnitId;
    }
    
    if (_frequency == "WEEKLY") {
      payload["weekday"] = _weekday;
    } else if (_frequency == "EVERY_N_DAYS") {
      payload["interval_days"] = int.parse(_intervalController.text);
    }
    
    if (_endDate != null) {
      payload["planned_end_date"] = DateFormat('yyyy-MM-dd').format(_endDate!);
    }
    
    if (_instructionController.text.isNotEmpty) {
      payload["instruction_remark"] = _instructionController.text.trim();
    }
    
    if (_noteController.text.isNotEmpty) {
      payload["note"] = _noteController.text.trim();
    }
    
    if (_remarkController.text.isNotEmpty) {
      payload["remark"] = _remarkController.text.trim();
    }
    
    final api = ref.read(apiServiceProvider);
    try {
      await api.createMedicine(payload);
      ref.invalidate(medicineTypesListProvider);
      ref.invalidate(dosageUnitsListProvider);
      if (!mounted) return;
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Medicine created successfully!"),
          backgroundColor: AppTheme.colorTaken,
          behavior: SnackBarBehavior.floating,
        ),
      );
      Navigator.pop(context);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString()),
          backgroundColor: AppTheme.colorSkipped,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final typesAsync = ref.watch(medicineTypesListProvider);
    final unitsAsync = ref.watch(dosageUnitsListProvider);
    final theme = Theme.of(context);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text("Add Medication"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Section 1: Basic Info
                    _buildSectionHeader("1. GENERAL DETAILS"),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          children: [
                            TextFormField(
                              controller: _nameController,
                              decoration: const InputDecoration(
                                labelText: "Medicine Name",
                                prefixIcon: Icon(Icons.medication_outlined),
                              ),
                              validator: (value) {
                                if (value == null || value.isEmpty) return "Name is required";
                                return null;
                              },
                            ),
                            const SizedBox(height: 16),
                            typesAsync.when(
                              data: (types) => _isCustomType
                                  ? TextFormField(
                                      controller: _customTypeController,
                                      decoration: InputDecoration(
                                        labelText: "Custom Medicine Type",
                                        prefixIcon: const Icon(Icons.category_outlined),
                                        suffixIcon: TextButton(
                                          onPressed: () => setState(() => _isCustomType = false),
                                          child: const Text("Select List"),
                                        ),
                                      ),
                                      validator: (value) {
                                        if (_isCustomType && (value == null || value.isEmpty)) {
                                          return "Enter custom type name";
                                        }
                                        return null;
                                      },
                                    )
                                  : DropdownButtonFormField<String>(
                                      decoration: InputDecoration(
                                        labelText: "Medicine Type",
                                        prefixIcon: const Icon(Icons.category_outlined),
                                        suffixIcon: TextButton(
                                          onPressed: () => setState(() => _isCustomType = true),
                                          child: const Text("Create Custom"),
                                        ),
                                      ),
                                      value: _selectedTypeId,
                                      items: types
                                          .map((t) => DropdownMenuItem(value: t.id, child: Text(t.name)))
                                          .toList(),
                                      onChanged: (val) => setState(() => _selectedTypeId = val),
                                    ),
                              loading: () => const LinearProgressIndicator(),
                              error: (e, s) => Text("Failed to load types: $e"),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    
                    // Section 2: Dosage Info
                    _buildSectionHeader("2. DOSAGE DETAILS"),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          children: [
                            TextFormField(
                              controller: _dosageController,
                              decoration: const InputDecoration(
                                labelText: "Dosage Amount",
                                prefixIcon: Icon(Icons.scale_outlined),
                                helperText: "e.g., 1.0, 1.5, 0.5",
                              ),
                              keyboardType: const TextInputType.numberWithOptions(decimal: true),
                              validator: (value) {
                                if (value == null || value.isEmpty) return "Amount is required";
                                if (double.tryParse(value) == null) return "Must be a valid decimal number";
                                return null;
                              },
                            ),
                            const SizedBox(height: 16),
                            unitsAsync.when(
                              data: (units) {
                                if (_selectedUnitId == null && units.isNotEmpty) {
                                  _selectedUnitId = units.first.id;
                                }
                                return _isCustomUnit
                                    ? TextFormField(
                                        controller: _customUnitController,
                                        decoration: InputDecoration(
                                          labelText: "Custom Dosage Unit",
                                          prefixIcon: const Icon(Icons.ad_units_outlined),
                                          suffixIcon: TextButton(
                                            onPressed: () => setState(() => _isCustomUnit = false),
                                            child: const Text("Select List"),
                                          ),
                                        ),
                                        validator: (value) {
                                          if (_isCustomUnit && (value == null || value.isEmpty)) {
                                            return "Enter custom unit name";
                                          }
                                          return null;
                                        },
                                      )
                                    : DropdownButtonFormField<String>(
                                        decoration: InputDecoration(
                                          labelText: "Dosage Unit",
                                          prefixIcon: const Icon(Icons.ad_units_outlined),
                                          suffixIcon: TextButton(
                                            onPressed: () => setState(() => _isCustomUnit = true),
                                            child: const Text("Create Custom"),
                                          ),
                                        ),
                                        value: _selectedUnitId,
                                        items: units
                                            .map((u) => DropdownMenuItem(value: u.id, child: Text(u.name)))
                                            .toList(),
                                        onChanged: (val) => setState(() => _selectedUnitId = val),
                                      );
                              },
                              loading: () => const LinearProgressIndicator(),
                              error: (e, s) => Text("Failed to load units: $e"),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    
                    // Section 3: Schedule Pattern
                    _buildSectionHeader("3. SCHEDULE CONFIGURATION"),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            ListTile(
                              title: const Text("Schedule Time", style: TextStyle(fontWeight: FontWeight.bold)),
                              trailing: Text(
                                "${_scheduleTime.hour.toString().padLeft(2, '0')}:${_scheduleTime.minute.toString().padLeft(2, '0')}",
                                style: const TextStyle(fontSize: 18, color: AppTheme.primaryTealLight, fontWeight: FontWeight.bold),
                              ),
                              onTap: _selectTime,
                            ),
                            const Divider(color: AppTheme.surfaceDarkBorder),
                            DropdownButtonFormField<String>(
                              decoration: const InputDecoration(labelText: "Repeat Pattern"),
                              value: _frequency,
                              items: const [
                                DropdownMenuItem(value: "DAILY", child: Text("Daily")),
                                DropdownMenuItem(value: "WEEKLY", child: Text("Weekly")),
                                DropdownMenuItem(value: "EVERY_N_DAYS", child: Text("Every N Days")),
                              ],
                              onChanged: (val) {
                                if (val != null) setState(() => _frequency = val);
                              },
                            ),
                            if (_frequency == "WEEKLY") ...[
                              const SizedBox(height: 16),
                              DropdownButtonFormField<int>(
                                decoration: const InputDecoration(labelText: "Select Weekday"),
                                value: _weekday,
                                items: const [
                                  DropdownMenuItem(value: 1, child: Text("Monday")),
                                  DropdownMenuItem(value: 2, child: Text("Tuesday")),
                                  DropdownMenuItem(value: 3, child: Text("Wednesday")),
                                  DropdownMenuItem(value: 4, child: Text("Thursday")),
                                  DropdownMenuItem(value: 5, child: Text("Friday")),
                                  DropdownMenuItem(value: 6, child: Text("Saturday")),
                                  DropdownMenuItem(value: 7, child: Text("Sunday")),
                                ],
                                onChanged: (val) {
                                  if (val != null) setState(() => _weekday = val);
                                },
                              ),
                            ] else if (_frequency == "EVERY_N_DAYS") ...[
                              const SizedBox(height: 16),
                              TextFormField(
                                controller: _intervalController,
                                decoration: const InputDecoration(
                                  labelText: "Repeat Interval (Days)",
                                  prefixIcon: Icon(Icons.repeat),
                                ),
                                keyboardType: TextInputType.number,
                                validator: (value) {
                                  if (_frequency == "EVERY_N_DAYS") {
                                    if (value == null || value.isEmpty) return "Interval is required";
                                    final valInt = int.tryParse(value);
                                    if (valInt == null || valInt <= 0) return "Must be a positive integer";
                                  }
                                  return null;
                                },
                              ),
                            ],
                            const SizedBox(height: 16),
                            ListTile(
                              title: const Text("Start Date", style: TextStyle(fontWeight: FontWeight.bold)),
                              trailing: Text(
                                DateFormat('MMM dd, yyyy').format(_startDate),
                                style: const TextStyle(fontSize: 16, color: Colors.white, fontWeight: FontWeight.bold),
                              ),
                              onTap: _selectStartDate,
                            ),
                            ListTile(
                              title: const Text("End Date (Optional)", style: TextStyle(fontWeight: FontWeight.bold)),
                              trailing: Text(
                                _endDate != null ? DateFormat('MMM dd, yyyy').format(_endDate!) : "No end date set",
                                style: TextStyle(
                                    fontSize: 16, 
                                    color: _endDate != null ? Colors.white : Colors.white54,
                                    fontWeight: FontWeight.bold
                                ),
                              ),
                              onTap: _selectEndDate,
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    
                    // Section 4: Instructions/Notes
                    _buildSectionHeader("4. ADDITIONAL DETAILS"),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          children: [
                            TextFormField(
                              controller: _instructionController,
                              decoration: const InputDecoration(
                                labelText: "Medication Instructions (Optional)",
                                prefixIcon: Icon(Icons.integration_instructions_outlined),
                                hintText: "e.g., Take after food",
                              ),
                            ),
                            const SizedBox(height: 16),
                            TextFormField(
                              controller: _noteController,
                              decoration: const InputDecoration(
                                labelText: "Additional Notes (Optional)",
                                prefixIcon: Icon(Icons.note_alt_outlined),
                              ),
                            ),
                            const SizedBox(height: 16),
                            TextFormField(
                              controller: _remarkController,
                              decoration: const InputDecoration(
                                labelText: "Audit Remark (Optional)",
                                prefixIcon: Icon(Icons.history_toggle_off_outlined),
                                hintText: "Why are you adding this medicine?",
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 32),
                    
                    ElevatedButton(
                      onPressed: _save,
                      child: const Text("CREATE MEDICINE"),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
      child: Text(
        title,
        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, letterSpacing: 1.5, color: AppTheme.primaryTealLight),
      ),
    );
  }
}
