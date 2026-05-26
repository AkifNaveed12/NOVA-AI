import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'step3_screen.dart';

class Step2Screen extends StatefulWidget {
  const Step2Screen({super.key});

  @override
  State<Step2Screen> createState() => _Step2ScreenState();
}

class _Step2ScreenState extends State<Step2Screen> {
  final _keyCtrl = TextEditingController();
  bool _obscure = true;
  bool _showGuide = false;
  String _error = '';

  void _next() async {
    final key = _keyCtrl.text.trim();
    if (key.isEmpty || key.length < 10) {
      setState(() => _error = 'Please enter a valid Groq API key (starts with gsk_).');
      return;
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('setup_groq_key', key);
    if (!mounted) return;
    Navigator.pushReplacement(
      context, MaterialPageRoute(builder: (_) => const Step3Screen()));
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
              const Text('Step 2 of 5',
                style: TextStyle(color: Color(0xFF666688), fontSize: 14)),
              const SizedBox(height: 6),
              const Text('Groq API Key',
                style: TextStyle(color: Color(0xFF7B6CF6), fontSize: 26,
                  fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              const Text(
                'NOVA uses Groq\'s free AI to answer your questions. '
                'Your key stays on your PC — never sent anywhere else.',
                style: TextStyle(color: Color(0xFF888899), fontSize: 13)),

              const SizedBox(height: 20),

              // How-to guide toggle
              GestureDetector(
                onTap: () => setState(() => _showGuide = !_showGuide),
                child: Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1117),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0x447B6CF6)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.help_outline,
                        color: Color(0xFF7B6CF6), size: 18),
                      const SizedBox(width: 10),
                      const Expanded(
                        child: Text('How to get your free Groq API key?',
                          style: TextStyle(color: Color(0xFF7B6CF6),
                            fontSize: 13, fontWeight: FontWeight.w500))),
                      Icon(
                        _showGuide
                          ? Icons.keyboard_arrow_up
                          : Icons.keyboard_arrow_down,
                        color: const Color(0xFF7B6CF6), size: 20),
                    ],
                  ),
                ),
              ),

              if (_showGuide) ...[
                const SizedBox(height: 2),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF080D14),
                    borderRadius: const BorderRadius.only(
                      bottomLeft: Radius.circular(10),
                      bottomRight: Radius.circular(10)),
                    border: Border.all(color: const Color(0x337B6CF6)),
                  ),
                  child: const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _GuideStep(
                        number: '1',
                        text: 'Open a browser and go to:\nconsole.groq.com'),
                      _GuideStep(
                        number: '2',
                        text: 'Sign up for a free account\n(Google sign-in works)'),
                      _GuideStep(
                        number: '3',
                        text: 'Click "API Keys" in the left sidebar'),
                      _GuideStep(
                        number: '4',
                        text: 'Click "Create API Key" → give it any name'),
                      _GuideStep(
                        number: '5',
                        text: 'Copy the key (starts with gsk_)\nand paste it below'),
                      SizedBox(height: 4),
                      Text('Free tier: 14,400 requests/day — more than enough.',
                        style: TextStyle(color: Color(0xFF555577),
                          fontSize: 11, fontStyle: FontStyle.italic)),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 20),

              TextField(
                controller: _keyCtrl,
                obscureText: _obscure,
                decoration: InputDecoration(
                  hintText: 'gsk_...',
                  labelText: 'Groq API Key',
                  labelStyle: const TextStyle(color: Color(0xFF7B6CF6)),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                      color: const Color(0xFF666688)),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                ),
              ),

              if (_error.isNotEmpty) ...[
                const SizedBox(height: 10),
                Text(_error,
                  style: const TextStyle(color: Color(0xFFFF4444), fontSize: 13)),
              ],

              const SizedBox(height: 32),

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
              color: Color(0x227B6CF6),
              shape: BoxShape.circle,
              border: Border.fromBorderSide(
                BorderSide(color: Color(0xFF7B6CF666))),
            ),
            child: Text(number,
              style: const TextStyle(
                color: Color(0xFF7B6CF6), fontSize: 11,
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
