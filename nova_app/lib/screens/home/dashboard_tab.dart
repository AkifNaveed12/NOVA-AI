import 'package:flutter/material.dart';
import '../../api/client.dart';

class _QuickAction {
  final String label;
  final String command;
  final IconData icon;
  const _QuickAction(this.label, this.command, this.icon);
}

const _kActions = [
  _QuickAction('Lock PC',      'lock screen',      Icons.lock_outline),
  _QuickAction('Mute',         'mute',             Icons.volume_off_outlined),
  _QuickAction('Volume Up',    'volume up',        Icons.volume_up_outlined),
  _QuickAction('Volume Down',  'volume down',      Icons.volume_down_outlined),
  _QuickAction('Screenshot',   'take screenshot',  Icons.screenshot_monitor_outlined),
  _QuickAction('Open YouTube', 'open youtube',     Icons.play_circle_outline),
  _QuickAction('Battery',      'battery level',    Icons.battery_4_bar_outlined),
  _QuickAction('CPU Usage',    'cpu usage',        Icons.speed_outlined),
];

class DashboardTab extends StatefulWidget {
  const DashboardTab({super.key});

  @override
  State<DashboardTab> createState() => _DashboardTabState();
}

class _DashboardTabState extends State<DashboardTab> {
  String _lastResponse = '';
  bool _loading = false;

  Future<void> _runAction(String command) async {
    setState(() { _loading = true; _lastResponse = ''; });
    try {
      final result = await sendCommand(command);
      setState(() {
        _lastResponse = result['response'] as String? ??
                        result['message'] as String? ?? 'Done.';
        _loading = false;
      });
    } catch (e) {
      setState(() { _lastResponse = 'Error: $e'; _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(20, 24, 20, 4),
            child: Text('NOVA AI',
              style: TextStyle(color: Color(0xFF00D4FF), fontSize: 22,
                fontWeight: FontWeight.bold, letterSpacing: 2)),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(20, 0, 20, 16),
            child: Text('Quick Actions',
              style: TextStyle(color: Color(0xFF666688), fontSize: 13)),
          ),
          Expanded(
            child: GridView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 1.6,
              ),
              itemCount: _kActions.length,
              itemBuilder: (_, i) {
                final action = _kActions[i];
                return GestureDetector(
                  onTap: _loading ? null : () => _runAction(action.command),
                  child: Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF111122),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFF222244)),
                    ),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(action.icon, color: const Color(0xFF00D4FF), size: 24),
                        const SizedBox(height: 8),
                        Text(action.label,
                          style: const TextStyle(color: Colors.white, fontSize: 14,
                            fontWeight: FontWeight.w500)),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          if (_loading || _lastResponse.isNotEmpty)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF111122),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF00D4FF33)),
              ),
              child: _loading
                ? const Row(
                    children: [
                      SizedBox(height: 16, width: 16,
                        child: CircularProgressIndicator(
                          color: Color(0xFF00D4FF), strokeWidth: 2)),
                      SizedBox(width: 12),
                      Text('Running...', style: TextStyle(color: Color(0xFF666688))),
                    ])
                : Text(_lastResponse,
                    style: const TextStyle(color: Colors.white, fontSize: 13)),
            ),
        ],
      ),
    );
  }
}
