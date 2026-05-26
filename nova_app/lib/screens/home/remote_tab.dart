import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../api/client.dart';

class RemoteTab extends StatefulWidget {
  const RemoteTab({super.key});

  @override
  State<RemoteTab> createState() => _RemoteTabState();
}

class _RemoteTabState extends State<RemoteTab> {
  final _cmdCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final List<Map<String, String>> _messages = [];

  String _novaStatus = 'offline';
  bool _sending = false;
  String _serverIp = '';

  WebSocketChannel? _statusWs;
  WebSocketChannel? _interactiveWs;
  bool _inInteractive = false;

  // Voice (F1)
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _speechAvailable = false;
  bool _isListening = false;

  // Screenshot viewer (F5)
  bool _screenshotLoading = false;

  static const _statusColors = {
    'sleeping':    Color(0xFF555577),
    'listening':   Color(0xFF00FF88),
    'processing':  Color(0xFFFFAA00),
    'speaking':    Color(0xFF00D4FF),
    'offline':     Color(0xFF444444),
  };

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final prefs = await SharedPreferences.getInstance();
    _serverIp = prefs.getString('nova_server_ip') ?? '';
    _connectStatusWs();
    _speechAvailable = await _speech.initialize(
      onStatus: (status) {
        if (status == 'done' || status == 'notListening') {
          if (mounted) setState(() => _isListening = false);
        }
      },
      onError: (_) {
        if (mounted) setState(() => _isListening = false);
      },
    );
    if (mounted) setState(() {});
  }

  void _connectStatusWs() {
    _statusWs?.sink.close();
    if (_serverIp.isEmpty) return;
    try {
      _statusWs = WebSocketChannel.connect(
        Uri.parse('ws://$_serverIp:8000/ws/status'));
      _statusWs!.stream.listen(
        (raw) {
          if (!mounted) return;
          final data = jsonDecode(raw as String) as Map<String, dynamic>;
          if (data['type'] == 'status') {
            setState(() => _novaStatus = data['state'] as String);
          }
        },
        onError: (_) {
          setState(() => _novaStatus = 'offline');
          Future.delayed(const Duration(seconds: 3), _connectStatusWs);
        },
        onDone: () {
          setState(() => _novaStatus = 'offline');
          Future.delayed(const Duration(seconds: 3), _connectStatusWs);
        },
      );
      setState(() => _novaStatus = 'sleeping');
    } catch (_) {
      setState(() => _novaStatus = 'offline');
    }
  }

  Future<void> _sendCommand() async {
    final text = _cmdCtrl.text.trim();
    if (text.isEmpty || _sending) return;
    _cmdCtrl.clear();
    setState(() {
      _sending = true;
      _messages.add({'role': 'user', 'text': text});
    });
    _scrollToBottom();

    try {
      final result = await sendCommand(text);

      if (result['status'] == 'interactive_required') {
        _startInteractiveFlow(text);
        return;
      }

      final response = result['response'] as String? ?? 'Done.';
      setState(() {
        _messages.add({'role': 'nova', 'text': response});
        _sending = false;
      });
    } catch (e) {
      setState(() {
        _messages.add({'role': 'nova', 'text': 'Error: $e'});
        _sending = false;
      });
    }
    _scrollToBottom();
  }

  void _startInteractiveFlow(String initialCommand) {
    setState(() => _inInteractive = true);
    try {
      _interactiveWs = WebSocketChannel.connect(
        Uri.parse('ws://$_serverIp:8000/ws/interactive'));

      // Send the initial command
      _interactiveWs!.sink.add(jsonEncode({'text': initialCommand}));

      _interactiveWs!.stream.listen(
        (raw) {
          if (!mounted) return;
          final data = jsonDecode(raw as String) as Map<String, dynamic>;
          final type = data['type'] as String;
          final text = data['text'] as String? ?? '';

          if (type == 'speak') {
            setState(() {
              _messages.add({'role': 'nova', 'text': text});
              _sending = false;
            });
            _scrollToBottom();
            // Re-enable input so user can respond
          } else if (type == 'final') {
            setState(() {
              _messages.add({'role': 'nova', 'text': text});
              _sending = false;
              _inInteractive = false;
            });
            _interactiveWs?.sink.close();
            _scrollToBottom();
          } else if (type == 'error') {
            setState(() {
              _messages.add({'role': 'nova', 'text': 'Error: $text'});
              _sending = false;
              _inInteractive = false;
            });
          }
        },
        onDone: () => setState(() { _inInteractive = false; _sending = false; }),
        onError: (e) {
          setState(() {
            _messages.add({'role': 'nova', 'text': 'Connection lost: $e'});
            _inInteractive = false;
            _sending = false;
          });
        },
      );
    } catch (e) {
      setState(() {
        _messages.add({'role': 'nova', 'text': 'Interactive flow failed: $e'});
        _sending = false;
        _inInteractive = false;
      });
    }
  }

  // Called when user replies in an interactive flow
  void _sendInteractiveReply(String text) {
    if (_interactiveWs == null) return;
    setState(() {
      _messages.add({'role': 'user', 'text': text});
      _sending = true;
    });
    _interactiveWs!.sink.add(jsonEncode({'text': text}));
    _scrollToBottom();
  }

  Future<void> _viewLastScreenshot() async {
    setState(() => _screenshotLoading = true);
    try {
      final bytes = await fetchScreenshot();
      if (!mounted) return;
      setState(() => _screenshotLoading = false);
      if (bytes == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No screenshot available yet. Try "take screenshot" first.')));
        return;
      }
      _showScreenshotFullscreen(bytes);
    } catch (_) {
      if (!mounted) return;
      setState(() => _screenshotLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not load screenshot')));
    }
  }

  void _showScreenshotFullscreen(Uint8List bytes) {
    showDialog(
      context: context,
      barrierColor: Colors.black87,
      builder: (ctx) => Dialog(
        backgroundColor: Colors.black,
        insetPadding: EdgeInsets.zero,
        child: Stack(
          children: [
            InteractiveViewer(
              maxScale: 6,
              child: SizedBox.expand(
                child: Image.memory(bytes, fit: BoxFit.contain)),
            ),
            Positioned(
              top: 48, right: 12,
              child: IconButton(
                icon: const Icon(Icons.close, color: Colors.white, size: 28),
                onPressed: () => Navigator.pop(ctx),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _toggleVoice() async {
    if (!_speechAvailable) return;
    if (_isListening) {
      await _speech.stop();
      setState(() => _isListening = false);
      return;
    }
    setState(() => _isListening = true);
    await _speech.listen(
      onResult: (result) {
        setState(() => _cmdCtrl.text = result.recognizedWords);
        if (result.finalResult && result.recognizedWords.isNotEmpty) {
          setState(() => _isListening = false);
          if (_inInteractive) {
            _sendInteractiveReply(_cmdCtrl.text.trim());
          } else {
            _sendCommand();
          }
        }
      },
      listenMode: stt.ListenMode.confirmation,
      pauseFor: const Duration(seconds: 3),
    );
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    _statusWs?.sink.close();
    _interactiveWs?.sink.close();
    _cmdCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _statusColors[_novaStatus] ?? const Color(0xFF444444);

    return SafeArea(
      child: Column(
        children: [
          // Status bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Container(width: 10, height: 10,
                  decoration: BoxDecoration(
                    color: statusColor,
                    shape: BoxShape.circle,
                    boxShadow: [BoxShadow(color: statusColor.withOpacity(0.5),
                      blurRadius: 6, spreadRadius: 2)],
                  )),
                const SizedBox(width: 10),
                Text('NOVA is $_novaStatus',
                  style: TextStyle(color: statusColor, fontSize: 14,
                    fontWeight: FontWeight.w500)),
                const Spacer(),
                // Screenshot viewer button (F5)
                _screenshotLoading
                  ? const SizedBox(width: 20, height: 20,
                      child: CircularProgressIndicator(
                        color: Color(0xFF555577), strokeWidth: 2))
                  : IconButton(
                      icon: const Icon(Icons.photo_camera_outlined,
                        color: Color(0xFF555577), size: 22),
                      onPressed: _viewLastScreenshot,
                      tooltip: 'View last screenshot',
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                    ),
              ],
            ),
          ),

          // Message history
          Expanded(
            child: ListView.builder(
              controller: _scrollCtrl,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: _messages.length,
              itemBuilder: (_, i) {
                final msg = _messages[i];
                final isUser = msg['role'] == 'user';
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    constraints: BoxConstraints(
                      maxWidth: MediaQuery.of(context).size.width * 0.75),
                    decoration: BoxDecoration(
                      color: isUser
                        ? const Color(0xFF00D4FF22)
                        : const Color(0xFF111122),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isUser
                          ? const Color(0xFF00D4FF44)
                          : const Color(0xFF222244)),
                    ),
                    child: Text(msg['text']!,
                      style: TextStyle(
                        color: isUser ? const Color(0xFF00D4FF) : Colors.white,
                        fontSize: 14)),
                  ),
                );
              },
            ),
          ),

          // Voice listening banner
          if (_isListening)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 8),
              color: const Color(0xFF1A0000),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.mic, color: Colors.red, size: 16),
                  SizedBox(width: 8),
                  Text('Listening... speak now',
                    style: TextStyle(color: Colors.red, fontSize: 13)),
                ],
              ),
            ),

          // Input row
          Container(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            color: const Color(0xFF0A0A1A),
            child: Row(
              children: [
                // Mic button
                GestureDetector(
                  onTap: _speechAvailable ? _toggleVoice : null,
                  child: Container(
                    width: 44, height: 44,
                    decoration: BoxDecoration(
                      color: _isListening
                        ? Colors.red
                        : const Color(0xFF1A1A2E),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: _isListening
                          ? Colors.red
                          : const Color(0xFF333355)),
                    ),
                    child: Icon(
                      _isListening ? Icons.stop : Icons.mic,
                      color: _isListening ? Colors.white : const Color(0xFF00D4FF),
                      size: 20),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _cmdCtrl,
                    onSubmitted: (_) => _inInteractive
                      ? _sendInteractiveReply(_cmdCtrl.text.trim())
                      : _sendCommand(),
                    decoration: InputDecoration(
                      hintText: _inInteractive
                        ? 'Reply to NOVA...'
                        : 'Type a command...',
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 12),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: _sending ? null : () {
                    final text = _cmdCtrl.text.trim();
                    if (text.isEmpty) return;
                    _cmdCtrl.clear();
                    if (_inInteractive) {
                      _sendInteractiveReply(text);
                    } else {
                      _sendCommand();
                    }
                  },
                  child: Container(
                    width: 44, height: 44,
                    decoration: BoxDecoration(
                      color: _sending
                        ? const Color(0xFF333355)
                        : const Color(0xFF00D4FF),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: _sending
                      ? const Padding(
                          padding: EdgeInsets.all(12),
                          child: CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2))
                      : const Icon(Icons.send_rounded, color: Colors.black, size: 20),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
