import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'step2_screen.dart';

class Step1Screen extends StatefulWidget {
  const Step1Screen({super.key});

  @override
  State<Step1Screen> createState() => _Step1ScreenState();
}

class _Step1ScreenState extends State<Step1Screen> {
  final _nameCtrl = TextEditingController();
  String _error = '';

  Future<void> _next() async {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) {
      setState(() => _error = 'Please enter your name.');
      return;
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('setup_user_name', name);
    if (!mounted) return;
    Navigator.pushReplacement(
      context, MaterialPageRoute(builder: (_) => const Step2Screen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 40),
              const Text('Step 1 of 5',
                style: TextStyle(color: Color(0xFF666688), fontSize: 14)),
              const SizedBox(height: 8),
              const Text("What's your name?",
                style: TextStyle(color: Color(0xFF7B6CF6), fontSize: 26,
                  fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              const Text('NOVA will use this to greet you.',
                style: TextStyle(color: Color(0xFF666688), fontSize: 14)),
              const SizedBox(height: 32),
              TextField(
                controller: _nameCtrl,
                autofocus: true,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  hintText: 'Your name',
                  labelText: 'Name',
                  labelStyle: TextStyle(color: Color(0xFF7B6CF6)),
                ),
                onSubmitted: (_) => _next(),
              ),
              if (_error.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(_error,
                  style: const TextStyle(color: Color(0xFFFF4444), fontSize: 13)),
              ],
              const Spacer(),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _next,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF7B6CF6),
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10)),
                  ),
                  child: const Text('Next →',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
