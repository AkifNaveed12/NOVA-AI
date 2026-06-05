import 'package:flutter/material.dart';
import '../../api/client.dart';
import '../home/main_screen.dart';

class Step6Screen extends StatefulWidget {
  final String userName;
  const Step6Screen({super.key, required this.userName});

  @override
  State<Step6Screen> createState() => _Step6ScreenState();
}

class _Step6ScreenState extends State<Step6Screen> {
  bool _registering = false;
  String _message = '';
  String _error = '';
  bool _registered = false;

  Future<void> _registerFace() async {
    setState(() {
      _registering = true;
      _error = '';
      _message = 'Initializing camera. Please look at your computer\'s webcam...';
    });

    try {
      final res = await registerFaceWebcam(widget.userName);
      if (!mounted) return;

      if (res['success'] == true) {
        setState(() {
          _registered = true;
          _registering = false;
          _message = 'Face registered successfully!';
        });
        // Auto navigate after a brief delay
        await Future.delayed(const Duration(milliseconds: 1500));
        await _finish();
      } else {
        setState(() {
          _error = res['error'] ?? 'Registration failed. Ensure webcam is connected and look directly at it.';
          _registering = false;
          _message = '';
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Connection error: $e';
        _registering = false;
        _message = '';
      });
    }
  }

  Future<void> _finish() async {
    await markSetupComplete();
    if (!mounted) return;
    Navigator.pushReplacement(
      context, MaterialPageRoute(builder: (_) => const MainScreen()));
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
              const Text('Step 6 of 6',
                style: TextStyle(color: Color(0xFF666688), fontSize: 14)),
              const SizedBox(height: 8),
              const Text('Face Recognition',
                style: TextStyle(color: Color(0xFF7B6CF6), fontSize: 26,
                  fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text('Register your face to log in automatically next time, ${widget.userName}.',
                style: const TextStyle(color: Color(0xFF666688), fontSize: 14)),
              const SizedBox(height: 48),

              // Visual center state
              Expanded(
                child: Center(
                  child: _registered
                      ? const Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.check_circle_outline, color: Color(0xFF00FF88), size: 72),
                            SizedBox(height: 16),
                            Text('Face Profile Created!',
                              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                          ],
                        )
                      : _registering
                          ? Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const SizedBox(
                                  width: 60, height: 60,
                                  child: CircularProgressIndicator(color: Color(0xFF7B6CF6), strokeWidth: 3),
                                ),
                                const SizedBox(height: 24),
                                Text(_message,
                                  textAlign: TextAlign.center,
                                  style: const TextStyle(color: Color(0xFFCCCCDD), fontSize: 14)),
                              ],
                            )
                          : Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.face_retouching_natural, color: Color(0xFF555577), size: 80),
                                if (_error.isNotEmpty) ...[
                                  const SizedBox(height: 24),
                                  Container(
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF330000),
                                      borderRadius: BorderRadius.circular(8),
                                      border: Border.all(color: const Color(0xFFFF4444)),
                                    ),
                                    child: Text(_error,
                                      textAlign: TextAlign.center,
                                      style: const TextStyle(color: Color(0xFFFF4444), fontSize: 12)),
                                  ),
                                ],
                              ],
                            ),
                ),
              ),

              const SizedBox(height: 24),

              // Buttons
              if (!_registered && !_registering) ...[
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _registerFace,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF7B6CF6),
                      foregroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10)),
                    ),
                    child: const Text('Start Face Scan',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: TextButton(
                    onPressed: _finish,
                    style: TextButton.styleFrom(
                      foregroundColor: const Color(0xFF666688),
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    child: const Text('Skip for now',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
