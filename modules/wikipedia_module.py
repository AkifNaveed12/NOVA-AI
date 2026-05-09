"""
MODULE 7 — Wikipedia Knowledge Base
======================================
Answers "tell me about X" queries with 3-sentence Wikipedia summaries.
Handles disambiguation errors by offering multiple topic choices.
No API key required — uses the wikipedia Python library.

Tech: wikipedia (Python library, free, no key)
Output: 3-sentence summary string → TTS engine
"""

import re
import wikipedia


class WikipediaModule:
    def __init__(self):
        # Use English Wikipedia
        wikipedia.set_lang("en")

    def search(self, query: str) -> str:
        """
        Returns a 3-sentence Wikipedia summary for the given query.
        Gracefully handles disambiguation and page-not-found errors.
        """
        if not query or not query.strip():
            return "What would you like me to look up on Wikipedia?"

        query = query.strip()

        try:
            summary = wikipedia.summary(query, sentences=3, auto_suggest=True)
            # Clean references like [1], [2], etc. and strip extra whitespace
            summary = re.sub(r'\[\d+\]', '', summary)
            summary = re.sub(r'\s+', ' ', summary).strip()
            return summary

        except wikipedia.exceptions.DisambiguationError as e:
            # Offer the top 3 options to the user
            options = e.options[:3]
            opts_str = ", ".join(options)
            return (
                f"'{query}' could refer to several things: {opts_str}. "
                f"Please be more specific, for example: tell me about {options[0]}."
            )

        except wikipedia.exceptions.PageError:
            return f"I couldn't find a Wikipedia article about '{query}'. Please try a different search term."

        except Exception as e:
            print(f"[Wikipedia] Unexpected error for '{query}': {e}")
            return f"Sorry, I had trouble looking up '{query}' on Wikipedia right now."
