# NOVA AI — Build Log

## Current Status
**Active T:** T12 — Android APK Build
**Phase:** 5 — Deployment

## Progress Table

| T | Title | Status | Date |
|---|-------|--------|------|
| T0 | Log System & Pre-flight Cleanup | ✅ Done | 2026-05-26 |
| T1 | Thread-Safety Lock | ✅ Done | 2026-05-26 |
| T2 | FastAPI Server Skeleton | ✅ Done | 2026-05-26 |
| T3 | WebSocket Status Bridge | ✅ Done | 2026-05-26 |
| T4 | Remote Command Endpoint | ✅ Done | 2026-05-26 |
| T5 | UDP Auto-Discovery | ✅ Done | 2026-05-26 |
| T6 | Onboarding Backend | ✅ Done | 2026-05-26 |
| T7 | Coding Assistant Module | ✅ Done | 2026-05-26 |
| T8 | Flutter App Scaffold | ✅ Done | 2026-05-26 |
| T9 | Connect + Onboarding UI | ✅ Done | 2026-05-26 |
| T10 | Dashboard + Remote Control UI | ✅ Done | 2026-05-26 |
| T11 | Coding Assistant UI | ✅ Done | 2026-05-26 |
| T12 | Android APK Build | 🔄 Active | 2026-05-26 |
| T13 | PyInstaller Packaging | ⬜ Todo | — |
| T14 | End-to-End Integration Tests | ⬜ Todo | — |

---

## T12 — Android APK Build
**Started:** 2026-05-26
**Goal:** Build the Flutter APK. No web version (Android only per user request).

### Steps
- [ ] Install Flutter SDK (if not installed): https://docs.flutter.dev/get-started/install/windows
- [ ] `cd nova_app && flutter pub get`
- [ ] `flutter build apk --release`
- [ ] Output: `nova_app/build/app/outputs/flutter-apk/app-release.apk`
- [ ] Transfer APK to Android device and install (enable "Unknown sources")

### Issues
*(none yet)*

---

## What Was Built (T0–T11 Summary)

### Backend (modules/api_server.py)
- `GET /api/health` — health check, no auth
- `GET /api/setup/status` — checks if Groq key is configured
- `POST /api/setup` — saves user config (surgical .env update, validates Groq key)
- `POST /api/command` — routes text command through full NLP pipeline
- `POST /api/chat/code` — coding assistant (Markdown responses)
- `POST /api/chat/code/reset` — clears code conversation
- `WS /ws/status` — real-time NOVA state (sleeping/listening/processing/speaking)
- `WS /ws/interactive` — multi-turn voice flows (email, WhatsApp)
- UDP broadcaster on port 37020 for network auto-discovery

### Flutter App (nova_app/)
- `ConnectScreen` — IP + API key entry with connection test
- `Step1–5` — 5-step onboarding wizard (name, Groq key, email, contacts, city)
- `DashboardTab` — 8 quick-action buttons (lock, mute, volume, screenshot, etc.)
- `RemoteTab` — chat-style text commands + live NOVA status indicator (WebSocket)
- `CodeTab` — Markdown-rendered coding assistant with context memory

### Other fixes
- SQLite WAL mode enabled (prevents "database is locked" under concurrent API + voice access)
- `nova_core.route()` protected by `threading.Lock` (T1)
- All 4 NOVA state transitions (sleeping/listening/processing/speaking) broadcast to WebSocket clients

---

## Issues Log (Cross-T)

| Date | T | Issue | Resolution |
|------|---|-------|------------|
| 2026-05-26 | T0 | groq_brain.py used nova.user_name (removed from config) | Updated to use user.name |
| 2026-05-26 | T0 | config.json had stale model llama3-70b-8192 | Updated to llama-3.3-70b-versatile |
