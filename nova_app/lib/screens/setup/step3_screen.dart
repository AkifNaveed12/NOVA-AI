import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'step4_screen.dart';

class Step3Screen extends StatefulWidget {
  const Step3Screen({super.key});

  @override
  State<Step3Screen> createState() => _Step3ScreenState();
}

class _Step3ScreenState extends State<Step3Screen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _obscure = true;
  bool _showGuide = false;

  Future<void> _next({bool skip = false}) async {
    final prefs = await SharedPreferences.getInstance();
    if (!skip) {
      await prefs.setString('setup_email', _emailCtrl.text.trim());
      await prefs.setString('setup_email_pass', _passCtrl.text.trim());
    }
    if (!mounted) return;
    Navigator.pushReplacement(
      context, MaterialPageRoute(builder: (_) => const Step4Screen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 32),
              const Text('Step 3 of 5',
                style: TextStyle(color: Color(0xFF666688), fontSize: 14)),
              const SizedBox(height: 6),
              Row(
                children: [
                  const Text('Email',
                    style: TextStyle(color: Color(0xFF00D4FF), fontSize: 26,
                      fontWeight: FontWeight.bold)),
                  const SizedBox(width: 10),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: const Color(0xFF333355),
                      borderRadius: BorderRadius.circular(6)),
                    child: const Text('Optional',
                      style: TextStyle(color: Color(0xFF888899), fontSize: 11))),
                ],
              ),
              const SizedBox(height: 6),
              const Text(
                'Enables voice commands like "check my emails" and "send an email".\n'
                'You can skip this now and set it up later.',
                style: TextStyle(color: Color(0xFF888899), fontSize: 13)),

              const SizedBox(height: 20),

              // What is an App Password guide
              GestureDetector(
                onTap: () => setState(() => _showGuide = !_showGuide),
                child: Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1117),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFFFAA0044)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline,
                        color: Color(0xFFFFAA00), size: 18),
                      const SizedBox(width: 10),
                      const Expanded(
                        child: Text(
                          'What is an App Password and how do I get one?',
                          style: TextStyle(color: Color(0xFFFFAA00),
                            fontSize: 13, fontWeight: FontWeight.w500))),
                      Icon(
                        _showGuide
                          ? Icons.keyboard_arrow_up
                          : Icons.keyboard_arrow_down,
                        color: const Color(0xFFFFAA00), size: 20),
                    ],
                  ),
                ),
              ),

              if (_showGuide) ...[
                const SizedBox(height: 2),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0A0A0A),
                    borderRadius: const BorderRadius.only(
                      bottomLeft: Radius.circular(10),
                      bottomRight: Radius.circular(10)),
                    border: Border.all(color: const Color(0xFFFFAA0033)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('What is it?',
                        style: TextStyle(color: Colors.white,
                          fontWeight: FontWeight.bold, fontSize: 13)),
                      const SizedBox(height: 6),
                      const Text(
                        'An App Password is a special 16-character code Google '
                        'generates for apps like NOVA. It is NOT your Gmail password '
                        '— it only works for this one app, and you can delete it anytime.',
                        style: TextStyle(color: Color(0xFFCCCCDD),
                          fontSize: 12, height: 1.5)),
                      const SizedBox(height: 16),
                      const Text('How to get it (takes 2 minutes):',
                        style: TextStyle(color: Colors.white,
                          fontWeight: FontWeight.bold, fontSize: 13)),
                      const SizedBox(height: 10),
                      const _GuideStep(
                        number: '1',
                        text: 'Go to: myaccount.google.com\non your phone or PC'),
                      const _GuideStep(
                        number: '2',
                        text: 'Tap "Security" in the left menu'),
                      const _GuideStep(
                        number: '3',
                        text: 'Make sure "2-Step Verification" is turned ON\n'
                              '(required — App Passwords only work with 2FA enabled)'),
                      const _GuideStep(
                        number: '4',
                        text: 'In the search bar at the top, search:\n"App Passwords"'),
                      const _GuideStep(
                        number: '5',
                        text: 'Tap it → Type any name (e.g. "NOVA AI") → tap "Create"'),
                      const _GuideStep(
                        number: '6',
                        text: 'Google shows a 16-character password\n'
                              'Copy it and paste it below (spaces are fine)'),
                      Container(
                        margin: const EdgeInsets.only(top: 4),
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1A1A00),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: const Color(0xFFFFAA0033)),
                        ),
                        child: const Text(
                          '⚠  You see the App Password only once.\n'
                          'Copy it immediately before closing that window.',
                          style: TextStyle(color: Color(0xFFFFAA00),
                            fontSize: 12, height: 1.5)),
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 20),

              TextField(
                controller: _emailCtrl,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(
                  hintText: 'you@gmail.com',
                  labelText: 'Gmail Address',
                  labelStyle: TextStyle(color: Color(0xFF00D4FF)),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _passCtrl,
                obscureText: _obscure,
                decoration: InputDecoration(
                  hintText: 'xxxx xxxx xxxx xxxx',
                  labelText: 'App Password (16 characters)',
                  labelStyle: const TextStyle(color: Color(0xFF00D4FF)),
                  helperText: 'This is NOT your Gmail password — see guide above',
                  helperStyle: const TextStyle(color: Color(0xFF666688), fontSize: 11),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                      color: const Color(0xFF666688)),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                ),
              ),

              const SizedBox(height: 32),

              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => _next(skip: true),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFF666688),
                        side: const BorderSide(color: Color(0xFF333355)),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10)),
                      ),
                      child: const Text('Skip for now'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      onPressed: () => _next(),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00D4FF),
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
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}

class _GuideStep extends StatelessWidget {
  final String number;
  final String text;
  const _GuideStep({required this.number, required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 22, height: 22,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: Color(0xFFFFAA0022),
              shape: BoxShape.circle,
              border: Border.fromBorderSide(
                BorderSide(color: Color(0xFFFFAA0066))),
            ),
            child: Text(number,
              style: const TextStyle(
                color: Color(0xFFFFAA00), fontSize: 11,
                fontWeight: FontWeight.bold)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(text,
              style: const TextStyle(
                color: Color(0xFFCCCCDD), fontSize: 13, height: 1.5)),
          ),
        ],
      ),
    );
  }
}
