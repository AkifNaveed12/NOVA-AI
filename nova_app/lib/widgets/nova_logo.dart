import 'dart:math' as math;
import 'package:flutter/material.dart';

class NovaLogo extends StatefulWidget {
  final double size;
  const NovaLogo({super.key, this.size = 200});

  @override
  State<NovaLogo> createState() => _NovaLogoState();
}

class _NovaLogoState extends State<NovaLogo> with TickerProviderStateMixin {
  late AnimationController _rotationController;
  late AnimationController _pulseController;
  late AnimationController _breatheController;

  @override
  void initState() {
    super.initState();
    _rotationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 12),
    )..repeat();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat(reverse: true);

    _breatheController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _rotationController.dispose();
    _pulseController.dispose();
    _breatheController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([
        _rotationController,
        _pulseController,
        _breatheController,
      ]),
      builder: (context, child) {
        return CustomPaint(
          size: Size(widget.size, widget.size),
          painter: _NovaLogoPainter(
            rotationAngle: _rotationController.value * 2 * math.pi,
            pulseValue: _pulseController.value,
            breatheValue: _breatheController.value,
          ),
        );
      },
    );
  }
}

class _NovaLogoPainter extends CustomPainter {
  final double rotationAngle;
  final double pulseValue;
  final double breatheValue;

  _NovaLogoPainter({
    required this.rotationAngle,
    required this.pulseValue,
    required this.breatheValue,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final double scale = size.width / 400.0;
    canvas.save();
    canvas.scale(scale, scale);

    final center = const Offset(200, 200);

    // 1. Radial Glow
    final glowRadius = 170.0;
    final glowPaint = Paint()
      ..shader = RadialGradient(
        colors: [
          const Color(0xFF7B6CF6).withOpacity(0.18 + (pulseValue * 0.14)),
          const Color(0xFF7B6CF6).withOpacity(0.0),
        ],
      ).createShader(Rect.fromCircle(center: center, radius: glowRadius));
    canvas.drawCircle(center, glowRadius, glowPaint);

    // 2. Concentric background rings
    final ringPaint1 = Paint()
      ..color = const Color(0xFF7B6CF6).withOpacity(0.2)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.8;
    canvas.drawCircle(center, 148, ringPaint1);

    final ringPaint2 = Paint()
      ..color = const Color(0xFF7B6CF6).withOpacity(0.15)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.8;
    canvas.drawCircle(center, 118, ringPaint2);

    // 3. Orbiting dots (Clockwise - Purple)
    _drawOrbitDot(canvas, center, 148, rotationAngle, 4.0, const Color(0xFF7B6CF6).withOpacity(0.9));
    _drawOrbitDot(canvas, center, 148, rotationAngle + (math.pi / 2), 2.5, const Color(0xFF7B6CF6).withOpacity(0.5));
    _drawOrbitDot(canvas, center, 148, rotationAngle + math.pi, 3.0, const Color(0xFF7B6CF6).withOpacity(0.7));

    // 4. Orbiting dots (Counter-Clockwise - Teal)
    _drawOrbitDot(canvas, center, 118, -rotationAngle * 0.75, 3.0, const Color(0xFF5DCAA5).withOpacity(0.8));
    _drawOrbitDot(canvas, center, 118, -rotationAngle * 0.75 + math.pi, 2.0, const Color(0xFF5DCAA5).withOpacity(0.5));

    // 5. Central solid background circle
    final coreBgPaint = Paint()..color = const Color(0xFF0E0B1F);
    canvas.drawCircle(center, 88, coreBgPaint);

    final coreBorderPaint = Paint()
      ..color = const Color(0xFF7B6CF6).withOpacity(0.4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    canvas.drawCircle(center, 86, coreBorderPaint);

    // 6. Sine/Waveform background line inside core
    final wavePath = Path()
      ..moveTo(120, 200)
      ..quadraticBezierTo(160, 155, 200, 200)
      ..quadraticBezierTo(240, 245, 280, 200);
    final wavePaint = Paint()
      ..color = const Color(0xFF7B6CF6).withOpacity(0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round;
    canvas.drawPath(wavePath, wavePaint);

    // 7. Central breathing symbol shapes
    final symbolOpacity = 0.85 + (breatheValue * 0.15);
    
    // Top arrow block
    final topPath = Path()
      ..moveTo(200, 138)
      ..lineTo(175, 160)
      ..lineTo(175, 195)
      ..lineTo(200, 162)
      ..lineTo(225, 195)
      ..lineTo(225, 160)
      ..close();
    
    final symbolShader = const LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: [Color(0xFFA89AF8), Color(0xFF5B4FD4)],
    ).createShader(const Rect.fromLTRB(175, 138, 225, 240));

    final topPaint = Paint()
      ..shader = symbolShader
      ..color = Colors.white.withOpacity(symbolOpacity); // applies opacity via shader tint
    canvas.drawPath(topPath, topPaint);

    // Bottom arrow block
    final bottomPath = Path()
      ..moveTo(178, 202)
      ..lineTo(162, 240)
      ..lineTo(200, 218)
      ..lineTo(238, 240)
      ..lineTo(222, 202)
      ..lineTo(200, 222)
      ..close();
    final bottomPaint = Paint()
      ..shader = symbolShader
      ..color = Colors.white.withOpacity(symbolOpacity * 0.79);
    canvas.drawPath(bottomPath, bottomPaint);

    // Center light dot
    final dotPaint = Paint()..color = const Color(0xFFC4B8FC);
    canvas.drawCircle(const Offset(200, 192), 5.0, dotPaint);

    canvas.restore();
  }

  void _drawOrbitDot(Canvas canvas, Offset center, double radius, double angle, double dotRadius, Color color) {
    final x = center.dx + radius * math.cos(angle);
    final y = center.dy + radius * math.sin(angle);
    final paint = Paint()..color = color;
    canvas.drawCircle(Offset(x, y), dotRadius, paint);
  }

  @override
  bool shouldRepaint(covariant _NovaLogoPainter oldDelegate) {
    return oldDelegate.rotationAngle != rotationAngle ||
        oldDelegate.pulseValue != pulseValue ||
        oldDelegate.breatheValue != breatheValue;
  }
}
