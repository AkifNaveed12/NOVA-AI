import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../api/client.dart';

// ── Quick action definitions ──────────────────────────────────────

class _QuickAction {
  final String label;
  final String command;
  final IconData icon;
  const _QuickAction(this.label, this.command, this.icon);
}

const _kActions = [
  _QuickAction('Lock PC',       'lock screen',      Icons.lock_outline),
  _QuickAction('Mute',          'mute',             Icons.volume_off_outlined),
  _QuickAction('Volume Up',     'volume up',        Icons.volume_up_outlined),
  _QuickAction('Volume Down',   'volume down',      Icons.volume_down_outlined),
  _QuickAction('Screenshot',    'take screenshot',  Icons.screenshot_monitor_outlined),
  _QuickAction('Open YouTube',  'open youtube',     Icons.play_circle_outline),
  _QuickAction('Weather',       'what is the weather today', Icons.wb_sunny_outlined),
  _QuickAction('Battery',       'battery level',    Icons.battery_4_bar_outlined),
];

// ── Dashboard ─────────────────────────────────────────────────────

class DashboardTab extends StatefulWidget {
  const DashboardTab({super.key});

  @override
  State<DashboardTab> createState() => _DashboardTabState();
}

class _DashboardTabState extends State<DashboardTab> {
  // Quick actions
  bool _actionLoading = false;
  String _lastResponse = '';

  // Search (F8)
  String _searchPlatform = 'YouTube';
  final _searchCtrl = TextEditingController();
  bool _searchLoading = false;

  // Clipboard (F6)
  String _pcClipboard = '';
  bool _clipboardLoading = false;
  Timer? _clipboardTimer;

  // PC Context (Module 1)
  Map<String, dynamic> _pcContext = {};
  bool _contextLoading = false;
  Timer? _contextTimer;

  // Notes (F7)
  List<Map<String, dynamic>> _notes = [];
  bool _notesLoading = false;

  // Tasks (F7)
  List<Map<String, dynamic>> _tasks = [];
  bool _tasksLoading = false;

  // Activity (F9)
  List<Map<String, dynamic>> _activity = [];
  bool _activityLoading = false;
  bool _activityExpanded = false;

  @override
  void initState() {
    super.initState();
    _loadAll();
    _clipboardTimer = Timer.periodic(
      const Duration(seconds: 10), (_) => _refreshClipboard());
    _contextTimer = Timer.periodic(
      const Duration(seconds: 10), (_) => _refreshContext());
  }

  @override
  void dispose() {
    _clipboardTimer?.cancel();
    _contextTimer?.cancel();
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadAll() async {
    await Future.wait([
      _refreshClipboard(),
      _refreshContext(),
      _refreshNotes(),
      _refreshTasks(),
      _refreshActivity(),
    ]);
  }

  Future<void> _refreshContext() async {
    if (!mounted) return;
    setState(() => _contextLoading = true);
    try {
      final contextData = await fetchPCContext();
      if (!mounted) return;
      setState(() {
        _pcContext = contextData;
        _contextLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _contextLoading = false);
    }
  }

  Future<void> _refreshClipboard() async {
    if (!mounted) return;
    setState(() => _clipboardLoading = true);
    try {
      final content = await fetchClipboard();
      if (!mounted) return;
      setState(() { _pcClipboard = content ?? ''; _clipboardLoading = false; });
    } catch (_) {
      if (!mounted) return;
      setState(() => _clipboardLoading = false);
    }
  }


  Future<void> _refreshNotes() async {
    setState(() => _notesLoading = true);
    try {
      final notes = await fetchNotes(limit: 3);
      if (!mounted) return;
      setState(() { _notes = notes; _notesLoading = false; });
    } catch (_) {
      if (!mounted) return;
      setState(() => _notesLoading = false);
    }
  }

  Future<void> _refreshTasks() async {
    setState(() => _tasksLoading = true);
    try {
      final tasks = await fetchTasks();
      if (!mounted) return;
      setState(() { _tasks = tasks.take(5).toList(); _tasksLoading = false; });
    } catch (_) {
      if (!mounted) return;
      setState(() => _tasksLoading = false);
    }
  }

  Future<void> _refreshActivity() async {
    setState(() => _activityLoading = true);
    try {
      final act = await fetchActivity(limit: 5);
      if (!mounted) return;
      setState(() { _activity = act; _activityLoading = false; });
    } catch (_) {
      if (!mounted) return;
      setState(() => _activityLoading = false);
    }
  }

  Future<void> _runAction(String command) async {
    setState(() { _actionLoading = true; _lastResponse = ''; });
    try {
      final result = await sendCommand(command);
      final response = result['response'] as String? ??
                      result['message'] as String? ?? 'Done.';
      if (!mounted) return;
      setState(() { _lastResponse = response; _actionLoading = false; });
      if (command.contains('screenshot')) _refreshActivity();
    } catch (e) {
      if (!mounted) return;
      setState(() { _lastResponse = 'Error: $e'; _actionLoading = false; });
    }
  }

  Future<void> _doSearch() async {
    final query = _searchCtrl.text.trim();
    if (query.isEmpty) return;
    setState(() => _searchLoading = true);
    try {
      await sendCommand('search $query on ${_searchPlatform.toLowerCase()}');
      if (!mounted) return;
      setState(() {
        _lastResponse = 'Searching "$query" on $_searchPlatform...';
        _searchLoading = false;
      });
      _searchCtrl.clear();
    } catch (e) {
      if (!mounted) return;
      setState(() { _lastResponse = 'Error: $e'; _searchLoading = false; });
    }
  }

  // ── Notes dialog ─────────────────────────────────────────────────

  void _showAllNotes() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF0D0D1E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (ctx) => _NotesSheet(
        notes: _notes,
        onChanged: _refreshNotes,
      ),
    );
  }

