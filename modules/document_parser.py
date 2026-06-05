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

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"D:\Tools\Tesseract-OCR\tesseract.exe"


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
        Returns: {"text": str, "source_type": str, "filename": str, "success": bool, "error": str}
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
