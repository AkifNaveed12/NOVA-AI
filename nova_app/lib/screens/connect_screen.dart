import 'package:flutter/material.dart';
import '../api/client.dart';
import '../widgets/nova_logo.dart';
import 'setup/step1_screen.dart';
import 'home/main_screen.dart';

class ConnectScreen extends StatefulWidget {
  const ConnectScreen({super.key});

  @override
  State<ConnectScreen> createState() => _ConnectScreenState();
}

class _ConnectScreenState extends State<ConnectScreen> {
  final _ipCtrl = TextEditingController();
  final _keyCtrl = TextEditingController(text: 'nova-secret-change-this');
  bool _testing = false;
  bool _showIpGuide = false;
  bool _showKeyGuide = false;
  String _error = '';

  Future<void> _handleConnect() async {
    final ip = _ipCtrl.text.trim();
    final key = _keyCtrl.text.trim();
    if (ip.isEmpty) {
      setState(() => _error = 'Enter your PC\'s IP address.');
      return;
    }
    setState(() { _testing = true; _error = ''; });

    final ok = await checkConnection(ip, key);
    if (!mounted) return;
    setState(() => _testing = false);

    if (ok) {
      await saveServerConfig(ip, key);
      final setupDone = await isSetupComplete();
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => setupDone ? const MainScreen() : const Step1Screen()));
    } else {
      setState(() => _error =
        'Could not connect to NOVA.\n\n'
        '• Make sure NOVA is running on your PC (python main.py)\n'
        '• Both devices must be on the same WiFi\n'
        '• Check the IP is correct\n'
        '• Windows Firewall may be blocking port 8000');
    }
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
              const SizedBox(height: 40),

              // Logo
              const Row(
                children: [
                  NovaLogo(size: 36),
                  SizedBox(width: 12),
                  Text('NOVA AI',
                    style: TextStyle(color: Color(0xFF7B6CF6), fontSize: 26,
                      fontWeight: FontWeight.bold, letterSpacing: 3)),
                ],
              ),
              const SizedBox(height: 6),
              const Text('Connect to your PC',
                style: TextStyle(color: Color(0xFF888899), fontSize: 14)),

              const SizedBox(height: 32),

              // ── IP Address field ──────────────────────────────────
              TextField(
                controller: _ipCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  hintText: '192.168.1.x',
                  labelText: 'PC IP Address',
                  labelStyle: TextStyle(color: Color(0xFF7B6CF6)),
                  prefixIcon: Icon(Icons.computer_outlined,
                    color: Color(0xFF444466)),
                ),
              ),
              const SizedBox(height: 6),

              // How to find IP guide
              GestureDetector(
                onTap: () => setState(() => _showIpGuide = !_showIpGuide),
                child: Row(
                  children: [
                    const Icon(Icons.help_outline,
                      color: Color(0xFF555577), size: 14),
                    const SizedBox(width: 6),
                    const Text('How do I find my PC\'s IP address?',
                      style: TextStyle(color: Color(0xFF555577),
                        fontSize: 12, decoration: TextDecoration.underline)),
                    const SizedBox(width: 4),
                    Icon(
                      _showIpGuide
                        ? Icons.keyboard_arrow_up
                        : Icons.keyboard_arrow_down,
                      color: const Color(0xFF555577), size: 14),
                  ],
                ),
              ),

              if (_showIpGuide) ...[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1117),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF333355)),
                  ),
                  child: const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('On your PC (Windows):',
                        style: TextStyle(color: Colors.white,
                          fontWeight: FontWeight.bold, fontSize: 12)),
                      SizedBox(height: 8),
                      _Step(icon: Icons.search, text:
                        'Press Win + R → type cmd → press Enter'),
                      _Step(icon: Icons.terminal, text:
                        'Type: ipconfig and press Enter'),
                      _Step(icon: Icons.info_outline, text:
                        'Look for "IPv4 Address" under your WiFi adapter\n'
                        'It looks like: 192.168.1.x or 192.168.0.x'),
                      SizedBox(height: 10),
                      Text('Or faster:',
                        style: TextStyle(color: Colors.white,
                          fontWeight: FontWeight.bold, fontSize: 12)),
                      SizedBox(height: 6),
                      _Step(icon: Icons.wifi, text:
                        'Click the WiFi icon in taskbar → right-click your network\n'
                        '→ Properties → scroll down to IPv4 address'),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 16),

              // ── API Key field ─────────────────────────────────────
              TextField(
                controller: _keyCtrl,
                decoration: const InputDecoration(
                  hintText: 'nova-secret-change-this',
                  labelText: 'API Key',
                  labelStyle: TextStyle(color: Color(0xFF7B6CF6)),
                  prefixIcon: Icon(Icons.key_outlined,
                    color: Color(0xFF444466)),
                ),
              ),
              const SizedBox(height: 6),

              // What is the API key guide
              GestureDetector(
                onTap: () => setState(() => _showKeyGuide = !_showKeyGuide),
                child: Row(
                  children: [
                    const Icon(Icons.help_outline,
                      color: Color(0xFF555577), size: 14),
                    const SizedBox(width: 6),
                    const Text('What is the API key?',
                      style: TextStyle(color: Color(0xFF555577),
                        fontSize: 12, decoration: TextDecoration.underline)),
                    const SizedBox(width: 4),
                    Icon(
                      _showKeyGuide
                        ? Icons.keyboard_arrow_up
                        : Icons.keyboard_arrow_down,
                      color: const Color(0xFF555577), size: 14),
                  ],
                ),
              ),

              if (_showKeyGuide) ...[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1117),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF333355)),
                  ),
                  child: const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'The API key is a password that makes sure only your '
                        'phone can talk to your NOVA PC. The default is:\n',
                        style: TextStyle(color: Color(0xFFCCCCDD), fontSize: 12,
                          height: 1.5)),
                      Text('nova-secret-change-this',
                        style: TextStyle(color: Color(0xFF7B6CF6),
                          fontFamily: 'monospace', fontSize: 13)),
                      SizedBox(height: 10),
                      Text(
                        'You can change it in your PC\'s .env file '
                        '(NOVA_API_SECRET=your_key) and set the same key here.',
                        style: TextStyle(color: Color(0xFF666688),
                          fontSize: 12, height: 1.5)),
                    ],
                  ),
                ),
              ],

              // Error
              if (_error.isNotEmpty) ...[
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1A0000),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFFF444444)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.error_outline,
                        color: Color(0xFFFF4444), size: 18),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(_error,
                          style: const TextStyle(color: Color(0xFFFF8888),
                            fontSize: 13, height: 1.5)),
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 32),

              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _testing ? null : _handleConnect,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF7B6CF6),
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10)),
                  ),
                  child: _testing
                    ? const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SizedBox(height: 20, width: 20,
                            child: CircularProgressIndicator(
                              color: Colors.black, strokeWidth: 2)),
                          SizedBox(width: 12),
                          Text('Testing connection...',
                            style: TextStyle(fontSize: 16,
                              fontWeight: FontWeight.bold)),
                        ])
                    : const Text('Connect →',
                        style: TextStyle(fontSize: 16,
                          fontWeight: FontWeight.bold)),
                ),
              ),

              const SizedBox(height: 24),

              // Prerequisite reminder
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFF0E0B1F),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFF3D35A8)),
                ),
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Before connecting:',
                      style: TextStyle(color: Color(0xFF888899),
                        fontSize: 12, fontWeight: FontWeight.bold)),
                    SizedBox(height: 8),
                    _Step(icon: Icons.computer, text:
                      'NOVA must be running on your PC\n(python main.py)'),
                    _Step(icon: Icons.wifi, text:
                      'Your phone and PC must be on the same WiFi network'),
                    _Step(icon: Icons.shield_outlined, text:
                      'If connection fails, allow port 8000 in Windows Firewall'),
                  ],
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

class _Step extends StatelessWidget {
  final IconData icon;
  final String text;
  const _Step({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: const Color(0xFF555577), size: 15),
          const SizedBox(width: 10),
          Expanded(
            child: Text(text,
              style: const TextStyle(color: Color(0xFFCCCCDD),
                fontSize: 12, height: 1.5)),
          ),
        ],
      ),
    );
  }
}
