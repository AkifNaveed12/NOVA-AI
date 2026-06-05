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

import os
import json
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
        # Retrieve the key from system environment or defaults
        api_key = os.getenv("GROQ_API_KEY", "")
        self.client = Groq(api_key=api_key)

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
