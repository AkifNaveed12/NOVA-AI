import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../api/client.dart';
import 'home/main_screen.dart';

class FaceLoginScreen extends StatefulWidget {
  const FaceLoginScreen({super.key});

  @override
  State<FaceLoginScreen> createState() => _FaceLoginScreenState();
}

class _FaceLoginScreenState extends State<FaceLoginScreen> with SingleTickerProviderStateMixin {
  String _userName = '';
  bool _verifying = false;
  String _message = '';
  String _error = '';
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _loadUser();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _loadUser() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _userName = prefs.getString('setup_user_name') ?? 'User';
    });
    _verifyFace();
  }

  Future<void> _verifyFace() async {
    if (_verifying) return;
    setState(() {
      _verifying = true;
      _error = '';
      _message = 'Initializing face scan. Look at your PC\'s webcam...';
    });

    try {
      final res = await verifyFaceWebcam(_userName);
      if (!mounted) return;

      if (res['authenticated'] == true) {
        setState(() {
          _message = 'Identity Verified! Unlocking...';
          _verifying = false;
        });
        await Future.delayed(const Duration(milliseconds: 1200));
        if (!mounted) return;
        Navigator.pushReplacement(
          context, MaterialPageRoute(builder: (_) => const MainScreen()));
      } else {
        setState(() {
          _error = res['message'] ?? 'Face not recognized. Make sure your face is clearly visible.';
          _verifying = false;
          _message = '';
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Connection failed: $e';
        _verifying = false;
        _message = '';
      });
    }
  }

  void _bypass() {
    Navigator.pushReplacement(
      context, MaterialPageRoute(builder: (_) => const MainScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFF0E0B1F),
                Color(0xFF070510),
              ],
            ),
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const SizedBox(height: 64),
                // Premium logo / title
                const Text(
                  'NOVA AI SECURITY',
                  style: TextStyle(
                    color: Color(0xFF7B6CF6),
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 4,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Biometric Authentication',
                  style: TextStyle(
                    color: Color(0xFF555577),
                    fontSize: 12,
                    letterSpacing: 1.5,
                  ),
                ),
                const Spacer(),

                // Animated Scanner Circle
                AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, child) {
                    return Container(
                      width: 180,
                      height: 180,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: _error.isNotEmpty
                              ? const Color(0xFFFF4444)
                              : const Color(0xFF7B6CF6),
                          width: 2.0 + (_pulseController.value * 4.0),
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: (_error.isNotEmpty
                                    ? const Color(0xFFFF4444)
                                    : const Color(0xFF7B6CF6))
                                .withOpacity(0.1 + (_pulseController.value * 0.2)),
                            blurRadius: 15.0 + (_pulseController.value * 15.0),
                            spreadRadius: 2.0,
                          ),
                        ],
                      ),
                      child: Center(
                        child: Icon(
                          _error.isNotEmpty
                              ? Icons.gpp_bad_outlined
                              : _verifying
                                  ? Icons.face_unlock_outlined
                                  : Icons.lock_outline_rounded,
                          color: _error.isNotEmpty
                              ? const Color(0xFFFF4444)
                              : const Color(0xFF7B6CF6),
                          size: 72,
                        ),
                      ),
                    );
                  },
                ),

                const SizedBox(height: 48),

                // Welcome User
                Text(
                  'Welcome Back, $_userName',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),

                // Status message or error
                if (_verifying || _message.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0),
                    child: Text(
                      _message,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Color(0xFFCCCCDD), fontSize: 13),
                    ),
                  ),

                if (_error.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.all(12),
                    margin: const EdgeInsets.symmetric(horizontal: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF2E0A0A),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(0xFFFF4444).withOpacity(0.5)),
                    ),
                    child: Text(
                      _error,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Color(0xFFFF8888), fontSize: 12),
                    ),
                  ),

                const Spacer(),

                // Buttons
                if (!_verifying) ...[
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _verifyFace,
                      icon: const Icon(Icons.face, size: 20),
                      label: const Text(
                        'Scan Face to Unlock',
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF7B6CF6),
                        foregroundColor: Colors.black,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: TextButton(
                      onPressed: _bypass,
                      style: TextButton.styleFrom(
                        foregroundColor: const Color(0xFF555577),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: const Text(
                        'Skip & Open Dashboard',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
