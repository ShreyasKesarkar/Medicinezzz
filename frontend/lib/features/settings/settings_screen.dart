import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../auth/auth_provider.dart';
import '../../core/network/api_service.dart';
import '../../core/theme/app_theme.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  bool _notificationsEnabled = true;
  bool _isLoading = false;
  Map<String, dynamic>? _profile;

  @override
  void initState() {
    super.initState();
    _loadPreferences();
    _fetchProfile();
  }

  Future<void> _loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _notificationsEnabled = prefs.getBool('notifications_enabled') ?? true;
    });
  }

  Future<void> _toggleNotifications(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('notifications_enabled', value);
    setState(() {
      _notificationsEnabled = value;
    });
  }

  Future<void> _fetchProfile() async {
    setState(() => _isLoading = true);
    final api = ref.read(apiServiceProvider);
    try {
      final profile = await api.getMe();
      setState(() => _profile = profile);
    } catch (e) {
      // Profile fetch failed
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _logout() async {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Log Out"),
        content: const Text("Are you sure you want to log out from Medicinezzz?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("CANCEL"),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              await Supabase.instance.client.auth.signOut();
              if (!mounted) return;
              Navigator.pushReplacementNamed(context, '/login');
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.colorSkipped),
            child: const Text("LOG OUT"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(currentUserProvider);
    final theme = Theme.of(context);
    
    return Scaffold(
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // User Profile Section
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    const CircleAvatar(
                      radius: 36,
                      backgroundColor: AppTheme.primaryTeal,
                      child: Icon(Icons.person, size: 40, color: Colors.white),
                    ),
                    const SizedBox(height: 16),
                    _isLoading
                        ? const Center(child: CircularProgressIndicator())
                        : Text(
                            _profile?["full_name"] ?? user?.email?.split('@')[0] ?? "Patient Profile",
                            style: theme.textTheme.titleMedium?.copyWith(fontSize: 20),
                          ),
                    const SizedBox(height: 4),
                    Text(
                      user?.email ?? "",
                      style: theme.textTheme.bodyMedium,
                    ),
                    if (_profile != null) ...[
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.public, size: 14, color: AppTheme.primaryTealLight),
                          const SizedBox(width: 6),
                          Text(
                            "Timezone: ${_profile!['timezone']}",
                            style: const TextStyle(fontSize: 12, color: Colors.white70),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            
            // Settings Preferences Card
            const Text(
              "PREFERENCES",
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.5, color: AppTheme.primaryTealLight),
            ),
            const SizedBox(height: 8),
            Card(
              child: Column(
                children: [
                  SwitchListTile(
                    title: const Text("Enable Reminders", style: TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: const Text("Receive local push reminders for clustered events"),
                    activeColor: AppTheme.primaryTealLight,
                    value: _notificationsEnabled,
                    onChanged: _toggleNotifications,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // About and Info
            const Text(
              "APPLICATION INFO",
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.5, color: AppTheme.primaryTealLight),
            ),
            const SizedBox(height: 8),
            Card(
              child: Column(
                children: [
                  const ListTile(
                    title: Text("Version"),
                    trailing: Text("1.0.0", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
                  ),
                  const Divider(color: AppTheme.surfaceDarkBorder, height: 1),
                  ListTile(
                    title: const Text("API Status"),
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.colorTaken.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppTheme.colorTaken.withOpacity(0.5)),
                      ),
                      child: const Text("CONNECTED", style: TextStyle(color: AppTheme.colorTaken, fontSize: 11, fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            
            // Logout
            ElevatedButton.icon(
              onPressed: _logout,
              icon: const Icon(Icons.logout),
              label: const Text("LOG OUT"),
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.colorSkipped),
            ),
            const SizedBox(height: 48),
          ],
        ),
      ),
    );
  }
}
