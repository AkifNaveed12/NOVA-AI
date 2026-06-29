# FINAL-PLANNING.md

> Execution Playbook for NOVA AI Final Hackathon Sprint

## Global Engineering Rules

1.  Never leave the system in a broken state.
2.  Every task must end with the desktop assistant running successfully.
3.  Keep feature parity between **Desktop** and **Flutter Mobile App**
    where applicable.
4.  After every major task:
    -   Run the application.
    -   Verify voice pipeline.
    -   Verify API.
    -   Verify mobile connectivity.
5.  Work only on branch:

```{=html}
<!-- -->
```
    akif/hackathon-sprint/final-features

------------------------------------------------------------------------

# MODULE 0 --- Sprint 0: Stability Foundation

### T0

-   Create branch `akif/hackathon-sprint/final-features`
-   Pull latest changes
-   Run preflight checks
-   Verify project boots

### T1

Enable SQLite WAL mode.

Files: - modules/memory_system.py

Acceptance: - No database locked errors.

### T2

Preload faster-whisper during startup.

Files: - modules/stt.py

Acceptance: - No cold start.

### T3

Integrate webdriver-manager.

Files: - modules/web_automation.py

Acceptance: - Chrome launches without driver issues.

### T4

Verify Ollama fallback.

Files: - modules/local_llm.py - modules/groq_brain.py

Acceptance: - Internet OFF → Local LLM responds.

### T5

Run regression.

### T6

Verify Desktop + Mobile integration.

### T7

Test complete Desktop and Mobile workflow.

### T8

Update context.md with: - file - issue - implementation - bug fixes -
reasoning

### T9

Commit & Push

    git add .
    git commit -m "Sprint 0: Stability improvements"
    git push origin akif/hackathon-sprint/final-features

------------------------------------------------------------------------

# MODULE 1 --- Context Scanner

### T0

Create modules/context_scanner.py

### T1

Implement: - Active Window - Clipboard - CPU - RAM - Battery - Recent
Files

### T2

Background daemon every 10 seconds.

### T3

Inject context into Groq.

### T4

Expose context endpoint.

### T5

Display context inside Flutter Dashboard.

### T6

Regression.

### T7

Verify Desktop + Mobile integration.

### T8

Full Desktop + Mobile testing.

### T9

Update context.md.

### T10

Commit & Push.

------------------------------------------------------------------------

# MODULE 2 --- Semantic Memory

### T0

Create semantic_memory.py

### T1

Create schema.

### T2

Embedding generation.

### T3

Similarity search.

### T4

Inject semantic memories into prompts.

### T5

Migration script.

### T6

API endpoint.

### T7

Flutter memory screen.

### T8

Desktop + Mobile integration.

### T9

Regression testing.

### T10

Update context.md.

### T11

Commit & Push.

------------------------------------------------------------------------

# MODULE 3 --- Urdu Multilingual Pipeline

### T0

Create multilingual.py

### T1

Language detection.

### T2

Translation.

### T3

Urdu TTS.

### T4

Pipeline integration.

### T5

HUD updates.

### T6

Flutter language support.

### T7

Desktop + Mobile integration.

### T8

Regression tests.

### T9

Update context.md.

### T10

Commit & Push.

------------------------------------------------------------------------

# MODULE 4 --- Search Engine

### T0

Create search_engine.py

### T1

Tavily.

### T2

DuckDuckGo fallback.

### T3

Caching.

### T4

Groq integration.

### T5

Flutter Search UI.

### T6

Desktop + Mobile integration.

### T7

Testing.

### T8

Update context.md.

### T9

Commit & Push.

------------------------------------------------------------------------

# MODULE 5 --- Offline LLM

### T0

Finalize Ollama.

### T1

Implement local_llm.py

### T2

Groq fallback.

### T3

Offline validation.

### T4

Flutter offline status.

### T5

Desktop + Mobile integration.

### T6

Testing.

### T7

Update context.md.

### T8

Commit & Push.

------------------------------------------------------------------------

# MODULE 6 --- Demo Polish

### T0

HUD improvements.

### T1

Thinking animation.

### T2

Context indicator.

### T3

Language indicator.

### T4

Performance optimization.

### T5

Desktop + Mobile integration.

### T6

Complete regression.

### T7

Update context.md.

### T8

Commit & Push.

------------------------------------------------------------------------

# Final Acceptance Checklist

-   Voice assistant stable
-   Mobile app stable
-   Context Scanner operational
-   Semantic Memory operational
-   Faster Whisper operational
-   Tavily operational
-   DuckDuckGo fallback operational
-   Ollama operational
-   Groq fallback operational
-   Urdu operational
-   HUD polished
-   APIs stable
-   No regression
-   Demo rehearsed
-   Repository pushed

## Definition of Done

A task is complete only if:

-   Feature implemented
-   Existing functionality preserved
-   Desktop works
-   Flutter works
-   Integration verified
-   Regression passed
-   context.md updated
-   Changes committed and pushed
