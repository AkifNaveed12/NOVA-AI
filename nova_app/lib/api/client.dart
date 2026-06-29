import 'dart:convert';
import 'dart:typed_data';
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

// ── System info (F2) ──────────────────────────────────────────────

Future<Map<String, dynamic>> fetchSystemInfo() async {
  final config = await getServerConfig();
  final res = await http.get(
    Uri.parse('${_baseUrl(config['ip']!)}/api/system/info'),
    headers: {'X-API-Key': config['apiKey']!},
  ).timeout(const Duration(seconds: 10));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

// ── File browser (F3/F4) ─────────────────────────────────────────

Future<Map<String, dynamic>> listFiles(String path) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/files/list')
      .replace(queryParameters: {'path': path});
  final res = await http.get(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 10));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

Future<Map<String, dynamic>> searchFiles(String query) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/files/search')
      .replace(queryParameters: {'query': query});
  final res = await http.get(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 15));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

Future<Map<String, dynamic>> readFile(String path) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/files/read')
      .replace(queryParameters: {'path': path});
  final res = await http.get(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 10));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

Future<Map<String, dynamic>> writeFile(String path, String content) async {
  final config = await getServerConfig();
  final res = await http.post(
    Uri.parse('${_baseUrl(config['ip']!)}/api/files/write'),
    headers: {
      'X-API-Key': config['apiKey']!,
      'Content-Type': 'application/json',
    },
    body: jsonEncode({'path': path, 'content': content}),
  ).timeout(const Duration(seconds: 15));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

Future<Map<String, dynamic>> mkdirRemote(String path) async {
  final config = await getServerConfig();
  final res = await http.post(
    Uri.parse('${_baseUrl(config['ip']!)}/api/files/mkdir'),
    headers: {
      'X-API-Key': config['apiKey']!,
      'Content-Type': 'application/json',
    },
    body: jsonEncode({'path': path}),
  ).timeout(const Duration(seconds: 10));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

Future<Map<String, dynamic>> deleteRemote(String path) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/files/delete')
      .replace(queryParameters: {'path': path});
  final res = await http.delete(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 10));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

Future<Map<String, dynamic>> openRemote(String path) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/files/open')
      .replace(queryParameters: {'path': path});
  final res = await http.get(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 10));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

// ── Terminal (F3) ─────────────────────────────────────────────────

Future<Map<String, dynamic>> runTerminal(String cmd, {String? cwd}) async {
  final config = await getServerConfig();
  final body = <String, dynamic>{'command': cmd};
  if (cwd != null) body['cwd'] = cwd;
  final res = await http.post(
    Uri.parse('${_baseUrl(config['ip']!)}/api/terminal/run'),
    headers: {
      'X-API-Key': config['apiKey']!,
      'Content-Type': 'application/json',
    },
    body: jsonEncode(body),
  ).timeout(const Duration(seconds: 60));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

// ── Screenshot (F5) ───────────────────────────────────────────────

Future<Uint8List?> fetchScreenshot() async {
  final config = await getServerConfig();
  final res = await http.get(
    Uri.parse('${_baseUrl(config['ip']!)}/api/screenshot/latest'),
    headers: {'X-API-Key': config['apiKey']!},
  ).timeout(const Duration(seconds: 10));
  if (res.statusCode == 200) return res.bodyBytes;
  return null;
}

// ── Clipboard (F6) ────────────────────────────────────────────────

Future<String?> fetchClipboard() async {
  final config = await getServerConfig();
  final res = await http.get(
    Uri.parse('${_baseUrl(config['ip']!)}/api/clipboard'),
    headers: {'X-API-Key': config['apiKey']!},
  ).timeout(const Duration(seconds: 5));
  final data = jsonDecode(res.body) as Map<String, dynamic>;
  return data['content'] as String?;
}

Future<void> setClipboard(String text) async {
  final config = await getServerConfig();
  await http.post(
    Uri.parse('${_baseUrl(config['ip']!)}/api/clipboard'),
    headers: {
      'X-API-Key': config['apiKey']!,
      'Content-Type': 'application/json',
    },
    body: jsonEncode({'content': text}),
  ).timeout(const Duration(seconds: 5));
}

// ── Activity log (F9) ─────────────────────────────────────────────

// ── Notes (F7) ────────────────────────────────────────────────────

Future<List<Map<String, dynamic>>> fetchNotes({int limit = 20}) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/notes')
      .replace(queryParameters: {'limit': '$limit'});
  final res = await http.get(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 10));
  final data = jsonDecode(res.body) as Map<String, dynamic>;
  return (data['notes'] as List? ?? []).cast<Map<String, dynamic>>();
}

Future<void> addNote(String content, {String tags = ''}) async {
  final config = await getServerConfig();
  await http.post(
    Uri.parse('${_baseUrl(config['ip']!)}/api/notes'),
    headers: {'X-API-Key': config['apiKey']!, 'Content-Type': 'application/json'},
    body: jsonEncode({'content': content, 'tags': tags}),
  ).timeout(const Duration(seconds: 10));
}

