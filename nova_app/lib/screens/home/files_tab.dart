import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../api/client.dart';

class FilesTab extends StatefulWidget {
  const FilesTab({super.key});

  @override
  State<FilesTab> createState() => _FilesTabState();
}

class _FilesTabState extends State<FilesTab> {
  String _currentPath = '';
  List<Map<String, dynamic>> _entries = [];
  final List<String> _history = [];
  bool _loading = false;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _loadDir('');
  }

  Future<void> _loadDir(String path) async {
    setState(() { _loading = true; _error = ''; });
    try {
      final result = await listFiles(path);
      if (!mounted) return;
      setState(() {
        _entries = (result['entries'] as List).cast<Map<String, dynamic>>();
        _currentPath = (result['path'] as String?) ?? path;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  void _navigate(String path) {
    _history.add(_currentPath);
    _loadDir(path);
  }

  void _goBack() {
    if (_history.isEmpty) return;
    final prev = _history.removeLast();
    _loadDir(prev);
  }

  Future<void> _openFile(Map<String, dynamic> entry) async {
    final path = entry['path'] as String;
    final ext = (entry['extension'] as String? ?? '').toLowerCase();
    const viewable = {
      '.py', '.dart', '.js', '.ts', '.txt', '.md', '.json',
      '.yaml', '.yml', '.toml', '.ini', '.env', '.sh', '.bat',
      '.ps1', '.sql', '.html', '.css', '.xml', '.csv', '.cfg',
      '.java', '.cs', '.go', '.rs', '.rb', '.php', '.swift',
      '.kt', '.c', '.cpp', '.h',
    };

    if (viewable.contains(ext)) {
      await _showFileViewer(path, entry['name'] as String, ext);
    } else {
      try {
        await openRemote(path);
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Opened on PC'),
          backgroundColor: Color(0xFF00AA55)));
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Error: $e'),
          backgroundColor: const Color(0xFFAA2222)));
      }
    }
  }

  Future<void> _showFileViewer(String path, String name, String ext) async {
    String content;
    try {
      final result = await readFile(path);
      content = result['content'] as String? ?? '';
    } catch (e) {
      content = 'Error reading file:\n$e';
    }

    if (!mounted) return;
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF0D0D1E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (ctx) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.85,
        minChildSize: 0.4,
        maxChildSize: 0.97,
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
            // Header
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 4, 8),
              child: Row(children: [
                Icon(_langIcon(ext), color: _langColor(ext), size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(name,
                    style: const TextStyle(color: Colors.white,
                      fontWeight: FontWeight.bold, fontSize: 14),
                    overflow: TextOverflow.ellipsis)),
                IconButton(
                  icon: const Icon(Icons.copy, color: Color(0xFF555577), size: 18),
                  tooltip: 'Copy to clipboard',
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: content));
                    ScaffoldMessenger.of(ctx).showSnackBar(const SnackBar(
                      content: Text('Copied to clipboard'),
                      duration: Duration(seconds: 1)));
                  }),
                IconButton(
                  icon: const Icon(Icons.close, color: Color(0xFF555577), size: 20),
                  onPressed: () => Navigator.pop(ctx)),
              ]),
            ),
            const Divider(color: Color(0xFF3D35A8), height: 1),
            // Content
            Expanded(
              child: SingleChildScrollView(
                controller: ctrl,
                padding: const EdgeInsets.all(16),
                child: SelectableText(
                  content,
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    color: Color(0xFFCCFFCC),
                    fontSize: 12,
                    height: 1.5),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showNewItemDialog() async {
    final nameCtrl = TextEditingController();
    final contentCtrl = TextEditingController();
    bool isFolder = false;
    if (!mounted) return;

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, ss) => AlertDialog(
          backgroundColor: const Color(0xFF1B163B),
          title: const Text('Create new', style: TextStyle(color: Colors.white)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Toggle
              Row(children: [
                const Text('File', style: TextStyle(color: Color(0xFF888899), fontSize: 13)),
                Switch(
                  value: isFolder,
                  onChanged: (v) => ss(() => isFolder = v),
                  activeColor: const Color(0xFF7B6CF6)),
                const Text('Folder', style: TextStyle(color: Color(0xFF888899), fontSize: 13)),
              ]),
              const SizedBox(height: 8),
              TextField(
                controller: nameCtrl,
                autofocus: true,
                decoration: const InputDecoration(
                  labelText: 'Name',
                  labelStyle: TextStyle(color: Color(0xFF7B6CF6)),
                  hintText: 'e.g. main.py or src'),
              ),
              if (!isFolder) ...[
                const SizedBox(height: 8),
                TextField(
                  controller: contentCtrl,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Initial content (optional)',
                    labelStyle: TextStyle(color: Color(0xFF7B6CF6))),
                ),
              ],
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                final name = nameCtrl.text.trim();
                if (name.isEmpty) return;
                final newPath = _currentPath.isEmpty
                    ? name
                    : '$_currentPath\\$name';
                Navigator.pop(ctx);
                try {
                  if (isFolder) {
                    await mkdirRemote(newPath);
                  } else {
                    await writeFile(newPath, contentCtrl.text);
                  }
                  await _loadDir(_currentPath);
                } catch (e) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                    content: Text('Error: $e'),
                    backgroundColor: const Color(0xFFAA2222)));
                }
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF7B6CF6),
                foregroundColor: Colors.black),
              child: const Text('Create'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _confirmDelete(Map<String, dynamic> entry) async {
    final name = entry['name'] as String;
    if (!mounted) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1B163B),
        title: Text('Delete "$name"?',
          style: const TextStyle(color: Colors.white)),
        content: Text(
          (entry['type'] == 'directory')
            ? 'This will delete the folder and all its contents. Cannot be undone.'
            : 'This cannot be undone.',
          style: const TextStyle(color: Color(0xFF888899), fontSize: 13)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFAA2222)),
            child: const Text('Delete', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await deleteRemote(entry['path'] as String);
      await _loadDir(_currentPath);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Error: $e'),
        backgroundColor: const Color(0xFFAA2222)));
    }
  }

  String _formatSize(dynamic size) {
    if (size == null) return '';
    final b = (size as num).toInt();
    if (b < 1024) return '${b}B';
    if (b < 1024 * 1024) return '${(b / 1024).toStringAsFixed(1)}KB';
    if (b < 1024 * 1024 * 1024) return '${(b / (1024 * 1024)).toStringAsFixed(1)}MB';
    return '${(b / (1024 * 1024 * 1024)).toStringAsFixed(1)}GB';
  }

  IconData _entryIcon(Map<String, dynamic> e) {
    if (e['type'] == 'directory') return Icons.folder;
    switch ((e['extension'] as String? ?? '').toLowerCase()) {
      case '.py': return Icons.code;
      case '.dart': return Icons.code;
      case '.js': case '.ts': return Icons.code;
      case '.json': return Icons.data_object;
      case '.md': return Icons.article;
      case '.txt': return Icons.description;
      case '.pdf': return Icons.picture_as_pdf;
      case '.png': case '.jpg': case '.jpeg': case '.gif': case '.webp':
        return Icons.image;
      case '.mp4': case '.avi': case '.mkv': case '.mov':
        return Icons.video_library;
      case '.mp3': case '.wav': case '.flac': case '.ogg':
        return Icons.music_note;
      case '.zip': case '.rar': case '.7z': case '.tar': case '.gz':
        return Icons.archive;
      case '.exe': case '.msi': return Icons.apps;
      default: return Icons.insert_drive_file;
    }
  }

  Color _entryColor(Map<String, dynamic> e) {
    if (e['type'] == 'directory') return const Color(0xFFFFAA00);
    switch ((e['extension'] as String? ?? '').toLowerCase()) {
      case '.py': return const Color(0xFF4488FF);
      case '.dart': return const Color(0xFF7B6CF6);
      case '.js': case '.ts': return const Color(0xFFFFDD00);
      case '.json': return const Color(0xFF00FF88);
      case '.md': return const Color(0xFFCCCCFF);
      case '.txt': return const Color(0xFFCCCCCC);
      case '.pdf': return const Color(0xFFFF6644);
      case '.png': case '.jpg': case '.jpeg': case '.gif':
        return const Color(0xFFFF88CC);
      case '.mp4': case '.mkv': return const Color(0xFFFF88AA);
      case '.zip': case '.rar': return const Color(0xFFFFBB44);
      default: return const Color(0xFF666688);
    }
  }

  IconData _langIcon(String ext) => _entryIcon({'type': 'file', 'extension': ext});
  Color _langColor(String ext) => _entryColor({'type': 'file', 'extension': ext});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          // Header row
          Container(
            padding: const EdgeInsets.fromLTRB(12, 10, 4, 6),
            child: Row(children: [
              if (_history.isNotEmpty)
                IconButton(
                  icon: const Icon(Icons.arrow_back_ios_new,
                    color: Color(0xFF7B6CF6), size: 18),
                  onPressed: _goBack,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                )
              else
                const SizedBox(width: 4),
              const Icon(Icons.folder_open, color: Color(0xFF7B6CF6), size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  _currentPath.isEmpty
                    ? 'Files'
                    : _currentPath.split('\\').last,
                  style: const TextStyle(color: Color(0xFF7B6CF6),
                    fontSize: 16, fontWeight: FontWeight.bold),
                  overflow: TextOverflow.ellipsis),
              ),
              IconButton(
                icon: const Icon(Icons.refresh,
                  color: Color(0xFF555577), size: 20),
                onPressed: () => _loadDir(_currentPath),
                tooltip: 'Refresh',
              ),
              if (_currentPath.isNotEmpty)
                IconButton(
                  icon: const Icon(Icons.add,
                    color: Color(0xFF7B6CF6), size: 22),
                  onPressed: _showNewItemDialog,
                  tooltip: 'New file/folder',
                ),
            ]),
          ),

          // Breadcrumb path
          if (_currentPath.isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 6),
              child: Text(
                _currentPath,
                style: const TextStyle(color: Color(0xFF444466), fontSize: 10),
                overflow: TextOverflow.ellipsis),
            ),

          const Divider(color: Color(0xFF1A1A2E), height: 1),

          // Body
          Expanded(
            child: _loading
              ? const Center(child: CircularProgressIndicator(
                  color: Color(0xFF7B6CF6)))
              : _error.isNotEmpty
                ? Center(child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.wifi_off,
                          color: Color(0xFF555577), size: 48),
                        const SizedBox(height: 16),
                        Text(_error,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            color: Color(0xFF888899), fontSize: 12)),
                        const SizedBox(height: 20),
                        ElevatedButton(
                          onPressed: () => _loadDir(_currentPath),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF7B6CF6),
                            foregroundColor: Colors.black),
                          child: const Text('Retry'),
                        ),
                      ],
                    )))
                : _entries.isEmpty
                  ? const Center(child: Text('Empty',
                      style: TextStyle(color: Color(0xFF555577))))
                  : ListView.builder(
                      itemCount: _entries.length,
                      itemBuilder: (_, i) {
                        final e = _entries[i];
                        final isDir = e['type'] == 'directory';
                        return Dismissible(
                          key: Key(e['path'] as String),
                          direction: DismissDirection.endToStart,
                          confirmDismiss: (_) async {
                            await _confirmDelete(e);
                            return false;
                          },
                          background: Container(
                            alignment: Alignment.centerRight,
                            padding: const EdgeInsets.only(right: 24),
                            color: const Color(0xFF3A0000),
                            child: const Icon(Icons.delete_outline,
                              color: Color(0xFFFF4444)),
                          ),
                          child: ListTile(
                            dense: true,
                            leading: Icon(_entryIcon(e),
                              color: _entryColor(e), size: 22),
                            title: Text(e['name'] as String,
                              style: TextStyle(
                                color: isDir
                                  ? Colors.white
                                  : const Color(0xFFCCCCDD),
                                fontSize: 14,
                                fontWeight: isDir
                                  ? FontWeight.w500
                                  : FontWeight.normal)),
                            trailing: e['size'] != null
                              ? Text(_formatSize(e['size']),
                                  style: const TextStyle(
                                    color: Color(0xFF444466), fontSize: 11))
                              : null,
                            onTap: () => isDir
                              ? _navigate(e['path'] as String)
                              : _openFile(e),
                            onLongPress: () => _confirmDelete(e),
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
