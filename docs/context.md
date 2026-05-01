## architecture.md
- File: architecture.md (new file)
- Added: System Architecture flowchart in Mermaid (flowchart TD)
  - Nodes: Gesture Engine (BG thread), Wake Word Listener, Microphone Input,
    NLP Intent Engine, Groq API, Local Module Router, System Modules,
    Web + APIs, Automation, Memory/DB, TTS Output + HUD Display
  - Flows match original diagram exactly; GE bypasses voice pipeline to TTS
- Added: ERD in Mermaid (erDiagram)
  - Tables: Users, UserFacts, Notes, Tasks, Events, Reminders, Contacts,
    ActivityLog, ConversationLog — all fields and keys preserved as-is
  - Relationships: Users 1-to-many all tables; ActivityLog links Notes/Tasks/Events/ConversationLog
- Reason: Mermaid-renderable version of architecture.png and erd.png for docs

## planning.md
- File: planning.md (new file, project root)
- Content: Full 28-day development plan — all 25 modules, task-by-task breakdown
- Structure: Each day has T0 (prereqs) → T1...Tn (implementation) → TEST → PUSH
- Appendix: Master module index, git commit convention, 24 test case summary table
- Source: Derived from nova_4week_roadmap.svg + Modules_detail_information + SYSTEM_SUMMARY
- Reason: Single planning document covering all implementation steps for semester submission