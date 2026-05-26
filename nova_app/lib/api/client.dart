import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

const int _kApiPort = 8000;

/// Reads stored server config from SharedPreferences.
Future<Map<String, String>> getServerConfig() async {
  final prefs = await SharedPreferences.getInstance();
  return {
    'ip': prefs.getString('nova_server_ip') ?? '',
    'apiKey': prefs.getString('nova_api_key') ?? 'nova-secret-change-this',
  };
}

/// Saves server config to SharedPreferences.
Future<void> saveServerConfig(String ip, String apiKey) async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString('nova_server_ip', ip);
  await prefs.setString('nova_api_key', apiKey);
}

/// Returns true if setup wizard has been completed.
Future<bool> isSetupComplete() async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getBool('nova_setup_complete') ?? false;
}

Future<void> markSetupComplete() async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setBool('nova_setup_complete', true);
}

String _baseUrl(String ip) => 'http://$ip:$_kApiPort';

/// Tests if NOVA is reachable at the given IP.
Future<bool> checkConnection(String ip, String apiKey) async {
  try {
    final res = await http.get(
      Uri.parse('${_baseUrl(ip)}/api/health'),
      headers: {'X-API-Key': apiKey},
    ).timeout(const Duration(seconds: 5));
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    return body['status'] == 'online';
  } catch (_) {
    return false;
  }
}

/// Sends a text command to NOVA. Returns the full response JSON.
Future<Map<String, dynamic>> sendCommand(String command) async {
  final config = await getServerConfig();
  final res = await http.post(
    Uri.parse('${_baseUrl(config['ip']!)}/api/command'),
    headers: {
      'X-API-Key': config['apiKey']!,
      'Content-Type': 'application/json',
    },
    body: jsonEncode({'command': command}),
  ).timeout(const Duration(seconds: 30));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

/// Sends a message to the coding assistant. Returns {"status":..., "reply":...}.
Future<Map<String, dynamic>> sendCodeMessage(String message) async {
  final config = await getServerConfig();
  final res = await http.post(
    Uri.parse('${_baseUrl(config['ip']!)}/api/chat/code'),
    headers: {
      'X-API-Key': config['apiKey']!,
      'Content-Type': 'application/json',
    },
    body: jsonEncode({'message': message}),
  ).timeout(const Duration(seconds: 60));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

/// Resets the coding assistant conversation history.
Future<void> resetCodeConversation() async {
  final config = await getServerConfig();
  await http.post(
    Uri.parse('${_baseUrl(config['ip']!)}/api/chat/code/reset'),
    headers: {'X-API-Key': config['apiKey']!},
  ).timeout(const Duration(seconds: 10));
}

/// Sends setup data to the PC. Returns {"status":..., "message":...} or error with "field".
Future<Map<String, dynamic>> submitSetup({
  required String userName,
  required String groqKey,
  String emailAddress = '',
  String emailAppPassword = '',
  String defaultCity = 'Wah Cantt',
  List<Map<String, String>> whatsappContacts = const [],
}) async {
  final config = await getServerConfig();
  final res = await http.post(
    Uri.parse('${_baseUrl(config['ip']!)}/api/setup'),
    headers: {
      'X-API-Key': config['apiKey']!,
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'user_name': userName,
      'groq_key': groqKey,
      'email_address': emailAddress,
      'email_app_password': emailAppPassword,
      'default_city': defaultCity,
      'whatsapp_contacts': whatsappContacts,
    }),
  ).timeout(const Duration(seconds: 30));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

/// Opens a WebSocket connection to /ws/status for real-time NOVA state.
Future<WebSocketChannel> openStatusSocket() async {
  final config = await getServerConfig();
  final uri = Uri.parse('ws://${config['ip']}:$_kApiPort/ws/status');
  return WebSocketChannel.connect(uri);
}

/// Opens a WebSocket connection to /ws/interactive for multi-turn commands.
Future<WebSocketChannel> openInteractiveSocket() async {
  final config = await getServerConfig();
  final uri = Uri.parse('ws://${config['ip']}:$_kApiPort/ws/interactive');
  return WebSocketChannel.connect(uri);
}
