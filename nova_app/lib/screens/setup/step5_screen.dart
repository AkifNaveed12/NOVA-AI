import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../api/client.dart';
import '../home/main_screen.dart';

class Step5Screen extends StatefulWidget {
  const Step5Screen({super.key});

  @override
  State<Step5Screen> createState() => _Step5ScreenState();
}

class _Step5ScreenState extends State<Step5Screen> {
  final _cityCtrl = TextEditingController(text: 'Wah Cantt');
  bool _submitting = false;
  String _error = '';

  Future<void> _finish() async {
    setState(() { _submitting = true; _error = ''; });

    try {
      final prefs = await SharedPreferences.getInstance();
      final userName = prefs.getString('setup_user_name') ?? '';
      final groqKey = prefs.getString('setup_groq_key') ?? '';
      final email = prefs.getString('setup_email') ?? '';
      final emailPass = prefs.getString('setup_email_pass') ?? '';
      final contactsJson = prefs.getString('setup_contacts') ?? '[]';
      final contacts = (jsonDecode(contactsJson) as List)
          .cast<Map<String, dynamic>>()
          .map((c) => {'name': c['name'] as String, 'phone': c['phone'] as String})
          .toList();

      final result = await submitSetup(
        userName: userName,
        groqKey: groqKey,
        emailAddress: email,
        emailAppPassword: emailPass,
        defaultCity: _cityCtrl.text.trim(),
        whatsappContacts: contacts,
      );

      if (!mounted) return;

      if (result['status'] == 'success') {
        await markSetupComplete();
        // Clean up temp setup keys
        for (final k in ['setup_user_name', 'setup_groq_key', 'setup_email',
                          'setup_email_pass', 'setup_contacts']) {
          await prefs.remove(k);
        }
        Navigator.pushReplacement(
          context, MaterialPageRoute(builder: (_) => const MainScreen()));
      } else {
        setState(() {
          _error = result['message'] ?? result['reply'] ?? 'Setup failed. Check server logs.';
          _submitting = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Connection error: $e';
        _submitting = false;
      });
    }
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
              const Text('Step 5 of 5',
                style: TextStyle(color: Color(0xFF666688), fontSize: 14)),
              const SizedBox(height: 8),
              const Text('Almost Done!',
                style: TextStyle(color: Color(0xFF7B6CF6), fontSize: 26,
                  fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              const Text('Set your default city for weather forecasts.',
                style: TextStyle(color: Color(0xFF666688), fontSize: 14)),
              const SizedBox(height: 32),
              TextField(
                controller: _cityCtrl,
                decoration: const InputDecoration(
                  hintText: 'e.g. Islamabad',
                  labelText: 'Default City',
                  labelStyle: TextStyle(color: Color(0xFF7B6CF6)),
                ),
              ),
              if (_error.isNotEmpty) ...[
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF330000),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFFFF4444)),
                  ),
                  child: Text(_error,
                    style: const TextStyle(color: Color(0xFFFF4444), fontSize: 13)),
                ),
              ],
              const Spacer(),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _submitting ? null : _finish,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF7B6CF6),
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10)),
                  ),
                  child: _submitting
                    ? const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SizedBox(height: 20, width: 20,
                            child: CircularProgressIndicator(
                              color: Colors.black, strokeWidth: 2)),
                          SizedBox(width: 12),
                          Text('Setting up NOVA...',
                            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                        ])
                    : const Text('Finish Setup ✓',
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
