"""
MODULE — Folder Watcher
Daemon thread: watches nova_inbox/ for new files.
On new file detected → triggers AssignmentManager.process_file()
Uses: watchdog library
"""

import threading
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class _AssignmentFileHandler(FileSystemEventHandler):

    WAIT_SECONDS = 2  # wait for file write to complete before parsing

    def __init__(self, assignment_manager, processed_files: set):
        super().__init__()
        self.manager = assignment_manager
        self.processed = processed_files
        self._pending_lock = threading.Lock()

    def on_created(self, event):
        if event.is_directory:
            return
        path = event.src_path
        ext = Path(path).suffix.lower()
        allowed = {'.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg'}
        if ext not in allowed:
            return
        # Avoid double-processing
        with self._pending_lock:
            if path in self.processed:
                return
            self.processed.add(path)
        # Short delay — let the OS finish writing the file
        time.sleep(self.WAIT_SECONDS)
        # Run in a new thread so watchdog handler returns quickly
        threading.Thread(
            target=self.manager.process_file,
            args=(path,),
            daemon=True
        ).start()


class FolderWatcher:

    def __init__(self, inbox_path: str, assignment_manager):
        self.inbox = Path(inbox_path)
        self.inbox.mkdir(exist_ok=True)
        self.manager = assignment_manager
        self._processed: set = set()
        self._observer = None
        self._stop_event = threading.Event()

    def start(self):
        handler = _AssignmentFileHandler(self.manager, self._processed)
        self._observer = Observer()
        self._observer.schedule(handler, str(self.inbox), recursive=False)
        self._observer.start()
        print(f"[FolderWatcher] Watching {self.inbox} for new assignments...")

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()
