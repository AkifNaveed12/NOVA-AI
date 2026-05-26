import 'dart:async';
import 'package:flutter/material.dart';
import '../../api/client.dart';

class SystemTab extends StatefulWidget {
  const SystemTab({super.key});

  @override
  State<SystemTab> createState() => _SystemTabState();
}

class _SystemTabState extends State<SystemTab> {
  Map<String, dynamic> _info = {};
  bool _loading = true;
  String _error = '';
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _refresh();
    _timer = Timer.periodic(const Duration(seconds: 5), (_) => _refresh());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _refresh() async {
    try {
      final info = await fetchSystemInfo();
      if (!mounted) return;
      setState(() { _info = info; _loading = false; _error = ''; });
    } catch (e) {
      if (!mounted) return;
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  Color _cpuColor(double v) => v > 80
      ? const Color(0xFFFF4444)
      : v > 50 ? const Color(0xFFFFAA00) : const Color(0xFF00FF88);

  Color _ramColor(double v) => v > 85
      ? const Color(0xFFFF4444)
      : v > 65 ? const Color(0xFFFFAA00) : const Color(0xFF00D4FF);

  Color _battColor(double v) => v < 20
      ? const Color(0xFFFF4444)
      : v < 40 ? const Color(0xFFFFAA00) : const Color(0xFF00FF88);

  Widget _card({
    required String label,
    required String value,
    required IconData icon,
    required Color color,
    double? percent,
    String? sub,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF111122),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF222244)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(children: [
            Icon(icon, color: color, size: 16),
            const SizedBox(width: 6),
            Text(label,
              style: const TextStyle(color: Color(0xFF888899), fontSize: 11)),
          ]),
          const SizedBox(height: 6),
          Text(value,
            style: TextStyle(color: color, fontSize: 20,
              fontWeight: FontWeight.bold)),
          if (sub != null)
            Text(sub,
              style: const TextStyle(color: Color(0xFF555577), fontSize: 10)),
          if (percent != null) ...[
            const SizedBox(height: 6),
            ClipRRect(
              borderRadius: BorderRadius.circular(3),
              child: LinearProgressIndicator(
                value: (percent / 100).clamp(0.0, 1.0),
                minHeight: 4,
                backgroundColor: const Color(0xFF222233),
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(
        child: CircularProgressIndicator(color: Color(0xFF00D4FF)));
    }

    if (_error.isNotEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Color(0xFFFF4444), size: 40),
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Text(_error,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Color(0xFFFF8888), fontSize: 12)),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () { setState(() { _loading = true; _error = ''; }); _refresh(); },
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00D4FF),
                foregroundColor: Colors.black),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    final cpu = (_info['cpu_percent'] as num?)?.toDouble() ?? 0;
    final ram = (_info['ram_percent'] as num?)?.toDouble() ?? 0;
    final disk = (_info['disk_percent'] as num?)?.toDouble() ?? 0;
    final ramUsed = (_info['ram_used_gb'] as num?)?.toStringAsFixed(1) ?? '-';
    final ramTotal = (_info['ram_total_gb'] as num?)?.toStringAsFixed(1) ?? '-';
    final diskUsed = (_info['disk_used_gb'] as num?)?.toStringAsFixed(1) ?? '-';
    final diskTotal = (_info['disk_total_gb'] as num?)?.toStringAsFixed(1) ?? '-';
    final netSent = (_info['net_sent_mb'] as num?)?.toStringAsFixed(0) ?? '-';
    final netRecv = (_info['net_recv_mb'] as num?)?.toStringAsFixed(0) ?? '-';
    final battPct = (_info['battery_percent'] as num?)?.toDouble();
    final charging = _info['battery_charging'] as bool? ?? false;
    final uptime = _info['uptime'] as String? ?? '-';

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: _refresh,
        color: const Color(0xFF00D4FF),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(children: [
                const Icon(Icons.monitor, color: Color(0xFF00D4FF), size: 20),
                const SizedBox(width: 8),
                const Text('System Monitor',
                  style: TextStyle(color: Color(0xFF00D4FF), fontSize: 16,
                    fontWeight: FontWeight.bold)),
                const Spacer(),
                Text('Live • 5s',
                  style: const TextStyle(color: Color(0xFF555577), fontSize: 11)),
              ]),
              const SizedBox(height: 16),

              // CPU + RAM
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 1.25,
                children: [
                  _card(
                    label: 'CPU',
                    value: '${cpu.toStringAsFixed(1)}%',
                    icon: Icons.speed,
                    color: _cpuColor(cpu),
                    percent: cpu,
                  ),
                  _card(
                    label: 'RAM',
                    value: '${ram.toStringAsFixed(0)}%',
                    icon: Icons.memory,
                    color: _ramColor(ram),
                    percent: ram,
                    sub: '$ramUsed / $ramTotal GB',
                  ),
                  _card(
                    label: 'Disk (C:)',
                    value: '${disk.toStringAsFixed(0)}%',
                    icon: Icons.storage,
                    color: const Color(0xFF8888FF),
                    percent: disk,
                    sub: '$diskUsed / $diskTotal GB',
                  ),
                  battPct != null
                    ? _card(
                        label: charging ? 'Charging' : 'Battery',
                        value: '${battPct.toStringAsFixed(0)}%',
                        icon: charging
                          ? Icons.battery_charging_full
                          : Icons.battery_4_bar,
                        color: _battColor(battPct),
                        percent: battPct,
                      )
                    : _card(
                        label: 'Battery',
                        value: 'N/A',
                        icon: Icons.battery_unknown,
                        color: const Color(0xFF555577),
                      ),
                ],
              ),
              const SizedBox(height: 12),

              // Network
              Row(children: [
                Expanded(
                  child: _card(
                    label: 'Sent',
                    value: '${netSent}MB',
                    icon: Icons.upload,
                    color: const Color(0xFF00FFAA),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _card(
                    label: 'Received',
                    value: '${netRecv}MB',
                    icon: Icons.download,
                    color: const Color(0xFFFFAA00),
                  ),
                ),
              ]),
              const SizedBox(height: 12),

              // Uptime
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                decoration: BoxDecoration(
                  color: const Color(0xFF111122),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF222244)),
                ),
                child: Row(children: [
                  const Icon(Icons.timer_outlined, color: Color(0xFF888899), size: 18),
                  const SizedBox(width: 10),
                  const Text('Uptime',
                    style: TextStyle(color: Color(0xFF888899), fontSize: 12)),
                  const SizedBox(width: 16),
                  Text(uptime,
                    style: const TextStyle(color: Colors.white, fontSize: 14,
                      fontWeight: FontWeight.w500)),
                ]),
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }
}
