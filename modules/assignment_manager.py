"""
MODULE — Assignment Manager
Orchestrator for the full assignment pipeline:
  raw_input → detect → confirm → generate → write → notify
Handles DB logging and interacts with NOVA's voice pipeline.
"""

import os
from modules.document_parser import DocumentParser
from modules.assignment_detector import AssignmentDetector
from modules.assignment_generator import AssignmentGenerator
from modules.document_writer import DocumentWriter


class AssignmentManager:

    def __init__(self, db_manager=None, speak_func=None, listen_func=None, wake_word=None):
        self.db = db_manager
        self.speak = speak_func or print
        self.listen = listen_func
        self.wake_word = wake_word
        self.parser = DocumentParser()
        self.detector = AssignmentDetector()
        self.generator = AssignmentGenerator()
        self.writer = DocumentWriter()

    def process_file(self, file_path: str) -> dict:
        """
        Full pipeline for a detected file.
        Called by FolderWatcher or API endpoint.
        Returns result dict.
        """
        print(f"[AssignmentManager] Processing: {file_path}")

        # Pause background wake word detection to prevent PyAudio resource conflicts
        if self.wake_word:
            self.wake_word.pause()

        try:
            # Step 1: Parse
            parsed = self.parser.parse(file_path)
            if not parsed["success"]:
                self.speak(f"I couldn't read the file: {parsed.get('error', 'Unknown error')}")
                return {"success": False, "error": parsed["error"]}

            # Step 2: Detect
            metadata = self.detector.analyze(parsed["text"])
            if not metadata.get("is_assignment") or metadata.get("confidence", 0) < 0.4:
                self.speak("I analyzed the file but I'm not sure it's an assignment. Let me know if you'd like me to try generating anyway.")
                return {"success": False, "reason": "not_assignment"}

            # Step 3: Notify + confirm
            subject = metadata.get("subject", "Unknown Subject")
            title = metadata.get("title", "Assignment")
            deadline = metadata.get("deadline", "no deadline mentioned")
            self.speak(
                f"New assignment detected. Subject: {subject}. "
                f"Task: {title}. Deadline: {deadline}. "
                f"Shall I generate this assignment?"
            )

            # Step 4: Listen for confirmation
            if self.listen:
                response = self.listen()
                response_lower = response.lower() if response else ""
                confirm_keywords = ["yes", "sure", "go ahead", "do it", "yeah", "generate", "solve", "haan", "jee", "kar do", "start", "please", "okay", "ok", "کر"]
                if response and any(w in response_lower for w in confirm_keywords):
                    pass  # proceed
                else:
                    self.speak("Okay, I'll leave it for now. Say 'generate assignment' when you're ready.")
                    return {"success": False, "reason": "user_declined"}

            # Step 5: Ask for resources (optional)
            resource_paths = []
            if self.listen:
                self.speak("Do you have any lecture notes, slides, or resources? Say 'skip' to continue without them.")
                resource_response = self.listen()
                if resource_response and "skip" not in resource_response.lower():
                    # Resources would be uploaded via app or dropped in inbox separately
                    # For voice: just note intent, actual files handled separately
                    pass

            # Step 6: Ask output format if not specified
            output_format = metadata.get("output_format", "any")
            if output_format == "any":
                if self.listen:
                    self.speak("Should I save it as a PDF or a Word document?")
                    fmt_response = self.listen() or ""
                    output_format = "docx" if "word" in fmt_response.lower() else "pdf"
                else:
                    output_format = "pdf"

            # Step 7: Generate
            self.speak("Generating your assignment. This may take a moment.")
            result = self.generator.generate(
                metadata=metadata,
                resource_paths=resource_paths,
                progress_callback=lambda msg: print(f"[Progress] {msg}")
            )

            if not result["success"]:
                self.speak("I ran into an issue generating the assignment. Please try again.")
                return {"success": False, "error": result.get("error")}

            # Step 8: Write document
            write_result = self.writer.write(
                title=result["title"],
                content=result["content"],
                subject=result["subject"],
                output_format=output_format
            )

            if not write_result["success"]:
                self.speak("Assignment was generated but I couldn't save the file.")
                return {"success": False, "error": write_result.get("error")}

            # Step 9: Log to DB
            if self.db:
                try:
                    self.db.conn.execute(
                        """INSERT INTO assignments (source, raw_text, subject, deadline, output_format, output_path, status)
                           VALUES (?, ?, ?, ?, ?, ?, 'done')""",
                        ("folder", parsed["text"][:500], subject,
                         metadata.get("deadline"), output_format, write_result["path"])
                    )
                    self.db.conn.commit()
                except Exception as dbe:
                    print(f"[AssignmentManager] DB log error: {dbe}")

            # Step 10: Notify
            filename = write_result["filename"]
            word_count = result["word_count"]
            self.speak(
                f"Assignment complete! {word_count} words saved as {filename} in your Nova Outbox folder."
            )
            return {"success": True, "path": write_result["path"],
                    "filename": filename, "word_count": word_count}
        finally:
            if self.wake_word:
                self.wake_word.resume()
