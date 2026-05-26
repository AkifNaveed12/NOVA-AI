import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'screens/connect_screen.dart';
import 'screens/setup/step1_screen.dart';
import 'screens/home/main_screen.dart';

void main() {
  runApp(const NovaApp());
}

class NovaApp extends StatelessWidget {
  const NovaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NOVA AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        colorScheme: ColorScheme.dark(
          primary: const Color(0xFF00D4FF),
          surface: const Color(0xFF0A0A1A),
          background: const Color(0xFF0A0A1A),
        ),
        scaffoldBackgroundColor: const Color(0xFF0A0A1A),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0A0A1A),
          foregroundColor: Color(0xFF00D4FF),
          elevation: 0,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF111122),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(color: Color(0xFF222244)),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(color: Color(0xFF222244)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(color: Color(0xFF00D4FF)),
          ),
          hintStyle: const TextStyle(color: Color(0xFF555577)),
        ),
      ),
      home: const _Splash(),
    );
  }
}

class _Splash extends StatefulWidget {
  const _Splash();

  @override
  State<_Splash> createState() => _SplashState();
}

class _SplashState extends State<_Splash> {
  @override
  void initState() {
    super.initState();
    _route();
  }

  Future<void> _route() async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString('nova_server_ip') ?? '';
    final setupDone = prefs.getBool('nova_setup_complete') ?? false;

    if (!mounted) return;
    if (ip.isEmpty) {
      Navigator.pushReplacement(
        context, MaterialPageRoute(builder: (_) => const ConnectScreen()));
    } else if (!setupDone) {
      Navigator.pushReplacement(
        context, MaterialPageRoute(builder: (_) => const Step1Screen()));
    } else {
      Navigator.pushReplacement(
        context, MaterialPageRoute(builder: (_) => const MainScreen()));
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('NOVA AI', style: TextStyle(
              color: Color(0xFF00D4FF), fontSize: 36, fontWeight: FontWeight.bold,
              letterSpacing: 4)),
            SizedBox(height: 16),
            CircularProgressIndicator(color: Color(0xFF00D4FF)),
          ],
        ),
      ),
    );
  }
}
