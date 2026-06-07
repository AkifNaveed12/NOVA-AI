import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'screens/connect_screen.dart';
import 'screens/setup/step1_screen.dart';
import 'screens/home/main_screen.dart';

import 'widgets/nova_logo.dart';

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
          primary: const Color(0xFF7B6CF6),
          surface: const Color(0xFF0E0B1F),
          background: const Color(0xFF0E0B1F),
        ),
        scaffoldBackgroundColor: const Color(0xFF0E0B1F),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0E0B1F),
          foregroundColor: Color(0xFF7B6CF6),
          elevation: 0,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF1B163B),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(color: Color(0xFF3D35A8)),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(color: Color(0xFF3D35A8)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(color: Color(0xFF7B6CF6)),
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
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const NovaLogo(size: 180),
            const SizedBox(height: 32),
            const Text('NOVA', style: TextStyle(
              color: Color(0xFFA89AF8), fontSize: 32, fontWeight: FontWeight.bold,
              letterSpacing: 8)),
            const SizedBox(height: 8),
            Text('NEURAL ORCHESTRATED VOICE ASSISTANT', style: TextStyle(
              color: const Color(0xFF7B6CF6).withOpacity(0.7), fontSize: 10,
              letterSpacing: 2)),
          ],
        ),
      ),
    );
  }
}
