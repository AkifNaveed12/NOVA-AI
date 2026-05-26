import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../api/client.dart';

class TrackpadTab extends StatefulWidget {
  const TrackpadTab({super.key});

  @override
  State<TrackpadTab> createState() => _TrackpadTabState();
}

class _TrackpadTabState extends State<TrackpadTab> {
  WebSocketChannel? _channel;
  bool _connecting = true;
  String _error = '';
  double _sensitivity = 1.5;
  String _serverIp = '';

  @override
  void initState() {
    super.initState();
    _connectWs();
  }

  Future<void> _connectWs() async {
    setState(() {
      _connecting = true;
      _error = '';
    });
    try {
      final config = await getServerConfig();
      _serverIp = config['ip'] ?? '';
      if (_serverIp.isEmpty) {
        setState(() {
          _error = 'No Server IP configured. Please configure in Settings.';
          _connecting = false;
        });
        return;
      }
      final wsUrl = Uri.parse('ws://$_serverIp:8000/ws/mouse');
      _channel = WebSocketChannel.connect(wsUrl);
      
      // Wait to verify it doesn't fail immediately
      await Future.delayed(const Duration(milliseconds: 500));
      if (!mounted) return;
      setState(() {
        _connecting = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Failed to connect: $e';
        _connecting = false;
      });
    }
  }

  void _send(Map<String, dynamic> data) {
    if (_channel != null) {
      try {
        _channel!.sink.add(jsonEncode(data));
      } catch (_) {
        // Try reconnecting silently or display reconnect UI
      }
    }
  }

  @override
  void dispose() {
    _channel?.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_connecting) {
      return const Scaffold(
        backgroundColor: Color(0xFF080812),
        body: Center(
          child: CircularProgressIndicator(color: Color(0xFF7B6CF6)),
        ),
      );
    }

    if (_error.isNotEmpty) {
      return Scaffold(
        backgroundColor: const Color(0xFF080812),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.link_off, color: Color(0xFFAA2222), size: 48),
                const SizedBox(height: 16),
                Text(
                  _error,
                  style: const TextStyle(color: Color(0xFF888899), fontSize: 13),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: _connectWs,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF7B6CF6),
                    foregroundColor: Colors.black,
                  ),
                  child: const Text('Reconnect'),
                )
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFF080812),
      body: SafeArea(
        child: Column(
          children: [
            // Settings header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              color: const Color(0xFF0D0D1E),
              child: Row(
                children: [
                  const Icon(Icons.mouse, color: Color(0xFF7B6CF6), size: 18),
                  const SizedBox(width: 8),
                  const Text(
                    'Mouse Trackpad',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Spacer(),
                  const Text(
                    'Sensitivity: ',
                    style: TextStyle(color: Color(0xFF444466), fontSize: 11),
                  ),
                  Expanded(
                    child: Slider(
                      value: _sensitivity,
                      min: 0.5,
                      max: 4.0,
                      activeColor: const Color(0xFF7B6CF6),
                      inactiveColor: const Color(0xFF1B163B),
                      onChanged: (val) {
                        setState(() {
                          _sensitivity = val;
                        });
                      },
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.sync, color: Color(0xFF555577), size: 18),
                    onPressed: _connectWs,
                    tooltip: 'Reconnect socket',
                  ),
                ],
              ),
            ),

            // Trackpad Body
            Expanded(
              child: Row(
                children: [
                  // Left side touchpad panel
                  Expanded(
                    child: GestureDetector(
                      onPanUpdate: (details) {
                        _send({
                          "type": "move",
                          "dx": details.delta.dx * _sensitivity,
                          "dy": details.delta.dy * _sensitivity,
                        });
                      },
                      onTap: () => _send({"type": "click", "button": "left"}),
                      onDoubleTap: () => _send({"type": "click", "button": "double"}),
                      onLongPress: () => _send({"type": "click", "button": "right"}),
                      child: Container(
                        margin: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F0F26),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFF1B163B), width: 2),
                          boxShadow: const [
                            BoxShadow(
                              color: Color(0x107B6CF6),
                              blurRadius: 10,
                              spreadRadius: 2,
                            ),
                          ],
                        ),
                        child: const Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.touch_app, color: Color(0xFF7B6CF6), size: 40),
                              SizedBox(height: 16),
                              Text(
                                'Slide to Move Cursor',
                                style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500),
                              ),
                              SizedBox(height: 8),
                              Text(
                                'Tap = Left Click\nDouble Tap = Double Click\nLong Press = Right Click',
                                textAlign: TextAlign.center,
                                style: TextStyle(color: Color(0xFF444466), fontSize: 11),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),

                  // Right side scroll wheel strip
                  Container(
                    width: 60,
                    margin: const EdgeInsets.only(top: 12, bottom: 12, right: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0F0F26),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFF1B163B), width: 2),
                    ),
                    child: GestureDetector(
                      onVerticalDragUpdate: (details) {
                        // Normalize scrolling sensitivity
                        int amount = -(details.delta.dy * 1.5).toInt();
                        if (amount != 0) {
                          _send({
                            "type": "scroll",
                            "amount": amount,
                          });
                        }
                      },
                      child: const Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.arrow_upward, color: Color(0xFF7B6CF6), size: 16),
                          SizedBox(height: 16),
                          Icon(Icons.unfold_more, color: Color(0xFF444466), size: 20),
                          SizedBox(height: 16),
                          Icon(Icons.arrow_downward, color: Color(0xFF7B6CF6), size: 16),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