Future<void> deleteNote(int id) async {
  final config = await getServerConfig();
  await http.delete(
    Uri.parse('${_baseUrl(config['ip']!)}/api/notes/$id'),
    headers: {'X-API-Key': config['apiKey']!},
  ).timeout(const Duration(seconds: 10));
}

// ── Tasks (F7) ────────────────────────────────────────────────────

Future<List<Map<String, dynamic>>> fetchTasks({bool includeDone = false}) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/tasks')
      .replace(queryParameters: {'include_done': '$includeDone'});
  final res = await http.get(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 10));
  final data = jsonDecode(res.body) as Map<String, dynamic>;
  return (data['tasks'] as List? ?? []).cast<Map<String, dynamic>>();
}

Future<void> addTask(String title, {String priority = 'medium', String? dueDate}) async {
  final config = await getServerConfig();
  final body = <String, dynamic>{'title': title, 'priority': priority};
  if (dueDate != null) body['due_date'] = dueDate;
  await http.post(
    Uri.parse('${_baseUrl(config['ip']!)}/api/tasks'),
    headers: {'X-API-Key': config['apiKey']!, 'Content-Type': 'application/json'},
    body: jsonEncode(body),
  ).timeout(const Duration(seconds: 10));
}

Future<void> markTaskDone(int id) async {
  final config = await getServerConfig();
  await http.patch(
    Uri.parse('${_baseUrl(config['ip']!)}/api/tasks/$id/done'),
    headers: {'X-API-Key': config['apiKey']!},
  ).timeout(const Duration(seconds: 10));
}

Future<void> deleteTask(int id) async {
  final config = await getServerConfig();
  await http.delete(
    Uri.parse('${_baseUrl(config['ip']!)}/api/tasks/$id'),
    headers: {'X-API-Key': config['apiKey']!},
  ).timeout(const Duration(seconds: 10));
}

// ── Activity log (F9) ─────────────────────────────────────────────

Future<List<Map<String, dynamic>>> fetchActivity({int limit = 30}) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/activity')
      .replace(queryParameters: {'limit': '$limit'});
  final res = await http.get(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 10));
  final data = jsonDecode(res.body) as Map<String, dynamic>;
  return (data['logs'] as List? ?? []).cast<Map<String, dynamic>>();
}

// ── Assignment & Face Auth (Phase 4 Additions) ────────────────────

Future<Map<String, dynamic>> uploadAssignment(Uint8List fileBytes, String filename) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/assignment/upload');
  final request = http.MultipartRequest('POST', uri)
    ..headers['X-API-Key'] = config['apiKey']!
    ..files.add(http.MultipartFile.fromBytes('file', fileBytes, filename: filename));
  final response = await request.send().timeout(const Duration(seconds: 30));
  final responseBody = await response.stream.bytesToString();
  return jsonDecode(responseBody) as Map<String, dynamic>;
}

Future<List<Map<String, dynamic>>> fetchAssignmentStatus() async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/assignment/status');
  final res = await http.get(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 10));
  final data = jsonDecode(res.body) as Map<String, dynamic>;
  return (data['assignments'] as List? ?? []).cast<Map<String, dynamic>>();
}

Future<Uint8List?> downloadAssignment(int id) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/assignment/download/$id');
  final res = await http.get(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 30));
  if (res.statusCode == 200) return res.bodyBytes;
  return null;
}

Future<Map<String, dynamic>> registerFaceWebcam(String userName) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/auth/face/register/webcam');
  final res = await http.post(
    uri,
    headers: {
      'X-API-Key': config['apiKey']!,
      'Content-Type': 'application/json',
    },
    body: jsonEncode({'user_name': userName}),
  ).timeout(const Duration(seconds: 40));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

Future<Map<String, dynamic>> verifyFaceWebcam(String userName) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/auth/face/verify/webcam');
  final res = await http.post(
    uri,
    headers: {
      'Content-Type': 'application/json',
    },
    body: jsonEncode({'user_name': userName}),
  ).timeout(const Duration(seconds: 40));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

Future<Map<String, dynamic>> fetchFaceStatus(String userName) async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/auth/face/status')
      .replace(queryParameters: {'user_name': userName});
  final res = await http.get(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 10));
  return jsonDecode(res.body) as Map<String, dynamic>;
}

// ── Module 1: PC Context ──────────────────────────────────────────

Future<Map<String, dynamic>> fetchPCContext() async {
  final config = await getServerConfig();
  final uri = Uri.parse('${_baseUrl(config['ip']!)}/api/context/current');
  final res = await http.get(uri, headers: {'X-API-Key': config['apiKey']!})
      .timeout(const Duration(seconds: 10));
  return jsonDecode(res.body) as Map<String, dynamic>;
}


