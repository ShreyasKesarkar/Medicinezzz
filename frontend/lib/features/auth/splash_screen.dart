import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'auth_provider.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    await Future.delayed(const Duration(milliseconds: 1500));
    if (!mounted) return;
    
    final authenticated = ref.read(isAuthenticatedProvider);
    if (authenticated) {
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.medical_services_outlined, size: 80, color: Color(0xFF0D9488)),
            const SizedBox(height: 24),
            Text(
              "MEDICINEZZZ",
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                letterSpacing: 4,
                fontSize: 28,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              "Your Smart Medication Companion",
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 48),
            const CircularProgressIndicator(strokeWidth: 3),
          ],
        ),
      ),
    );
  }
}
