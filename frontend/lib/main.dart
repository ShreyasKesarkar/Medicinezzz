import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'core/theme/app_theme.dart';
import 'core/constants/api_constants.dart';
import 'features/notifications/notification_service.dart';
import 'features/auth/splash_screen.dart';
import 'features/auth/login_screen.dart';
import 'features/auth/register_screen.dart';
import 'features/auth/forgot_password_screen.dart';
import 'features/home/home_screen.dart';
import 'features/medicines/medicine_details_screen.dart';
import 'features/medicines/create_medicine_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Supabase Auth client
  await Supabase.initialize(
    url: ApiConstants.supabaseUrl,
    anonKey: ApiConstants.supabaseAnonKey,
  );
  
  // Initialize Local Notifications plugin
  await NotificationService.init();
  
  runApp(
    const ProviderScope(
      child: MedicinezzzApp(),
    ),
  );
}

class MedicinezzzApp extends StatelessWidget {
  const MedicinezzzApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Medicinezzz',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.dark, // Default to sleek premium dark mode
      initialRoute: '/',
      routes: {
        '/': (context) => const SplashScreen(),
        '/login': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/forgot-password': (context) => const ForgotPasswordScreen(),
        '/home': (context) => const HomeScreen(),
        '/create-medicine': (context) => const CreateMedicineScreen(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/medicine-details') {
          final medicineId = settings.arguments as String;
          return MaterialPageRoute(
            builder: (context) => MedicineDetailsScreen(medicineId: medicineId),
          );
        }
        return null;
      },
    );
  }
}
