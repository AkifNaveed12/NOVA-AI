import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'step5_screen.dart';

class Step4Screen extends StatefulWidget {
  const Step4Screen({super.key});

  @override
  State<Step4Screen> createState() => _Step4ScreenState();
}

class _Step4ScreenState extends State<Step4Screen> {
  final List<Map<String, String>> _contacts = [];
  final _nameCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  bool _showGuide = false;
  String _addError = '';

  void _addContact() {
    final name = _nameCtrl.text.trim();
    final phone = _phoneCtrl.text.trim();

    if (name.isEmpty) {
      setState(() => _addError = 'Enter a name.');
      return;
    }
    if (phone.isEmpty || !phone.startsWith('+')) {
      setState(() => _addError = 'Phone must start with country code, e.g. +923001234567');
      return;
    }

    setState(() {
      _contacts.add({'name': name, 'phone': phone});
      _nameCtrl.clear();
      _phoneCtrl.clear();
      _addError = '';
    });
  }

  void _removeContact(int index) {
    setState(() => _contacts.removeAt(index));
  }

  Future<void> _next({bool skip = false}) async {
    final prefs = await SharedPreferences.getInstance();
    if (!skip && _contacts.isNotEmpty) {
      await prefs.setString('setup_contacts', jsonEncode(_contacts));
    }
    if (!mounted) return;
    Navigator.pushReplacement(
      context, MaterialPageRoute(builder: (_) => const Step5Screen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 32),
              const Text('Step 4 of 5',
                style: TextStyle(color: Color(0xFF666688), fontSize: 14)),
              const SizedBox(height: 6),
              Row(
                children: [
                  const Text('WhatsApp Contacts',
                    style: TextStyle(color: Color(0xFF00D4FF), fontSize: 22,
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
                'Add people you message often. NOVA will recognise them by name — '
                '"text Mama", "send a message to Hamza".',
                style: TextStyle(color: Color(0xFF888899), fontSize: 13)),

              const SizedBox(height: 16),

              // Guide toggle
              GestureDetector(
                onTap: () => setState(() => _showGuide = !_showGuide),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1117),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF25D36644)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.phone_outlined,
                        color: Color(0xFF25D366), size: 16),
                      const SizedBox(width: 8),
                      const Expanded(
                        child: Text('How to find someone\'s phone number with country code?',
                          style: TextStyle(color: Color(0xFF25D366),
                            fontSize: 12, fontWeight: FontWeight.w500))),
                      Icon(
                        _showGuide
                          ? Icons.keyboard_arrow_up
                          : Icons.keyboard_arrow_down,
                        color: const Color(0xFF25D366), size: 18),
                    ],
                  ),
                ),
              ),

              if (_showGuide) ...[
                const SizedBox(height: 2),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFF080D0A),
                    borderRadius: const BorderRadius.only(
                      bottomLeft: Radius.circular(10),
                      bottomRight: Radius.circular(10)),
                    border: Border.all(color: const Color(0xFF25D36633)),
                  ),
                  child: const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Country code examples:',
                        style: TextStyle(color: Colors.white,
                          fontWeight: FontWeight.bold, fontSize: 12)),
                      SizedBox(height: 8),
                      _PhoneExample(flag: '🇵🇰', country: 'Pakistan', example: '+923001234567'),
                      _PhoneExample(flag: '🇺🇸', country: 'USA', example: '+12025551234'),
                      _PhoneExample(flag: '🇬🇧', country: 'UK', example: '+447911123456'),
                      _PhoneExample(flag: '🇸🇦', country: 'Saudi Arabia', example: '+966501234567'),
                      _PhoneExample(flag: '🇦🇪', country: 'UAE', example: '+971501234567'),
                      SizedBox(height: 10),
                      Text(
                        'Formula: + country_code + number (no leading 0)\n'
                        'e.g. 0300-1234567 (PK) → +923001234567',
                        style: TextStyle(color: Color(0xFF666688),
                          fontSize: 11, fontStyle: FontStyle.italic)),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 14),

              // Add contact row
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: TextField(
                      controller: _nameCtrl,
                      textCapitalization: TextCapitalization.words,
                      decoration: const InputDecoration(
                        hintText: 'Mama',
                        labelText: 'Name',
                        labelStyle: TextStyle(color: Color(0xFF00D4FF)),
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 12, vertical: 12),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _phoneCtrl,
                      keyboardType: TextInputType.phone,
                      decoration: const InputDecoration(
                        hintText: '+923001234567',
                        labelText: 'Phone',
                        labelStyle: TextStyle(color: Color(0xFF00D4FF)),
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 12, vertical: 12),
                      ),
                    ),
                  ),
                  const SizedBox(width: 6),
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: IconButton(
                      onPressed: _addContact,
                      icon: const Icon(Icons.add_circle_outline,
                        color: Color(0xFF00D4FF), size: 28)),
                  ),
                ],
              ),

              if (_addError.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(_addError,
                  style: const TextStyle(color: Color(0xFFFF4444), fontSize: 12)),
              ],

              const SizedBox(height: 8),

              // Contacts list
              Expanded(
                child: _contacts.isEmpty
                  ? const Center(
                      child: Text('No contacts added yet.\nYou can add them after setup too.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Color(0xFF444466), fontSize: 13)))
                  : ListView.builder(
                      itemCount: _contacts.length,
                      itemBuilder: (_, i) => Container(
                        margin: const EdgeInsets.only(bottom: 6),
                        decoration: BoxDecoration(
                          color: const Color(0xFF111122),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: const Color(0xFF222244)),
                        ),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: const Color(0xFF00D4FF22),
                            child: Text(_contacts[i]['name']![0].toUpperCase(),
                              style: const TextStyle(color: Color(0xFF00D4FF),
                                fontWeight: FontWeight.bold)),
                          ),
                          title: Text(_contacts[i]['name']!,
                            style: const TextStyle(color: Colors.white)),
                          subtitle: Text(_contacts[i]['phone']!,
                            style: const TextStyle(
                              color: Color(0xFF666688), fontSize: 12)),
                          trailing: IconButton(
                            icon: const Icon(Icons.remove_circle_outline,
                              color: Color(0xFFFF4444)),
                            onPressed: () => _removeContact(i)),
                        ),
                      ),
                    ),
              ),

              // Bottom buttons
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
                      child: Text(
                        _contacts.isEmpty ? 'Skip →' : 'Next →',
                        style: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }
}

class _PhoneExample extends StatelessWidget {
  final String flag;
  final String country;
  final String example;
  const _PhoneExample({required this.flag, required this.country, required this.example});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          Text(flag, style: const TextStyle(fontSize: 16)),
          const SizedBox(width: 8),
          SizedBox(width: 90,
            child: Text(country,
              style: const TextStyle(color: Color(0xFF888899), fontSize: 12))),
          Text(example,
            style: const TextStyle(color: Color(0xFF25D366),
              fontFamily: 'monospace', fontSize: 12)),
        ],
      ),
    );
  }
}
