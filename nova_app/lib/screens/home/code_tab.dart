import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../../api/client.dart';

class _Message {
  final bool isUser;
  final String content;
  const _Message({required this.isUser, required this.content});
}

class CodeTab extends StatefulWidget {
  const CodeTab({super.key});

  @override
  State<CodeTab> createState() => _CodeTabState();
}

class _CodeTabState extends State<CodeTab> {
  final _inputCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final List<_Message> _messages = [
    const _Message(isUser: false,
      content: "Hello! I'm your coding assistant. Ask me to write, debug, or explain code."),
  ];
  bool _loading = false;

  Future<void> _send() async {
    final text = _inputCtrl.text.trim();
    if (text.isEmpty || _loading) return;
    _inputCtrl.clear();
    setState(() {
      _messages.add(_Message(isUser: true, content: text));
      _loading = true;
    });
    _scrollToBottom();

    try {
      final result = await sendCodeMessage(text);
      final reply = result['reply'] as String? ?? 'No response.';
      setState(() {
        _messages.add(_Message(isUser: false, content: reply));
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _messages.add(_Message(isUser: false, content: 'Error: $e'));
        _loading = false;
      });
    }
    _scrollToBottom();
  }

  Future<void> _clearHistory() async {
    try {
      await resetCodeConversation();
    } catch (_) {}
    setState(() {
      _messages.clear();
      _messages.add(const _Message(isUser: false,
        content: 'Conversation cleared. Ask me anything about code.'));
    });
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
    _inputCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          // Header with clear button
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 8, 8),
            child: Row(
              children: [
                const Icon(Icons.code, color: Color(0xFF00D4FF), size: 20),
                const SizedBox(width: 8),
                const Text('Coding Assistant',
                  style: TextStyle(color: Color(0xFF00D4FF), fontSize: 16,
                    fontWeight: FontWeight.bold)),
                const Spacer(),
                TextButton.icon(
                  onPressed: _clearHistory,
                  icon: const Icon(Icons.delete_outline, size: 18),
                  label: const Text('Clear'),
                  style: TextButton.styleFrom(
                    foregroundColor: const Color(0xFF666688)),
                ),
              ],
            ),
          ),

          // Message list
          Expanded(
            child: ListView.builder(
              controller: _scrollCtrl,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _messages.length,
              itemBuilder: (_, i) {
                final msg = _messages[i];
                if (msg.isUser) {
                  return Align(
                    alignment: Alignment.centerRight,
                    child: Container(
                      margin: const EdgeInsets.symmetric(vertical: 4),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14, vertical: 10),
                      constraints: BoxConstraints(
                        maxWidth: MediaQuery.of(context).size.width * 0.8),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00D4FF22),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFF00D4FF44)),
                      ),
                      child: Text(msg.content,
                        style: const TextStyle(
                          color: Color(0xFF00D4FF), fontSize: 14)),
                    ),
                  );
                }
                // NOVA response — render as Markdown
                return Container(
                  margin: const EdgeInsets.symmetric(vertical: 4),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF111122),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF222244)),
                  ),
                  child: MarkdownBody(
                    data: msg.content,
                    styleSheet: MarkdownStyleSheet(
                      p: const TextStyle(color: Colors.white, fontSize: 14),
                      code: const TextStyle(
                        fontFamily: 'monospace',
                        color: Color(0xFF00FF88),
                        fontSize: 13,
                      ),
                      codeblockDecoration: BoxDecoration(
                        color: const Color(0xFF0A0A0A),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFF333344)),
                      ),
                      h1: const TextStyle(color: Color(0xFF00D4FF),
                        fontWeight: FontWeight.bold, fontSize: 18),
                      h2: const TextStyle(color: Color(0xFF00D4FF),
                        fontWeight: FontWeight.bold, fontSize: 16),
                      h3: const TextStyle(color: Color(0xFF00AACC),
                        fontWeight: FontWeight.bold, fontSize: 14),
                      listBullet: const TextStyle(color: Color(0xFF00D4FF)),
                      strong: const TextStyle(
                        color: Colors.white, fontWeight: FontWeight.bold),
                      em: const TextStyle(
                        color: Color(0xFFCCCCFF), fontStyle: FontStyle.italic),
                      blockquote: const TextStyle(color: Color(0xFF888899)),
                    ),
                  ),
                );
              },
            ),
          ),

          // Typing indicator
          if (_loading)
            const Padding(
              padding: EdgeInsets.only(left: 16, bottom: 4),
              child: Row(
                children: [
                  SizedBox(height: 16, width: 16,
                    child: CircularProgressIndicator(
                      color: Color(0xFF00D4FF), strokeWidth: 2)),
                  SizedBox(width: 10),
                  Text('NOVA is thinking...',
                    style: TextStyle(color: Color(0xFF666688), fontSize: 13)),
                ],
              ),
            ),

          // Input row
          Container(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            color: const Color(0xFF0A0A1A),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _inputCtrl,
                    minLines: 1,
                    maxLines: 4,
                    onSubmitted: (_) => _send(),
                    decoration: const InputDecoration(
                      hintText: 'Ask about code...',
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 16, vertical: 12),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: _loading ? null : _send,
                  child: Container(
                    width: 44, height: 44,
                    decoration: BoxDecoration(
                      color: _loading
                        ? const Color(0xFF333355)
                        : const Color(0xFF00D4FF),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: _loading
                      ? const Padding(
                          padding: EdgeInsets.all(12),
                          child: CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2))
                      : const Icon(Icons.send_rounded,
                          color: Colors.black, size: 20),
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