  void _showAddNoteDialog() async {
    final ctrl = TextEditingController();
    final saved = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1B163B),
        title: const Text('New Note', style: TextStyle(color: Colors.white)),
        content: TextField(
          controller: ctrl,
          autofocus: true,
          maxLines: 3,
          decoration: const InputDecoration(
            hintText: 'Write your note...',
            labelText: 'Note',
            labelStyle: TextStyle(color: Color(0xFF7B6CF6))),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, ctrl.text.trim()),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF7B6CF6),
              foregroundColor: Colors.black),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    if (saved == null || saved.isEmpty) return;
    try {
      await addNote(saved);
      await _refreshNotes();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e'), backgroundColor: const Color(0xFFAA2222)));
    }
  }

  // ── Tasks dialog ─────────────────────────────────────────────────

  void _showAllTasks() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF0D0D1E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (ctx) => _TasksSheet(
        tasks: _tasks,
        onChanged: _refreshTasks,
      ),
    );
  }

  void _showAddTaskDialog() async {
    final ctrl = TextEditingController();
    String priority = 'medium';
    final saved = await showDialog<Map<String, String>>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, ss) => AlertDialog(
          backgroundColor: const Color(0xFF1B163B),
          title: const Text('New Task', style: TextStyle(color: Colors.white)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: ctrl,
                autofocus: true,
                decoration: const InputDecoration(
                  hintText: 'What needs to be done?',
                  labelText: 'Task',
                  labelStyle: TextStyle(color: Color(0xFF7B6CF6))),
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: ['low', 'medium', 'high'].map((p) => GestureDetector(
                  onTap: () => ss(() => priority = p),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: priority == p
                        ? _priorityColor(p)
                        : const Color(0xFF1A1A2E),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: _priorityColor(p).withOpacity(0.5)),
                    ),
                    child: Text(p,
                      style: TextStyle(
                        color: priority == p ? Colors.black : _priorityColor(p),
                        fontSize: 12, fontWeight: FontWeight.bold)),
                  ),
                )).toList(),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () => Navigator.pop(ctx, {'title': ctrl.text.trim(), 'priority': priority}),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF7B6CF6), foregroundColor: Colors.black),
              child: const Text('Add'),
            ),
          ],
        ),
      ),
    );
    if (saved == null || (saved['title'] ?? '').isEmpty) return;
    try {
      await addTask(saved['title']!, priority: saved['priority']!);
      await _refreshTasks();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e'), backgroundColor: const Color(0xFFAA2222)));
    }
  }

  // ── Build helpers ─────────────────────────────────────────────────

  Color _priorityColor(String p) {
    switch (p.toLowerCase()) {
      case 'high': case '3': return const Color(0xFFFF4444);
      case 'medium': case '2': return const Color(0xFFFFAA00);
      default: return const Color(0xFF00FF88);
    }
  }

  Color _priorityColorFromInt(dynamic p) {
    final v = p is int ? p : int.tryParse('$p') ?? 2;
    if (v >= 3) return const Color(0xFFFF4444);
    if (v == 2) return const Color(0xFFFFAA00);
    return const Color(0xFF00FF88);
  }

  Widget _sectionHeader(String title, {Widget? trailing}) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(0, 4, 0, 10),
      child: Row(children: [
        Text(title,
          style: const TextStyle(color: Color(0xFF888899), fontSize: 12,
            fontWeight: FontWeight.bold, letterSpacing: 1)),
        const Spacer(),
        if (trailing != null) trailing,
      ]),
    );
  }

  // ── Build ─────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: RefreshIndicator(
        onRefresh: _loadAll,
        color: const Color(0xFF7B6CF6),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [

              // ── Header ─────────────────────────────────────────
              const Text('NOVA AI',
                style: TextStyle(color: Color(0xFF7B6CF6), fontSize: 22,
                  fontWeight: FontWeight.bold, letterSpacing: 2)),
              const SizedBox(height: 2),
              const Text('Your AI assistant',
                style: TextStyle(color: Color(0xFF444466), fontSize: 12)),
              const SizedBox(height: 20),

              // ── Search bar (F8) ────────────────────────────────
              _buildSearchBar(),
              const SizedBox(height: 20),

              // ── Quick Actions ──────────────────────────────────
              _sectionHeader('QUICK ACTIONS'),
              _buildQuickActions(),

              // Response card
              if (_actionLoading || _lastResponse.isNotEmpty) ...[
                const SizedBox(height: 12),
                _buildResponseCard(),
              ],
              const SizedBox(height: 20),

              // ── PC Live Context (Module 1) ──────────────────────
              _sectionHeader('PC LIVE CONTEXT',
                trailing: IconButton(
                  icon: const Icon(Icons.refresh,
                    color: Color(0xFF555577), size: 16),
                  onPressed: _refreshContext,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
                )),
              _buildPCContext(),
              const SizedBox(height: 20),

              // ── Clipboard (F6) ─────────────────────────────────
              _sectionHeader('CLIPBOARD SYNC',
                trailing: IconButton(
                  icon: const Icon(Icons.refresh,
                    color: Color(0xFF555577), size: 16),
                  onPressed: _refreshClipboard,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
                )),
              _buildClipboard(),
              const SizedBox(height: 20),

              // ── Notes (F7) ────────────────────────────────────
              _sectionHeader('NOTES',
                trailing: Row(children: [
                  GestureDetector(
                    onTap: _showAllNotes,
                    child: const Text('See all',
                      style: TextStyle(color: Color(0xFF7B6CF6), fontSize: 12))),
                  const SizedBox(width: 12),
                  GestureDetector(
                    onTap: _showAddNoteDialog,
                    child: const Icon(Icons.add,
                      color: Color(0xFF7B6CF6), size: 18)),
                ])),
              _buildNotes(),
              const SizedBox(height: 20),

              // ── Tasks (F7) ────────────────────────────────────
              _sectionHeader('TASKS',
                trailing: Row(children: [
                  GestureDetector(
                    onTap: _showAllTasks,
                    child: const Text('See all',
                      style: TextStyle(color: Color(0xFF7B6CF6), fontSize: 12))),
                  const SizedBox(width: 12),
                  GestureDetector(
                    onTap: _showAddTaskDialog,
                    child: const Icon(Icons.add,
                      color: Color(0xFF7B6CF6), size: 18)),
                ])),
              _buildTasks(),
              const SizedBox(height: 20),

              // ── Activity (F9) ─────────────────────────────────
              _sectionHeader('RECENT ACTIVITY',
                trailing: GestureDetector(
                  onTap: () => setState(() => _activityExpanded = !_activityExpanded),
                  child: Icon(
                    _activityExpanded
                      ? Icons.keyboard_arrow_up
                      : Icons.keyboard_arrow_down,
                    color: const Color(0xFF555577), size: 18),
                )),
              _buildActivity(),
            ],
          ),
        ),
      ),
    );
  }

  // ── Search bar ────────────────────────────────────────────────────

  Widget _buildSearchBar() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1B163B),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF3D35A8)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Platform pills
          Row(children: ['YouTube', 'Google', 'Wikipedia'].map((p) =>
            GestureDetector(
              onTap: () => setState(() => _searchPlatform = p),
              child: Container(
                margin: const EdgeInsets.only(right: 8),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: _searchPlatform == p
                    ? const Color(0x227B6CF6)
                    : Colors.transparent,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: _searchPlatform == p
                      ? const Color(0xFF7B6CF6)
                      : const Color(0xFF333355)),
                ),
                child: Text(p,
                  style: TextStyle(
                    color: _searchPlatform == p
                      ? const Color(0xFF7B6CF6)
                      : const Color(0xFF666688),
                    fontSize: 12)),
              ),
            )).toList()),
          const SizedBox(height: 8),
          Row(children: [
            Expanded(
              child: TextField(
                controller: _searchCtrl,
                onSubmitted: (_) => _doSearch(),
                decoration: InputDecoration(
                  hintText: 'Search on $_searchPlatform...',
                  hintStyle: const TextStyle(color: Color(0xFF444466), fontSize: 13),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.zero,
                  isDense: true,
                ),
                style: const TextStyle(color: Colors.white, fontSize: 14),
              ),
            ),
            GestureDetector(
              onTap: _searchLoading ? null : _doSearch,
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF7B6CF6),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: _searchLoading
                  ? const SizedBox(width: 16, height: 16,
                      child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2))
                  : const Icon(Icons.search, color: Colors.black, size: 18),
              ),
            ),
          ]),
        ],
      ),
    );
  }

  // ── Quick actions grid ────────────────────────────────────────────

  Widget _buildQuickActions() {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 4,
        crossAxisSpacing: 8,
        mainAxisSpacing: 8,
        childAspectRatio: 0.85,
      ),
      itemCount: _kActions.length,
      itemBuilder: (_, i) {
        final a = _kActions[i];
        return GestureDetector(
          onTap: _actionLoading ? null : () => _runAction(a.command),
          child: Container(
            decoration: BoxDecoration(
              color: const Color(0xFF1B163B),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFF3D35A8)),
            ),
            padding: const EdgeInsets.all(8),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(a.icon, color: const Color(0xFF7B6CF6), size: 22),
                const SizedBox(height: 6),
                Text(a.label,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white, fontSize: 10),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
        );
      },
    );
  }

  // ── Response card ─────────────────────────────────────────────────

  Widget _buildResponseCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0E0B1F),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0x227B6CF6)),
      ),
      child: _actionLoading
        ? const Row(children: [
            SizedBox(height: 14, width: 14,
              child: CircularProgressIndicator(
                color: Color(0xFF7B6CF6), strokeWidth: 2)),
            SizedBox(width: 10),
            Text('Running...', style: TextStyle(color: Color(0xFF666688), fontSize: 13)),
          ])
        : Text(_lastResponse,
            style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4)),
    );
  }

  // ── PC Live Context Widget (Module 1) ─────────────────────────────

  Widget _buildPCContext() {
    final snap = _pcContext['snapshot'] as Map<String, dynamic>?;
    final activeWin = snap?['active_window'] as Map<String, dynamic>?;
    final activeTitle = activeWin?['title'] as String? ?? 'No active window';

    final system = snap?['system'] as Map<String, dynamic>?;
    final cpu = system?['cpu_percent'] ?? 0.0;
    final ram = system?['ram_percent'] ?? 0.0;

    final battery = snap?['battery'] as Map<String, dynamic>?;
    final batPercent = battery?['percent'] ?? 0;
    final plugged = battery?['plugged'] ?? false;

    final topProcs = snap?['top_processes'] as List? ?? [];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1B163B),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF3D35A8)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Active Window info
          Row(
            children: [
              const Icon(Icons.desktop_windows, color: Color(0xFF7B6CF6), size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  activeTitle,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Stats Row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: _buildContextStatItem(
                  'CPU Usage',
                  '$cpu%',
                  Icons.developer_board,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildContextStatItem(
                  'RAM Usage',
                  '$ram%',
                  Icons.memory,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildContextStatItem(
                  'Battery',
                  batPercent > 0 ? '$batPercent%${plugged ? " ⚡" : ""}' : 'N/A',
                  Icons.battery_std,
                ),
              ),
            ],
          ),
          if (topProcs.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Text(
              'TOP PROCESSES',
              style: TextStyle(
                color: Color(0xFF666688),
                fontSize: 10,
                fontWeight: FontWeight.bold,
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 6),
            ...topProcs.take(3).map((p) {
              final proc = p as Map<String, dynamic>;
              final name = proc['name'] ?? 'Unknown';
              final procCpu = proc['cpu_percent'] ?? 0.0;
              return Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        name,
                        style: const TextStyle(color: Color(0xFFCCCCCC), fontSize: 11),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Text(
                      '$procCpu% CPU',
                      style: const TextStyle(color: Color(0xFF7B6CF6), fontSize: 11),
                    ),
                  ],
                ),
              );
            }).toList(),
          ],
        ],
      ),
    );
  }

  Widget _buildContextStatItem(String label, String value, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: const Color(0xFF0E0B1F),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0x227B6CF6)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: const Color(0xFF666688), size: 12),
              const SizedBox(width: 4),
              Text(
                label,
                style: const TextStyle(color: Color(0xFF666688), fontSize: 9),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }


  // ── Clipboard ─────────────────────────────────────────────────────

  Widget _buildClipboard() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1B163B),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF3D35A8)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _clipboardLoading
            ? const Text('Loading...',
                style: TextStyle(color: Color(0xFF444466), fontSize: 12))
            : _pcClipboard.isEmpty
              ? const Text('PC clipboard is empty',
                  style: TextStyle(color: Color(0xFF444466), fontSize: 12,
                    fontStyle: FontStyle.italic))
              : Text(
                  _pcClipboard.length > 120
                    ? '${_pcClipboard.substring(0, 120)}...'
                    : _pcClipboard,
                  style: const TextStyle(color: Color(0xFFCCCCDD), fontSize: 13,
                    height: 1.4, fontFamily: 'monospace'),
                ),
          const SizedBox(height: 10),
          Row(children: [
            // Copy PC clipboard → phone
            _SmallButton(
              icon: Icons.phone_android,
              label: 'Copy to phone',
              onTap: _pcClipboard.isEmpty ? null : () async {
                await Clipboard.setData(ClipboardData(text: _pcClipboard));
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                  content: Text('Copied to phone clipboard'),
                  duration: Duration(seconds: 1)));
              },
            ),
            const SizedBox(width: 8),
            // Send phone clipboard → PC
            _SmallButton(
              icon: Icons.computer,
              label: 'Send to PC',
              onTap: () async {
                final data = await Clipboard.getData(Clipboard.kTextPlain);
                final text = data?.text ?? '';
                if (text.isEmpty) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Your phone clipboard is empty')));
                  return;
                }
                try {
                  await setClipboard(text);
                  if (!mounted) return;
                  setState(() => _pcClipboard = text);
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Sent to PC clipboard'),
                    duration: Duration(seconds: 1)));
                } catch (e) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: $e')));
                }
              },
            ),
          ]),
        ],
      ),
    );
  }

  // ── Notes ──────────────────────────────────────────────────────────

  Widget _buildNotes() {
    if (_notesLoading) {
      return const _LoadingRow();
    }
    if (_notes.isEmpty) {
      return _EmptyCard(
        text: 'No notes yet',
        onAdd: _showAddNoteDialog,
        addLabel: 'Add note',
      );
    }
    return Column(
      children: _notes.map((n) => Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 6),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFF1B163B),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: const Color(0xFF3D35A8)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              (n['content'] as String? ?? '').length > 100
                ? '${(n['content'] as String).substring(0, 100)}...'
                : n['content'] as String? ?? '',
              style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4)),
            if ((n['created_at'] as String?) != null) ...[
              const SizedBox(height: 4),
              Text(
                _formatDate(n['created_at'] as String),
                style: const TextStyle(color: Color(0xFF444466), fontSize: 10)),
            ],
          ],
        ),
      )).toList(),
    );
  }

  // ── Tasks ─────────────────────────────────────────────────────────

  Widget _buildTasks() {
    if (_tasksLoading) {
      return const _LoadingRow();
    }
    if (_tasks.isEmpty) {
      return _EmptyCard(
        text: 'No pending tasks',
        onAdd: _showAddTaskDialog,
        addLabel: 'Add task',
      );
    }
    return Column(
      children: _tasks.map((t) {
        final taskId = t['id'] as int? ?? 0;
        final title = t['title'] as String? ?? '';
        final priority = t['priority'];
        return Container(
          margin: const EdgeInsets.only(bottom: 6),
          decoration: BoxDecoration(
            color: const Color(0xFF1B163B),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: const Color(0xFF3D35A8)),
          ),
          child: ListTile(
            dense: true,
            leading: GestureDetector(
              onTap: () async {
                try {
                  await markTaskDone(taskId);
                  await _refreshTasks();
                } catch (_) {}
              },
              child: Container(
                width: 22, height: 22,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: _priorityColorFromInt(priority), width: 2)),
                child: const SizedBox(),
              ),
            ),
            title: Text(title,
              style: const TextStyle(color: Colors.white, fontSize: 13)),
            trailing: Container(
              width: 8, height: 8,
              decoration: BoxDecoration(
                color: _priorityColorFromInt(priority),
                shape: BoxShape.circle),
            ),
          ),
        );
      }).toList(),
    );
  }

  // ── Activity ─────────────────────────────────────────────────────

  Widget _buildActivity() {
    if (_activityLoading) {
      return const _LoadingRow();
    }
    if (_activity.isEmpty) {
      return const Text('No activity yet',
        style: TextStyle(color: Color(0xFF444466), fontSize: 12,
          fontStyle: FontStyle.italic));
    }

    final items = _activityExpanded ? _activity : _activity.take(3).toList();
    return Column(
      children: items.map((a) {
        final cmd = a['command_text'] as String? ?? '';
        final mod = a['module_triggered'] as String? ?? '';
        final resp = a['response_summary'] as String? ?? '';
        final ok = (a['success'] == true || a['success'] == 1);
        final ts = a['timestamp'] as String? ?? '';
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: const Color(0xFF0D0D1E),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: const Color(0xFF1A1A2E)),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 6, height: 6,
                margin: const EdgeInsets.only(top: 6, right: 10),
                decoration: BoxDecoration(
                  color: ok ? const Color(0xFF00FF88) : const Color(0xFFFF4444),
                  shape: BoxShape.circle),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(cmd,
                      style: const TextStyle(color: Colors.white, fontSize: 12,
                        fontWeight: FontWeight.w500),
                      overflow: TextOverflow.ellipsis),
                    if (resp.isNotEmpty)
                      Text(resp.length > 80 ? '${resp.substring(0, 80)}...' : resp,
                        style: const TextStyle(color: Color(0xFF666688), fontSize: 11),
                        overflow: TextOverflow.ellipsis),
                    if (mod.isNotEmpty || ts.isNotEmpty)
                      Text('${mod.isNotEmpty ? mod : ""}${ts.isNotEmpty ? "  •  ${_formatDate(ts)}" : ""}',
                        style: const TextStyle(color: Color(0xFF444466), fontSize: 10)),
                  ],
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  // ── Date formatter ────────────────────────────────────────────────

  String _formatDate(String raw) {
    try {
      final dt = DateTime.parse(raw);
      final now = DateTime.now();
      final diff = now.difference(dt);
      if (diff.inMinutes < 1) return 'just now';
      if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
      if (diff.inHours < 24) return '${diff.inHours}h ago';
      return '${diff.inDays}d ago';
    } catch (_) {
      return raw.length > 16 ? raw.substring(0, 16) : raw;
    }
  }
}

// ── Notes bottom sheet ────────────────────────────────────────────

class _NotesSheet extends StatefulWidget {
  final List<Map<String, dynamic>> notes;
  final VoidCallback onChanged;
  const _NotesSheet({required this.notes, required this.onChanged});

  @override
  State<_NotesSheet> createState() => _NotesSheetState();
}

class _NotesSheetState extends State<_NotesSheet> {
  late List<Map<String, dynamic>> _notes;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _notes = List.from(widget.notes);
    _reload();
  }

  Future<void> _reload() async {
    setState(() => _loading = true);
    try {
      final fresh = await fetchNotes(limit: 30);
      if (!mounted) return;
      setState(() { _notes = fresh; _loading = false; });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.8,
      maxChildSize: 0.95,
      builder: (_, ctrl) => Column(
        children: [
          // Handle
          Container(
            margin: const EdgeInsets.only(top: 8),
            width: 36, height: 4,
            decoration: BoxDecoration(
              color: const Color(0xFF444466),
              borderRadius: BorderRadius.circular(2)),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 8, 8),
            child: Row(children: [
              const Icon(Icons.note_outlined, color: Color(0xFF7B6CF6), size: 18),
              const SizedBox(width: 8),
              const Text('All Notes',
                style: TextStyle(color: Colors.white, fontSize: 16,
                  fontWeight: FontWeight.bold)),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.add, color: Color(0xFF7B6CF6)),
                onPressed: () async {
                  Navigator.pop(context);
                },
              ),
            ]),
          ),
          const Divider(color: Color(0xFF3D35A8), height: 1),
          Expanded(
            child: _loading
              ? const Center(child: CircularProgressIndicator(color: Color(0xFF7B6CF6)))
              : _notes.isEmpty
                ? const Center(child: Text('No notes yet',
                    style: TextStyle(color: Color(0xFF555577))))
                : ListView.builder(
                    controller: ctrl,
                    itemCount: _notes.length,
                    itemBuilder: (_, i) {
                      final n = _notes[i];
                      return Dismissible(
                        key: Key('${n['id']}'),
                        direction: DismissDirection.endToStart,
                        confirmDismiss: (_) async {
                          try {
                            await deleteNote(n['id'] as int);
                            widget.onChanged();
                            return true;
                          } catch (_) { return false; }
                        },
                        background: Container(
                          alignment: Alignment.centerRight,
                          padding: const EdgeInsets.only(right: 20),
                          color: const Color(0xFF3A0000),
                          child: const Icon(Icons.delete_outline,
                            color: Color(0xFFFF4444))),
                        child: ListTile(
                          title: Text(n['content'] as String? ?? '',
                            style: const TextStyle(color: Colors.white, fontSize: 13)),
                          subtitle: n['created_at'] != null
                            ? Text(_fmtDate(n['created_at'] as String),
                                style: const TextStyle(color: Color(0xFF444466), fontSize: 10))
                            : null,
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  String _fmtDate(String raw) {
    try {
      final dt = DateTime.parse(raw);
      final now = DateTime.now();
      final diff = now.difference(dt);
      if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
      if (diff.inHours < 24) return '${diff.inHours}h ago';
      return '${diff.inDays}d ago';
    } catch (_) { return raw; }
  }
}

// ── Tasks bottom sheet ────────────────────────────────────────────

class _TasksSheet extends StatefulWidget {
  final List<Map<String, dynamic>> tasks;
  final VoidCallback onChanged;
  const _TasksSheet({required this.tasks, required this.onChanged});

  @override
  State<_TasksSheet> createState() => _TasksSheetState();
}

class _TasksSheetState extends State<_TasksSheet> {
  late List<Map<String, dynamic>> _tasks;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _tasks = List.from(widget.tasks);
    _reload();
  }

  Future<void> _reload() async {
    setState(() => _loading = true);
    try {
      final fresh = await fetchTasks();
      if (!mounted) return;
      setState(() { _tasks = fresh; _loading = false; });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  Color _pColor(dynamic p) {
    final v = p is int ? p : int.tryParse('$p') ?? 2;
    if (v >= 3) return const Color(0xFFFF4444);
    if (v == 2) return const Color(0xFFFFAA00);
    return const Color(0xFF00FF88);
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.8,
      maxChildSize: 0.95,
      builder: (_, ctrl) => Column(
        children: [
          Container(
            margin: const EdgeInsets.only(top: 8),
            width: 36, height: 4,
            decoration: BoxDecoration(
              color: const Color(0xFF444466),
              borderRadius: BorderRadius.circular(2)),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 8, 8),
            child: Row(children: [
              const Icon(Icons.checklist, color: Color(0xFF7B6CF6), size: 18),
              const SizedBox(width: 8),
              const Text('All Tasks',
                style: TextStyle(color: Colors.white, fontSize: 16,
                  fontWeight: FontWeight.bold)),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.refresh, color: Color(0xFF555577)),
                onPressed: _reload,
              ),
            ]),
          ),
          const Divider(color: Color(0xFF3D35A8), height: 1),
          Expanded(
            child: _loading
              ? const Center(child: CircularProgressIndicator(color: Color(0xFF7B6CF6)))
              : _tasks.isEmpty
                ? const Center(child: Text('No pending tasks',
                    style: TextStyle(color: Color(0xFF555577))))
                : ListView.builder(
                    controller: ctrl,
                    itemCount: _tasks.length,
                    itemBuilder: (_, i) {
                      final t = _tasks[i];
                      final taskId = t['id'] as int? ?? 0;
                      final title = t['title'] as String? ?? '';
                      final priority = t['priority'];
                      return Dismissible(
                        key: Key('t$taskId'),
                        direction: DismissDirection.endToStart,
                        confirmDismiss: (_) async {
                          try {
                            await deleteTask(taskId);
                            widget.onChanged();
                            return true;
                          } catch (_) { return false; }
                        },
                        background: Container(
                          alignment: Alignment.centerRight,
                          padding: const EdgeInsets.only(right: 20),
                          color: const Color(0xFF3A0000),
                          child: const Icon(Icons.delete_outline,
                            color: Color(0xFFFF4444))),
                        child: ListTile(
                          dense: true,
                          leading: GestureDetector(
                            onTap: () async {
                              try {
                                await markTaskDone(taskId);
                                setState(() => _tasks.removeAt(i));
                                widget.onChanged();
                              } catch (_) {}
                            },
                            child: Container(
                              width: 22, height: 22,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                border: Border.all(color: _pColor(priority), width: 2)),
                            ),
                          ),
                          title: Text(title,
                            style: const TextStyle(color: Colors.white, fontSize: 13)),
                          trailing: Container(
                            width: 8, height: 8,
                            decoration: BoxDecoration(
                              color: _pColor(priority),
                              shape: BoxShape.circle),
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

// ── Shared helper widgets ─────────────────────────────────────────

class _SmallButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onTap;
  const _SmallButton({required this.icon, required this.label, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: onTap == null
            ? const Color(0xFF1A1A1A)
            : const Color(0xFF1A1A2E),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: const Color(0xFF333355)),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon, size: 14,
            color: onTap == null
              ? const Color(0xFF333355)
              : const Color(0xFF7B6CF6)),
          const SizedBox(width: 6),
          Text(label, style: TextStyle(
            fontSize: 11,
            color: onTap == null
              ? const Color(0xFF333355)
              : const Color(0xFFCCCCDD))),
        ]),
      ),
    );
  }
}

class _LoadingRow extends StatelessWidget {
  const _LoadingRow();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Row(children: [
        SizedBox(width: 14, height: 14,
          child: CircularProgressIndicator(
            color: Color(0xFF7B6CF6), strokeWidth: 2)),
        SizedBox(width: 10),
        Text('Loading...', style: TextStyle(color: Color(0xFF444466), fontSize: 12)),
      ]),
    );
  }
}

class _EmptyCard extends StatelessWidget {
  final String text;
  final VoidCallback onAdd;
  final String addLabel;
  const _EmptyCard({required this.text, required this.onAdd, required this.addLabel});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF0D0D1E),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF1A1A2E)),
      ),
      child: Row(children: [
        Text(text,
          style: const TextStyle(color: Color(0xFF444466), fontSize: 12,
            fontStyle: FontStyle.italic)),
        const Spacer(),
        GestureDetector(
          onTap: onAdd,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0x227B6CF6),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0x447B6CF6)),
            ),
            child: Text(addLabel,
              style: const TextStyle(color: Color(0xFF7B6CF6), fontSize: 11)),
          ),
        ),
      ]),
    );
  }
}
