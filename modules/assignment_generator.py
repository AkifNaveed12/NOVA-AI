"""
MODULE — Assignment Generator
Agentic Groq pipeline:
1. Receives assignment metadata from AssignmentDetector
2. Optionally receives user-provided resources (lecture notes, slides)
3. Searches web for supporting content (Wikipedia + web requests)
4. Generates a complete, humanized assignment
5. Returns structured content ready for DocumentWriter
"""

import os
import time
import requests
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
        Returns: {"title": str, "content": str, "word_count": int, "success": bool, "subject": str}
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
