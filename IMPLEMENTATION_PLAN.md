# NOVA AI — Hackathon Feature Implementation Plan

## Feature A: Assignment Auto-Detector & Generator | Feature B: Face-Based Login

**Branch:** `feature/hackathon-sprint` (branched off `akif/week4-dev`)
**Stack:** All free / open-source | Windows-compatible | Python 3.11

---

## Table of Contents

1. [System Pre-Scan Summary](https://claude.ai/chat/fba35779-1d25-4735-8099-dcd6d152e07f#1-system-pre-scan-summary)
2. [Feasibility Analysis](https://claude.ai/chat/fba35779-1d25-4735-8099-dcd6d152e07f#2-feasibility-analysis)
3. [Database Question — SQLite vs Vector DB](https://claude.ai/chat/fba35779-1d25-4735-8099-dcd6d152e07f#3-database-question--sqlite-vs-vector-db)
4. [Feature A: Assignment Pipeline](https://claude.ai/chat/fba35779-1d25-4735-8099-dcd6d152e07f#4-feature-a-assignment-pipeline)
5. [Feature B: Face-Based Login](https://claude.ai/chat/fba35779-1d25-4735-8099-dcd6d152e07f#5-feature-b-face-based-login)
6. [Branch &amp; Commit Strategy](https://claude.ai/chat/fba35779-1d25-4735-8099-dcd6d152e07f#6-branch--commit-strategy)
7. [Testing Protocol](https://claude.ai/chat/fba35779-1d25-4735-8099-dcd6d152e07f#7-testing-protocol)
8. [Risk Register](https://claude.ai/chat/fba35779-1d25-4735-8099-dcd6d152e07f#8-risk-register)

---

## 1. System Pre-Scan Summary

Before writing a single line, here is what the scan of the existing codebase reveals:

| Layer                         | Current State                                   | Impact on New Features                                               |
| ----------------------------- | ----------------------------------------------- | -------------------------------------------------------------------- |
| `nova_core.py`                | Protected by `_route_lock`                      | ✅ Safe — new modules slot in without touching the lock              |
| `modules/api_server.py`       | FastAPI running on port 8000                    | ✅ New endpoints bolt on as plain `def`routes                        |
| `modules/memory_system.py`    | SQLite with WAL mode,`db_singleton`exposed      | ✅ New tables added via `ALTER TABLE`or `CREATE TABLE IF NOT EXISTS` |
| `main.py`                     | Daemon thread launching pattern established     | ✅ New watcher thread follows same daemon pattern                    |
| `nova_app/`                   | Flutter +`novaApi()`client,`shared_preferences` | ✅ New screens follow existing tab pattern                           |
| `modules/coding_assistant.py` | Groq agentic agent with file tools              | ✅ Assignment generator reuses same Groq tool-calling infrastructure |
| `nova_core.route()`           | Routes on intent from NLP engine                | ✅ New intents `"assignment"`and `"face_login"`added to router       |
| Threading                     | 6 threads;`queue.Queue`pattern established      | ✅ Folder watcher and face auth run as daemon threads                |

**Verdict:** Both features are fully addable without breaking existing functionality. The architecture is modular enough that new modules are isolated additions.

---

## 2. Feasibility Analysis

### Feature A — Assignment Pipeline

| Implementation Path                                           | Feasibility                                                             | Verdict             |
| ------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------- |
| **Path 1 — WhatsApp Group Scanner**(Selenium on WhatsApp Web) | Medium — works but fragile; WhatsApp Web layout changes break selectors | ⚠️ Secondary option |
| **Path 2 — Folder Watcher**(watchdog library)                 | High — dead simple, battle-tested, zero fragility                       | ✅**Primary path**  |
| **Mobile Upload → App**                                       | High — uses existing `/api/files/write`endpoint from Alyan's work       | ✅**Mobile path**   |

**Decision:** Implement **Folder Watcher as primary** + **WhatsApp Web scanner as optional secondary** (toggle in `config.json`). Folder watcher is the reliable path for demo. Both paths feed into the same assignment generation pipeline.

### Feature B — Face-Based Login

| Question                          | Answer                                                                              |
| --------------------------------- | ----------------------------------------------------------------------------------- |
| Can SQLite store face embeddings? | ✅ Yes — as BLOB (serialized numpy array, ~5KB per face)                            |
| Do we need a vector DB / RAG?     | ❌ No — with 1-5 registered faces, cosine similarity on raw numpy arrays is instant |
| Which face recognition library?   | `deepface`(multi-backend, free) or `face_recognition`(dlib-based, free)             |
| Works on laptop webcam?           | ✅ Yes via OpenCV (already installed)                                               |
| Works in Flutter app?             | ✅ Phone camera →`/api/auth/face`endpoint → returns JWT-style session token         |
| Fallback if face fails?           | ✅ API key fallback (existing `X-API-Key`method)                                    |

**Decision:** Use `deepface` with `VGG-Face` or `Facenet` backend (free, offline, no API). Store embeddings as BLOB in a new `face_identities` table. Cosine similarity threshold: `0.6`.

---

## 3. Database Question — SQLite vs Vector DB

### Short Answer: **SQLite is perfectly sufficient. No vector DB needed.**

### Why

A vector database (Chroma, Pinecone, Weaviate) is designed for semantic search across millions of high-dimensional vectors. NOVA's use case is:

- Face login: compare 1 new face against ≤ 5 registered identities → brute-force cosine similarity on numpy arrays in under 1ms
- Assignment content: Groq does the semantic understanding, not a vector search engine

**SQLite BLOB storage for face embeddings:**

```python
import numpy as np, pickle, sqlite3

# Store
embedding = np.array([...])   # shape (512,) for Facenet, (128,) for face_recognition
conn.execute("INSERT INTO face_identities (user_name, embedding) VALUES (?, ?)",
             ("Akif", pickle.dumps(embedding)))

# Compare
stored = pickle.loads(row["embedding"])
new    = get_face_embedding(frame)
similarity = np.dot(stored, new) / (np.linalg.norm(stored) * np.linalg.norm(new))
# similarity > 0.6 → same person
```

This is completely feasible in SQLite. No ChromaDB, no Pinecone, no extra service to run.

### New Tables Needed

```sql
-- Feature B: Face Login
CREATE TABLE IF NOT EXISTS face_identities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name   TEXT NOT NULL,
    embedding   BLOB NOT NULL,          -- pickle.dumps(np.array)
    model       TEXT DEFAULT 'Facenet', -- which deepface model was used
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feature A: Assignment tracking
CREATE TABLE IF NOT EXISTS assignments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT,               -- 'folder' | 'whatsapp' | 'mobile_upload'
    raw_text        TEXT,               -- extracted assignment text
    subject         TEXT,
    deadline        TEXT,
    output_format   TEXT,               -- 'pdf' | 'docx'
    output_path     TEXT,
    status          TEXT DEFAULT 'pending',  -- pending | generating | done | failed
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Feature A: Assignment Pipeline

### Architecture Overview

```
INPUT SOURCES (any one)
  ├── Folder Watcher Thread  ──► watches /nova_inbox/ on PC
  ├── WhatsApp Web Scanner   ──► Selenium polls target group (optional)
  └── Mobile Upload          ──► POST /api/assignment/upload

          ↓ (all paths converge here)

AssignmentDetector.analyze(raw_input)
  ├── Document Parser  ──► extract text from PDF/DOCX/image/link
  ├── Subject Classifier  ──► NLP + Groq identify subject & type
  └── Requirement Extractor  ──► deadline, format, word count, rubric

          ↓

NOVA speaks: "New assignment detected: [subject]. Shall I generate it?"

          ↓ (user says yes)

AssignmentGenerator (agentic Groq pipeline)
  ├── Resource Injector  ──► user uploads lecture notes, slides (optional)
  ├── Web Researcher  ──► Groq web-search-style queries + Wikipedia
  └── Document Writer  ──► produces answer, humanizes tone, formats document

          ↓

OutputWriter
  ├── PDF → fpdf2 / reportlab
  └── DOCX → python-docx
  → saves to /nova_outbox/[timestamp]_[subject].pdf|docx

NOVA speaks: "Assignment ready: AI_Assignment.pdf saved to Nova Outbox"
Mobile: file available at GET /api/assignment/download/{id}
```

---

### Sub-Tasks — Feature A

---

#### A-T0 — Branch & Dependencies Setup

**Goal:** Create the hackathon branch, install all new dependencies without touching existing ones.

**Steps:**

```bash
# Create hackathon branch from latest dev branch
git checkout akif/week4-dev
git pull origin akif/week4-dev
git checkout -b feature/hackathon-sprint
```

**New pip dependencies to add to `requirements.txt`:**

```
# Feature A — Assignment Pipeline
watchdog==4.0.1            # folder watcher
PyMuPDF==1.24.3            # PDF text extraction (fitz)
python-docx==1.1.2         # Word doc read/write
pytesseract==0.3.10        # OCR for image-based assignments
Pillow==10.2.0             # already installed — image handling
fpdf2==2.7.9               # PDF generation output
reportlab==4.2.0           # alternative PDF generation
beautifulsoup4==4.12.3     # scrape web resources
selenium==4.18.1           # already installed — WhatsApp scanner
langdetect==1.0.9          # detect assignment language

# Feature B — Face Login
deepface==0.0.93           # face recognition (multi-backend)
tf-keras==2.16.0           # deepface backend dependency
```

**Install:**

```bash
pip install watchdog PyMuPDF python-docx pytesseract fpdf2 reportlab beautifulsoup4 langdetect deepface tf-keras
```

**Config additions to `config.json`:**

```json
"assignment_pipeline": {
  "enabled": true,
  "inbox_folder": "nova_inbox",
  "outbox_folder": "nova_outbox",
  "whatsapp_scanner_enabled": false,
  "whatsapp_target_group": "Class Group",
  "whatsapp_poll_interval_seconds": 30,
  "auto_generate_on_detect": false,
  "default_output_format": "pdf",
  "max_pages": 10,
  "humanize_tone": true
},
"face_login": {
  "enabled": true,
  "model": "Facenet",
  "similarity_threshold": 0.6,
  "registration_samples": 5,
  "camera_index": 0
}
```

**Create folders on startup:**

```python
os.makedirs("nova_inbox", exist_ok=True)
os.makedirs("nova_outbox", exist_ok=True)
```

**Verification:**

- [ ] Branch `feature/hackathon-sprint` created
- [ ] All packages install without errors
- [ ] `python main.py` still runs perfectly after installs
- [ ] `nova_inbox/` and `nova_outbox/` created on startup

---

#### A-T1 — Document Parser Module (`modules/document_parser.py`)

**Goal:** Extract clean text from any assignment format — PDF, DOCX, image (OCR), plain text, URL.

**File:** `modules/document_parser.py`

```python
"""
MODULE — Document Parser
Extracts clean text from: PDF, DOCX, images (OCR), plain text files, URLs.
Used by AssignmentDetector to normalize any input format into a text string.
"""

import os
import fitz          # PyMuPDF
import docx
import pytesseract
from PIL import Image
import requests
from bs4 import BeautifulSoup
from pathlib import Path


class DocumentParser:

    SUPPORTED_EXTENSIONS = {
        '.pdf': '_parse_pdf',
        '.docx': '_parse_docx',
        '.doc': '_parse_docx',
        '.txt': '_parse_txt',
        '.png': '_parse_image',
        '.jpg': '_parse_image',
        '.jpeg': '_parse_image',
        '.bmp': '_parse_image',
    }

    def parse(self, source: str) -> dict:
        """
        Main entry point.
        source: file path OR URL string
        Returns: {"text": str, "source_type": str, "filename": str, "success": bool}
        """
        source = source.strip()

        if source.startswith("http://") or source.startswith("https://"):
            return self._parse_url(source)

        path = Path(source)
        if not path.exists():
            return {"success": False, "text": "", "source_type": "unknown",
                    "filename": source, "error": "File not found"}

        ext = path.suffix.lower()
        method_name = self.SUPPORTED_EXTENSIONS.get(ext)

        if not method_name:
            return {"success": False, "text": "", "source_type": ext,
                    "filename": path.name, "error": f"Unsupported file type: {ext}"}

        try:
            text = getattr(self, method_name)(str(path))
            return {"success": True, "text": text.strip(), "source_type": ext,
                    "filename": path.name, "error": None}
        except Exception as e:
            return {"success": False, "text": "", "source_type": ext,
                    "filename": path.name, "error": str(e)}

    def _parse_pdf(self, path: str) -> str:
        doc = fitz.open(path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)

    def _parse_docx(self, path: str) -> str:
        doc = docx.Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

    def _parse_txt(self, path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _parse_image(self, path: str) -> str:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        return text

    def _parse_url(self, url: str) -> dict:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return {"success": True, "text": text[:8000], "source_type": "url",
                    "filename": url, "error": None}
        except Exception as e:
            return {"success": False, "text": "", "source_type": "url",
                    "filename": url, "error": str(e)}
```

**Verification:**

- [ ] `parser.parse("assignment.pdf")` returns correct text
- [ ] `parser.parse("assignment.docx")` returns correct text
- [ ] `parser.parse("photo.jpg")` runs pytesseract and returns OCR text
- [ ] `parser.parse("https://example.com/task.html")` returns webpage text
- [ ] Unknown extension returns `success: False` with error message

---

#### A-T2 — Assignment Detector Module (`modules/assignment_detector.py`)

**Goal:** Given raw extracted text, use Groq to identify: subject, requirements, deadline, word count, output format, and whether it's actually an assignment.

**File:** `modules/assignment_detector.py`

````python
"""
MODULE — Assignment Detector
Uses Groq to analyze extracted document text and determine:
- Is this an assignment? (confidence score)
- Subject / course name
- What is being asked
- Deadline (if mentioned)
- Required output format (pdf/docx/any)
- Word/page count requirement
- Any additional constraints
Returns a structured dict for the AssignmentGenerator.
"""

import os, json
from groq import Groq


_DETECT_PROMPT = """You are an academic assistant. Analyze the following text and determine if it is a university assignment or task.

Return ONLY a JSON object (no markdown, no explanation) with these exact fields:
{
  "is_assignment": true/false,
  "confidence": 0.0-1.0,
  "subject": "course/subject name or 'Unknown'",
  "assignment_type": "essay|report|code|problem_set|presentation|lab_report|other",
  "title": "short assignment title",
  "requirements": "full clear description of what needs to be done",
  "deadline": "extracted deadline string or null",
  "word_count": "e.g. '1000 words' or null",
  "page_count": "e.g. '5 pages' or null",
  "output_format": "pdf|docx|any",
  "special_instructions": "any formatting rules, citation style, headings required, etc."
}"""


class AssignmentDetector:

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

    def analyze(self, text: str) -> dict:
        """
        Analyze extracted text. Returns structured assignment metadata dict.
        """
        if not text or len(text.strip()) < 20:
            return {"is_assignment": False, "confidence": 0.0}

        # Cap text to avoid token overuse
        trimmed = text[:3000]

        try:
            resp = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": _DETECT_PROMPT},
                    {"role": "user", "content": f"TEXT TO ANALYZE:\n\n{trimmed}"}
                ],
                temperature=0.1,
                max_tokens=512,
            )
            raw = resp.choices[0].message.content.strip()
            # Strip markdown fences if any
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)
            return result
        except json.JSONDecodeError:
            # Fallback: return minimal structure
            return {"is_assignment": True, "confidence": 0.5,
                    "subject": "Unknown", "requirements": text[:500],
                    "output_format": "pdf", "title": "Detected Assignment"}
        except Exception as e:
            print(f"[AssignmentDetector] Error: {e}")
            return {"is_assignment": False, "confidence": 0.0, "error": str(e)}
````

**Verification:**

- [ ] Groq correctly identifies an assignment text with `is_assignment: true`
- [ ] Returns correct subject for "Write a 1000-word essay on TCP/IP for Computer Networks"
- [ ] Returns `is_assignment: false` for a random paragraph of text
- [ ] Handles JSON parse failures gracefully with fallback

---

#### A-T3 — Assignment Generator Module (`modules/assignment_generator.py`)

**Goal:** Agentic Groq pipeline that takes assignment metadata + optional user resources and produces a complete, humanized assignment text, ready for document writing.

**File:** `modules/assignment_generator.py`

```python
"""
MODULE — Assignment Generator
Agentic Groq pipeline:
1. Receives assignment metadata from AssignmentDetector
2. Optionally receives user-provided resources (lecture notes, slides)
3. Searches web for supporting content (Wikipedia + web requests)
4. Generates a complete, humanized assignment
5. Returns structured content ready for DocumentWriter
"""

import os, time, requests
from groq import Groq
from modules.document_parser import DocumentParser

_SYSTEM_PROMPT = """You are an expert academic writer helping a university student.
Your writing must be:
- Clear, well-structured, and academically appropriate
- Humanized — natural student tone, NOT obviously AI-generated
- Properly formatted with headings, introduction, body, conclusion
- Factually accurate, with specific examples where appropriate
- Concise — stick to the word/page count if specified
Do NOT use phrases like "In conclusion, it is evident that..." or "This essay will explore..."
Write like an intelligent, well-read student, not a corporate report generator."""


class AssignmentGenerator:

    HISTORY_WINDOW = 10

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
        self.parser = DocumentParser()

    def generate(self, metadata: dict, resource_paths: list = None,
                 progress_callback=None) -> dict:
        """
        Main generation pipeline.
        metadata: output from AssignmentDetector.analyze()
        resource_paths: list of file paths user provided (lecture notes, slides)
        progress_callback: called with status strings (for HUD / app updates)
        Returns: {"title": str, "content": str, "word_count": int, "success": bool}
        """

        def update(msg):
            print(f"[AssignmentGenerator] {msg}")
            if progress_callback:
                progress_callback(msg)

        update("Analyzing assignment requirements...")

        # Step 1: Extract resource content
        resource_text = ""
        if resource_paths:
            update(f"Loading {len(resource_paths)} resource(s)...")
            for path in resource_paths:
                result = self.parser.parse(path)
                if result["success"]:
                    resource_text += f"\n\n--- RESOURCE: {result['filename']} ---\n{result['text'][:3000]}"

        # Step 2: Build a focused research query
        subject = metadata.get("subject", "General")
        requirements = metadata.get("requirements", "Complete the assignment.")
        title = metadata.get("title", "Assignment")
        word_count = metadata.get("word_count", "500-800 words")
        special = metadata.get("special_instructions", "")

        # Step 3: Optional web research (Wikipedia)
        research_text = ""
        try:
            update("Researching topic online...")
            import wikipedia
            query = f"{subject} {title}"
            summary = wikipedia.summary(query, sentences=8)
            research_text = f"\n\n--- WEB RESEARCH: Wikipedia ---\n{summary}"
        except Exception:
            pass

        # Step 4: Build generation prompt
        context_block = ""
        if resource_text:
            context_block += f"\n\nUSER-PROVIDED RESOURCES:\n{resource_text[:4000]}"
        if research_text:
            context_block += research_text

        user_prompt = f"""Assignment Title: {title}
Subject: {subject}
What to do: {requirements}
Word count: {word_count}
Special instructions: {special}
{context_block}

Now write the complete, well-structured assignment. Include proper headings.
Use the resources and research provided where relevant. Do not copy verbatim — paraphrase and synthesize."""

        # Step 5: Generate
        update("Generating assignment content...")
        try:
            for attempt in range(3):
                try:
                    resp = self.client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": _SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=3000,
                    )
                    content = resp.choices[0].message.content.strip()
                    word_count_actual = len(content.split())
                    update(f"Assignment generated — {word_count_actual} words.")
                    return {"title": title, "content": content,
                            "word_count": word_count_actual, "success": True,
                            "subject": subject}
                except Exception as e:
                    if "rate_limit" in str(e).lower():
                        time.sleep(2 ** attempt)
                    else:
                        raise
        except Exception as e:
            print(f"[AssignmentGenerator] Generation failed: {e}")
            return {"title": title, "content": "", "word_count": 0,
                    "success": False, "error": str(e)}
```

**Verification:**

- [ ] Given a CS assignment prompt, generates 500+ word coherent text
- [ ] With a resource file provided, incorporates content from it
- [ ] Wikipedia research runs silently and augments the content
- [ ] Rate limit retry works (3 attempts with backoff)
- [ ] `success: False` returned cleanly on API error

---

#### A-T4 — Document Writer Module (`modules/document_writer.py`)

**Goal:** Takes the generated assignment text and writes a properly formatted PDF or DOCX file to `nova_outbox/`.

**File:** `modules/document_writer.py`

```python
"""
MODULE — Document Writer
Takes generated assignment content and produces:
- PDF output via fpdf2
- DOCX output via python-docx
Saves to nova_outbox/ with timestamped filename.
"""

import os
from datetime import datetime
from pathlib import Path
from fpdf import FPDF
import docx as _docx


class DocumentWriter:

    def __init__(self, outbox_path: str = "nova_outbox"):
        self.outbox = Path(outbox_path)
        self.outbox.mkdir(exist_ok=True)

    def write(self, title: str, content: str, subject: str,
              output_format: str = "pdf") -> dict:
        """
        Write the assignment to disk.
        Returns: {"success": bool, "path": str, "filename": str}
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_subject = "".join(c for c in subject if c.isalnum() or c in " _").strip().replace(" ", "_")
        filename_base = f"{timestamp}_{safe_subject}_Assignment"

        if output_format.lower() == "docx":
            return self._write_docx(title, content, filename_base)
        else:
            return self._write_pdf(title, content, filename_base)

    def _write_pdf(self, title: str, content: str, filename_base: str) -> dict:
        try:
            pdf = FPDF()
            pdf.set_margins(20, 20, 20)
            pdf.add_page()

            # Title
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(0, 10, title, align="C")
            pdf.ln(8)

            # Horizontal line
            pdf.set_draw_color(100, 100, 100)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)

            # Body — parse headings (lines starting with # or ALL CAPS short lines)
            pdf.set_font("Helvetica", "", 11)
            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    pdf.ln(4)
                    continue
                if line.startswith("## ") or line.startswith("# "):
                    pdf.set_font("Helvetica", "B", 13)
                    pdf.multi_cell(0, 8, line.lstrip("# ").strip())
                    pdf.set_font("Helvetica", "", 11)
                    pdf.ln(2)
                elif line.startswith("**") and line.endswith("**"):
                    pdf.set_font("Helvetica", "B", 11)
                    pdf.multi_cell(0, 7, line.strip("*"))
                    pdf.set_font("Helvetica", "", 11)
                else:
                    pdf.multi_cell(0, 7, line)

            filepath = str(self.outbox / f"{filename_base}.pdf")
            pdf.output(filepath)
            return {"success": True, "path": filepath,
                    "filename": f"{filename_base}.pdf", "format": "pdf"}
        except Exception as e:
            return {"success": False, "error": str(e), "path": "", "filename": ""}

    def _write_docx(self, title: str, content: str, filename_base: str) -> dict:
        try:
            doc = _docx.Document()
            doc.add_heading(title, 0)

            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    doc.add_paragraph("")
                    continue
                if line.startswith("## "):
                    doc.add_heading(line[3:], level=2)
                elif line.startswith("# "):
                    doc.add_heading(line[2:], level=1)
                else:
                    doc.add_paragraph(line)

            filepath = str(self.outbox / f"{filename_base}.docx")
            doc.save(filepath)
            return {"success": True, "path": filepath,
                    "filename": f"{filename_base}.docx", "format": "docx"}
        except Exception as e:
            return {"success": False, "error": str(e), "path": "", "filename": ""}
```

**Verification:**

- [ ] PDF file created with correct title heading and body paragraphs
- [ ] DOCX file created with heading styles matching # markers
- [ ] Files saved to `nova_outbox/` with timestamp prefix
- [ ] PDF opens correctly in Adobe Reader / browser
- [ ] DOCX opens correctly in Word / LibreOffice

---

#### A-T5 — Assignment Manager (`modules/assignment_manager.py`)

**Goal:** Orchestrator that ties all A-modules together. Handles the full pipeline from raw input to finished file. Also manages DB logging and NOVA voice flow.

**File:** `modules/assignment_manager.py`

```python
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

    def __init__(self, db_manager=None, speak_func=None, listen_func=None):
        self.db = db_manager
        self.speak = speak_func or print
        self.listen = listen_func
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
            if response and any(w in response.lower() for w in ["yes", "sure", "go ahead", "do it", "yeah"]):
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
            self.db.conn.execute(
                """INSERT INTO assignments (source, raw_text, subject, deadline, output_format, output_path, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'done')""",
                ("folder", parsed["text"][:500], subject,
                 metadata.get("deadline"), output_format, write_result["path"])
            )
            self.db.conn.commit()

        # Step 10: Notify
        filename = write_result["filename"]
        word_count = result["word_count"]
        self.speak(
            f"Assignment complete! {word_count} words saved as {filename} in your Nova Outbox folder."
        )
        return {"success": True, "path": write_result["path"],
                "filename": filename, "word_count": word_count}
```

**Verification:**

- [ ] Full pipeline runs end-to-end with a sample PDF assignment
- [ ] NOVA speaks correctly at each stage
- [ ] User confirmation ("yes" / "no") routes correctly
- [ ] Output file appears in `nova_outbox/` after completion
- [ ] DB row inserted with correct fields

---

#### A-T6 — Folder Watcher Thread (`modules/folder_watcher.py`)

**Goal:** Background daemon thread that watches `nova_inbox/` for new files and triggers the assignment pipeline.

**File:** `modules/folder_watcher.py`

```python
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
```

**Integration in `main.py`:**

```python
# After existing thread launches, add:
from modules.assignment_manager import AssignmentManager
from modules.folder_watcher import FolderWatcher

assignment_manager = AssignmentManager(
    db_manager=db_manager,
    speak_func=speak,
    listen_func=lambda: stt.transcribe(stt.listen())
)
folder_watcher = FolderWatcher(
    inbox_path=config.get("assignment_pipeline", {}).get("inbox_folder", "nova_inbox"),
    assignment_manager=assignment_manager
)
folder_watcher.start()
# In shutdown: folder_watcher.stop()
```

**Verification:**

- [ ] Drop a PDF file into `nova_inbox/` → NOVA speaks the detection message within 3 seconds
- [ ] Drop a `.txt` file with assignment text → pipeline triggers correctly
- [ ] Drop a `.zip` file → ignored (not in allowed extensions)
- [ ] Drop the same file twice → not processed twice (dedup set)
- [ ] Watcher survives `nova_inbox/` being empty for extended periods

---

#### A-T7 — WhatsApp Group Scanner (`modules/whatsapp_scanner.py`)

**Goal:** Optional secondary input path — Selenium polls a named WhatsApp Web group for new messages matching assignment keywords.

**File:** `modules/whatsapp_scanner.py`

```python
"""
MODULE — WhatsApp Group Scanner (OPTIONAL)
Polls a target WhatsApp Web group for new messages.
Triggers assignment pipeline when assignment keywords are detected.
Requires: WhatsApp Web active in Chrome, Selenium ChromeDriver on PATH.
Toggle: config.json -> assignment_pipeline.whatsapp_scanner_enabled
"""

import time
import threading
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


ASSIGNMENT_KEYWORDS = [
    "assignment", "task", "homework", "project", "submit", "due date",
    "deadline", "report", "essay", "lab report", "quiz", "exam",
    "تکلیف", "کام", "پراجیکٹ"  # Urdu keywords for Pakistani classrooms
]


class WhatsAppGroupScanner:

    def __init__(self, target_group: str, assignment_manager,
                 poll_interval: int = 30):
        self.group_name = target_group
        self.manager = assignment_manager
        self.interval = poll_interval
        self._stop = threading.Event()
        self._seen_messages: set = set()
        self.driver = None

    def _init_driver(self):
        opts = Options()
        opts.add_argument("--user-data-dir=whatsapp_session")
        opts.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=opts)
        self.driver.get("https://web.whatsapp.com")
        print("[WhatsAppScanner] Please scan QR code if not already logged in...")
        time.sleep(15)  # give user time to scan QR

    def _find_group_and_scan(self):
        try:
            # Find group in sidebar
            search = self.driver.find_element(
                By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'
            )
            search.clear()
            search.send_keys(self.group_name)
            time.sleep(2)
            # Click the group
            group = self.driver.find_element(
                By.XPATH, f'//span[@title="{self.group_name}"]'
            )
            group.click()
            time.sleep(1.5)
            # Get last few messages
            msgs = self.driver.find_elements(
                By.CSS_SELECTOR, "div.message-in .copyable-text span.selectable-text"
            )
            for msg_el in msgs[-10:]:  # check last 10 messages
                text = msg_el.text.strip()
                if not text or text in self._seen_messages:
                    continue
                self._seen_messages.add(text)
                if any(kw.lower() in text.lower() for kw in ASSIGNMENT_KEYWORDS):
                    print(f"[WhatsAppScanner] Assignment message detected: {text[:100]}")
                    # Save as temp txt and pass to manager
                    import tempfile, os
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                                     delete=False, encoding='utf-8') as f:
                        f.write(text)
                        tmp_path = f.name
                    threading.Thread(
                        target=self.manager.process_file,
                        args=(tmp_path,),
                        daemon=True
                    ).start()
        except Exception as e:
            print(f"[WhatsAppScanner] Error scanning group: {e}")

    def _scan_loop(self):
        self._init_driver()
        while not self._stop.is_set():
            self._find_group_and_scan()
            self._stop.wait(timeout=self.interval)
        if self.driver:
            self.driver.quit()

    def start(self):
        t = threading.Thread(target=self._scan_loop, daemon=True,
                              name="WhatsAppScannerThread")
        t.start()
        print(f"[WhatsAppScanner] Started — scanning group: '{self.group_name}'")

    def stop(self):
        self._stop.set()
```

**Verification:**

- [ ] Scanner starts and opens WhatsApp Web in Chrome
- [ ] Message with word "assignment" in target group triggers pipeline
- [ ] Messages already seen are not reprocessed (`_seen_messages` dedup)
- [ ] Scanner disabled cleanly when `whatsapp_scanner_enabled: false` in config
- [ ] No crash when WhatsApp Web is not logged in (waits for QR)

---

#### A-T8 — Assignment API Endpoints (add to `modules/api_server.py`)

**Goal:** Expose assignment pipeline through the REST API so the Flutter app can upload assignments, check status, and download output files.

**Add to `modules/api_server.py`:**

```python
# ── Assignment Pipeline Endpoints ────────────────────────────────

from fastapi import UploadFile, File
from fastapi.responses import FileResponse
import shutil, tempfile

class AssignmentUploadResponse(BaseModel):
    status: str
    assignment_id: int = None
    message: str = ""

@app.post("/api/assignment/upload")
def upload_assignment(file: UploadFile = File(...),
                      _auth: str = Depends(_require_auth)):
    """Mobile upload path — user uploads assignment file from phone."""
    inbox = Path("nova_inbox")
    inbox.mkdir(exist_ok=True)
    dest = inbox / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # FolderWatcher will pick this up automatically
    return {"status": "received", "message": f"File {file.filename} queued for processing."}

@app.get("/api/assignment/status")
def get_assignment_status(_auth: str = Depends(_require_auth)):
    """Returns the last 5 assignment records from DB."""
    try:
        from modules.memory_system import db_singleton
        rows = db_singleton.conn.execute(
            "SELECT id, subject, title, status, output_path, created_at "
            "FROM assignments ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        results = [dict(r) for r in rows]
        return {"assignments": results}
    except Exception as e:
        return {"assignments": [], "error": str(e)}

@app.get("/api/assignment/download/{assignment_id}")
def download_assignment(assignment_id: int, _auth: str = Depends(_require_auth)):
    """Download a completed assignment file."""
    try:
        from modules.memory_system import db_singleton
        row = db_singleton.conn.execute(
            "SELECT output_path, output_format FROM assignments WHERE id = ?",
            (assignment_id,)
        ).fetchone()
        if not row or not row["output_path"]:
            raise HTTPException(404, "Assignment not found or not yet complete.")
        path = Path(row["output_path"])
        if not path.exists():
            raise HTTPException(404, "Output file missing from disk.")
        media_type = "application/pdf" if str(path).endswith(".pdf") else \
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return FileResponse(str(path), media_type=media_type,
                            filename=path.name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
```

**Flutter additions (in `nova_app/`):**

New screen: `nova_app/lib/screens/home/assignment_tab.dart`

```
Features:
- Upload assignment button (file picker → POST /api/assignment/upload)
- Status card showing in-progress / done assignments
- Download button for completed assignments
- Assignment history list
```

**Verification:**

- [ ] `POST /api/assignment/upload` with a PDF file → `nova_inbox/` receives it → watcher triggers
- [ ] `GET /api/assignment/status` returns last 5 assignments from DB
- [ ] `GET /api/assignment/download/1` returns the output file for download
- [ ] Flutter upload button correctly POSTs multipart file
- [ ] Assignment appears in Flutter history list after completion

---

## 5. Feature B: Face-Based Login

### Architecture Overview

```
REGISTRATION FLOW (once):
  webcam/phone camera → capture 5 frames → deepface.represent()
  → 5 embeddings → average to 1 mean embedding → BLOB in face_identities table

LOGIN FLOW (each session):
  PC: webcam auto-scan at app startup → deepface.represent(frame)
      → cosine similarity vs stored embedding → > 0.6 → session token granted

  Mobile: camera frame → POST /api/auth/face → same comparison on server
          → returns {"authenticated": true, "token": "..."} or 401

  Web: camera frame via JS → POST /api/auth/face → same

FALLBACK:
  Face fails 3× → fall back to API key entry (existing X-API-Key method)
```

---

### Sub-Tasks — Feature B

---

#### B-T0 — Database Migration for Face Identities

**Add to `modules/memory_system.py` `_create_tables()` method:**

```python
self.conn.execute("""
    CREATE TABLE IF NOT EXISTS face_identities (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name   TEXT NOT NULL,
        embedding   BLOB NOT NULL,
        model       TEXT DEFAULT 'Facenet',
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
self.conn.execute("""
    CREATE TABLE IF NOT EXISTS face_sessions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        token       TEXT NOT NULL,
        user_name   TEXT NOT NULL,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at  TIMESTAMP NOT NULL
    )
""")
```

**Verification:**

- [ ] `data/memory.db` has both new tables after migration
- [ ] No errors on existing DB (uses `CREATE TABLE IF NOT EXISTS`)

---

#### B-T1 — Face Auth Module (`modules/face_auth.py`)

**Goal:** Registration and verification logic using deepface. SQLite BLOB storage for embeddings.

**File:** `modules/face_auth.py`

```python
"""
MODULE — Face Authentication
Registration: capture N face samples → average embedding → store in DB as BLOB
Verification: capture frame → compare vs stored embedding → cosine similarity
No cloud, no API, fully local using deepface.
"""

import cv2
import numpy as np
import pickle
import os
import secrets
from datetime import datetime, timedelta
from deepface import DeepFace


class FaceAuth:

    MODEL = "Facenet"              # Free, offline, ~90MB model download on first use
    SIMILARITY_THRESHOLD = 0.6    # Cosine similarity — > 0.6 = same person
    REGISTRATION_SAMPLES = 5      # Capture 5 frames, average embeddings
    SESSION_HOURS = 24

    def __init__(self, db_manager, camera_index: int = 0):
        self.db = db_manager
        self.cam_index = camera_index

    # ── Embedding utilities ──────────────────────────────────────

    def _get_embedding(self, frame: np.ndarray) -> np.ndarray | None:
        """Extract face embedding from a single frame. Returns None if no face found."""
        try:
            result = DeepFace.represent(
                img_path=frame,
                model_name=self.MODEL,
                enforce_detection=True,
                detector_backend="opencv"
            )
            return np.array(result[0]["embedding"])
        except Exception:
            return None

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    # ── DB utilities ─────────────────────────────────────────────

    def _store_embedding(self, user_name: str, embedding: np.ndarray):
        blob = pickle.dumps(embedding)
        self.db.conn.execute(
            "INSERT INTO face_identities (user_name, embedding, model) VALUES (?, ?, ?)",
            (user_name, blob, self.MODEL)
        )
        self.db.conn.commit()

    def _load_embedding(self, user_name: str) -> np.ndarray | None:
        row = self.db.conn.execute(
            "SELECT embedding FROM face_identities WHERE user_name = ? ORDER BY created_at DESC LIMIT 1",
            (user_name,)
        ).fetchone()
        if not row:
            return None
        return pickle.loads(row["embedding"])

    def is_registered(self, user_name: str) -> bool:
        row = self.db.conn.execute(
            "SELECT id FROM face_identities WHERE user_name = ?", (user_name,)
        ).fetchone()
        return row is not None

    # ── Registration ─────────────────────────────────────────────

    def register_from_webcam(self, user_name: str,
                              progress_callback=None) -> dict:
        """
        Opens webcam, captures REGISTRATION_SAMPLES frames with a face,
        averages the embeddings, stores in DB.
        """
        cap = cv2.VideoCapture(self.cam_index)
        if not cap.isOpened():
            return {"success": False, "error": "Camera not accessible."}

        embeddings = []
        attempts = 0
        max_attempts = 50  # try up to 50 frames to collect 5 good ones

        if progress_callback:
            progress_callback(f"Look at the camera. Collecting {self.REGISTRATION_SAMPLES} samples...")

        while len(embeddings) < self.REGISTRATION_SAMPLES and attempts < max_attempts:
            ret, frame = cap.read()
            if not ret:
                attempts += 1
                continue
            emb = self._get_embedding(frame)
            if emb is not None:
                embeddings.append(emb)
                if progress_callback:
                    progress_callback(f"Sample {len(embeddings)}/{self.REGISTRATION_SAMPLES} captured.")
            attempts += 1

        cap.release()

        if len(embeddings) < 3:
            return {"success": False,
                    "error": "Could not capture enough clear face samples. Ensure good lighting."}

        mean_embedding = np.mean(embeddings, axis=0)
        self._store_embedding(user_name, mean_embedding)
        return {"success": True,
                "message": f"Face registered for {user_name} ({len(embeddings)} samples)."}

    def register_from_frame(self, user_name: str, frame: np.ndarray) -> dict:
        """Register from a single frame (e.g., from phone camera via API)."""
        emb = self._get_embedding(frame)
        if emb is None:
            return {"success": False, "error": "No face detected in frame."}
        self._store_embedding(user_name, emb)
        return {"success": True, "message": f"Face registered for {user_name}."}

    # ── Verification ─────────────────────────────────────────────

    def verify_from_webcam(self, user_name: str) -> dict:
        """Verify identity from a single webcam capture."""
        cap = cv2.VideoCapture(self.cam_index)
        if not cap.isOpened():
            return {"authenticated": False, "error": "Camera not accessible."}

        for _ in range(20):  # try 20 frames
            ret, frame = cap.read()
            if not ret:
                continue
            emb = self._get_embedding(frame)
            if emb is not None:
                cap.release()
                return self._compare(user_name, emb)

        cap.release()
        return {"authenticated": False, "error": "Could not detect a face."}

    def verify_from_frame(self, user_name: str, frame: np.ndarray) -> dict:
        """Verify from a numpy frame (from API upload)."""
        emb = self._get_embedding(frame)
        if emb is None:
            return {"authenticated": False, "error": "No face detected."}
        return self._compare(user_name, emb)

    def _compare(self, user_name: str, new_embedding: np.ndarray) -> dict:
        stored = self._load_embedding(user_name)
        if stored is None:
            return {"authenticated": False,
                    "error": f"No face registered for '{user_name}'. Please register first."}
        similarity = self._cosine_similarity(stored, new_embedding)
        authenticated = similarity >= self.SIMILARITY_THRESHOLD
        return {
            "authenticated": authenticated,
            "similarity": round(similarity, 4),
            "threshold": self.SIMILARITY_THRESHOLD,
            "user_name": user_name if authenticated else None
        }

    # ── Session tokens ────────────────────────────────────────────

    def create_session(self, user_name: str) -> str:
        token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(hours=self.SESSION_HOURS)
        self.db.conn.execute(
            "INSERT INTO face_sessions (token, user_name, expires_at) VALUES (?, ?, ?)",
            (token, user_name, expires.isoformat())
        )
        self.db.conn.commit()
        return token

    def validate_session(self, token: str) -> dict:
        row = self.db.conn.execute(
            "SELECT user_name, expires_at FROM face_sessions WHERE token = ?",
            (token,)
        ).fetchone()
        if not row:
            return {"valid": False}
        if datetime.fromisoformat(row["expires_at"]) < datetime.now():
            return {"valid": False, "reason": "expired"}
        return {"valid": True, "user_name": row["user_name"]}
```

**Verification:**

- [ ] `register_from_webcam("Akif")` captures 5 samples and stores BLOB in DB
- [ ] `verify_from_webcam("Akif")` returns `authenticated: true` for correct face
- [ ] `verify_from_webcam("Akif")` with a different face returns `authenticated: false`
- [ ] `cosine_similarity` correctly scores 0.95+ for same person, 0.2-0.4 for different
- [ ] `create_session` → `validate_session` works with correct token

---

#### B-T2 — Face Auth API Endpoints (add to `modules/api_server.py`)

**Goal:** REST endpoints for face registration and login from phone/web.

```python
# ── Face Auth Endpoints ───────────────────────────────────────────

import base64, cv2, numpy as np
from pydantic import BaseModel

class FaceFrameRequest(BaseModel):
    user_name: str
    frame_b64: str     # base64-encoded JPEG frame from phone camera

def _decode_frame(frame_b64: str) -> np.ndarray:
    """Decode base64 image to numpy array."""
    img_bytes = base64.b64decode(frame_b64)
    np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

@app.post("/api/auth/face/register")
def face_register(req: FaceFrameRequest, _auth: str = Depends(_require_auth)):
    """Register a face from a phone/browser camera frame."""
    from modules.memory_system import db_singleton
    from modules.face_auth import FaceAuth
    auth = FaceAuth(db_singleton)
    frame = _decode_frame(req.frame_b64)
    result = auth.register_from_frame(req.user_name, frame)
    return result

@app.post("/api/auth/face/verify")
def face_verify(req: FaceFrameRequest):
    """
    Verify a face. No API key required — this IS the authentication.
    Returns a session token on success.
    """
    from modules.memory_system import db_singleton
    from modules.face_auth import FaceAuth
    auth = FaceAuth(db_singleton)
    frame = _decode_frame(req.frame_b64)
    result = auth.verify_from_frame(req.user_name, frame)
    if result.get("authenticated"):
        token = auth.create_session(req.user_name)
        return {"authenticated": True, "session_token": token,
                "user_name": req.user_name}
    return {"authenticated": False, "similarity": result.get("similarity", 0),
            "message": result.get("error", "Face not recognized.")}

@app.get("/api/auth/face/status")
def face_status(user_name: str, _auth: str = Depends(_require_auth)):
    """Check if a user has a registered face."""
    from modules.memory_system import db_singleton
    from modules.face_auth import FaceAuth
    auth = FaceAuth(db_singleton)
    return {"registered": auth.is_registered(user_name), "user_name": user_name}
```

**Verification:**

- [ ] `POST /api/auth/face/register` with base64 JPEG → face stored in DB
- [ ] `POST /api/auth/face/verify` with correct face → `authenticated: true` + session_token
- [ ] `POST /api/auth/face/verify` with wrong face → `authenticated: false`
- [ ] `POST /api/auth/face/verify` does NOT require X-API-Key header (it IS the auth)
- [ ] `GET /api/auth/face/status?user_name=Akif` returns `registered: true` after registration

---

#### B-T3 — PC Auto-Login at Startup

**Goal:** When NOVA starts on PC, auto-scan webcam for the registered face. If recognized → skip PIN/API key screen. If not → show regular connect screen.

**Add to `main.py` startup sequence:**

```python
# After db_manager init, before HUD launch:

from modules.face_auth import FaceAuth

face_auth_module = FaceAuth(db_manager)
user_name = config.get("user", {}).get("name", "User")

if face_auth_module.is_registered(user_name):
    print("[FaceLogin] Scanning for registered face...")
    auth_result = face_auth_module.verify_from_webcam(user_name)
    if auth_result.get("authenticated"):
        print(f"[FaceLogin] ✅ Welcome back, {user_name}! (similarity: {auth_result['similarity']})")
        # HUD shows welcome message
    else:
        print(f"[FaceLogin] ❌ Face not recognized. Continuing with standard startup.")
else:
    print("[FaceLogin] No face registered. Run registration via app or voice command.")
```

**Voice commands to add to NLP router:**

```
"Register my face"       → face_auth_module.register_from_webcam(user_name)
"Enable face login"      → same
"Who am I?"              → face_auth_module.verify_from_webcam(user_name)
```

**Verification:**

- [ ] On startup, webcam opens and face check runs within 5 seconds
- [ ] Registered face → welcome message in HUD
- [ ] Unregistered → graceful skip, normal startup
- [ ] Camera unavailable → graceful skip, no crash

---

#### B-T4 — Flutter Face Login Screen

**Goal:** Add face-login screen to the Flutter app. Camera frame → `/api/auth/face/verify` → session token stored → skips manual API key entry.

**New file:** `nova_app/lib/screens/face_login_screen.dart`

**Flow:**

```
App opens → check AsyncStorage for face_login_enabled
  ├── Enabled → open camera → capture frame every 1s → POST /api/auth/face/verify
  │     ├── Authenticated → store session_token → navigate to home
  │     └── Failed 3× → show "Use API Key" button → standard connect flow
  └── Disabled → standard connect screen
```

**Key dependencies to add to `pubspec.yaml`:**

```yaml
camera: ^0.10.5+9
```

**Verification:**

- [ ] Camera preview shows on face login screen
- [ ] Face detected within 3 seconds for registered user
- [ ] 3 failures → fallback to API key login
- [ ] Session token persisted in `shared_preferences`
- [ ] Subsequent app opens reuse valid session (no re-scan needed until expiry)

---

## 6. Branch & Commit Strategy

```
main
  └── akif/week4-dev  (current stable)
        └── feature/hackathon-sprint  (new work)
              ├── A-T0: deps + config + DB schema
              ├── A-T1: document_parser.py
              ├── A-T2: assignment_detector.py
              ├── A-T3: assignment_generator.py
              ├── A-T4: document_writer.py
              ├── A-T5: assignment_manager.py
              ├── A-T6: folder_watcher.py + main.py integration
              ├── A-T7: whatsapp_scanner.py (optional)
              ├── A-T8: API endpoints + Flutter assignment tab
              ├── B-T0: DB migration (face tables)
              ├── B-T1: face_auth.py
              ├── B-T2: API endpoints (face)
              ├── B-T3: PC auto-login integration
              └── B-T4: Flutter face login screen
```

**Commit message convention:**

```
feat(assignment-pipeline): [T number] — [what was done]
feat(face-login): [T number] — [what was done]

Examples:
feat(assignment-pipeline): A-T1 — document_parser.py, supports PDF/DOCX/img/URL
feat(assignment-pipeline): A-T5 — assignment_manager orchestrator with voice flow
feat(face-login): B-T1 — face_auth.py, deepface Facenet, SQLite BLOB storage
feat(face-login): B-T3 — PC startup face scan, welcome message in HUD
```

---

## 7. Testing Protocol

### Feature A Tests

| #   | Test                | Method                              | Expected                                |
| --- | ------------------- | ----------------------------------- | --------------------------------------- |
| 1   | PDF parse           | `parser.parse("test.pdf")`          | Clean text, no garbage                  |
| 2   | DOCX parse          | `parser.parse("test.docx")`         | Paragraph text returned                 |
| 3   | Image OCR           | `parser.parse("photo.jpg")`         | OCR text extracted                      |
| 4   | URL parse           | `parser.parse("https://...")`       | Page body text, no scripts              |
| 5   | Detect: assignment  | `detector.analyze(assignment_text)` | `is_assignment: true, confidence > 0.7` |
| 6   | Detect: random text | `detector.analyze("Hello world")`   | `is_assignment: false`                  |
| 7   | Generate assignment | Full pipeline with sample metadata  | 500+ words, coherent                    |
| 8   | Write PDF           | `writer.write(...)`                 | PDF in nova_outbox, opens correctly     |
| 9   | Write DOCX          | `writer.write(..., "docx")`         | DOCX in nova_outbox, opens correctly    |
| 10  | Folder watcher      | Drop file in nova_inbox             | NOVA speaks within 3s                   |
| 11  | API upload          | `POST /api/assignment/upload`       | File appears in inbox                   |
| 12  | API download        | `GET /api/assignment/download/1`    | File downloaded correctly               |
| 13  | Voice flow          | "Hey NOVA" + assignment detected    | Speaks prompt, listens, generates       |
| 14  | End-to-end          | Full flow: PDF in → assignment out  | DOCX/PDF in outbox                      |

### Feature B Tests

| #   | Test                  | Method                                    | Expected                                 |
| --- | --------------------- | ----------------------------------------- | ---------------------------------------- |
| 1   | Registration          | `face_auth.register_from_webcam("Akif")`  | BLOB stored in DB                        |
| 2   | Same-face verify      | `verify_from_webcam("Akif")`same person   | `authenticated: true, similarity > 0.6`  |
| 3   | Different-face verify | Different person                          | `authenticated: false, similarity < 0.5` |
| 4   | No face               | Covered camera                            | `error: "Could not detect a face"`       |
| 5   | Session create        | `create_session("Akif")`                  | Token returned, stored in DB             |
| 6   | Session validate      | Valid token                               | `valid: true, user_name: "Akif"`         |
| 7   | Session expired       | 25h old token                             | `valid: false, reason: expired`          |
| 8   | API register          | `POST /api/auth/face/register`with base64 | Success response                         |
| 9   | API verify correct    | `POST /api/auth/face/verify`correct face  | `authenticated: true`+ token             |
| 10  | API verify wrong      | Wrong face base64                         | `authenticated: false`                   |
| 11  | PC startup            | Launch main.py with face registered       | Welcome in HUD within 5s                 |
| 12  | Flutter login         | Open app, camera scan                     | Session token stored, home screen opens  |
| 13  | Fallback              | 3 face failures in app                    | API key input shown                      |

---

## 8. Risk Register

| Risk                                                  | Likelihood | Mitigation                                                                                                       |
| ----------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------- |
| deepface first-run model download (~90MB)             | Certain    | Download during A-T0 setup step, not at runtime. Call `DeepFace.build_model("Facenet")`once during install.      |
| pytesseract requires Tesseract binary on Windows      | Certain    | Install step: download Tesseract installer from tesseract-ocr/tesseract GitHub, add to PATH. Document in README. |
| WhatsApp Web HTML structure changes → Selenium breaks | Medium     | Whole scanner is optional (`config.json`toggle). Folder watcher is primary path.                                 |
| deepface CUDA/GPU errors on CPU-only machines         | Low        | Force CPU:`DeepFace.represent(..., detector_backend="opencv")`— opencv backend is CPU-only and stable.           |
| SQLite BLOB size for face embeddings                  | None       | Facenet embedding = 512 floats × 4 bytes = 2KB. SQLite handles gigabyte BLOBs.                                   |
| Concurrent DB writes (face + voice + API)             | Low        | WAL mode already enabled from Alyan's work (T14). No additional action needed.                                   |
| fpdf2 font issue with non-ASCII characters (Urdu)     | Medium     | Use `fpdf.add_font()`with a Unicode font (DejaVuSans.ttf). Add to assets/fonts/.                                 |
| Groq rate limit during assignment generation          | Low        | 3-attempt backoff already implemented in AssignmentGenerator.                                                    |

---

## Implementation Order Summary

```
Day 1:  A-T0 (branch + deps + config + DB schema + folder creation)
Day 2:  A-T1 (document_parser.py) + A-T2 (assignment_detector.py)
Day 3:  A-T3 (assignment_generator.py) + A-T4 (document_writer.py)
Day 4:  A-T5 (assignment_manager.py) + A-T6 (folder_watcher + main.py wire)
Day 5:  A-T7 (whatsapp_scanner, optional) + A-T8 (API endpoints + Flutter tab)
Day 6:  B-T0 (DB migration) + B-T1 (face_auth.py) — deepface model downloaded
Day 7:  B-T2 (API endpoints) + B-T3 (PC startup integration)
Day 8:  B-T4 (Flutter face login screen)
Day 9:  Full integration testing (all tests in Section 7)
Day 10: Demo polish, README update, final commits, merge PR to akif/week4-dev
```

---

_NOVA AI — Hackathon Sprint | feature/hackathon-sprint | Python 3.11 | All free tools_
_Implementation Plan v1.0 — Feature A: Assignment Pipeline | Feature B: Face Login_
