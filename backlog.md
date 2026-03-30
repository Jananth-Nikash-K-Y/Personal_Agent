# 📋 Sentinal Lee — Development Backlog

This file tracks the status of all active and planned development phases for Sentinal Lee.

## 🏗️ Phase Status Overview

| Phase | Feature | Status | Priority |
|---|---|---|---|
| **P1** | **Voice Interface** | 🔴 Backlog | High |
| **P2** | **Multi-Channel (WhatsApp)** | 🟡 In-Progress | High |
| **P3** | **Vision & Document Analysis** | ✅ Done | - |
| **P4** | **Expense Management** | ✅ Done | - |
| **P5** | **Task Management** | ✅ Done | - |
| **P6** | **Contact CRM** | ✅ Done | - |
| **P7** | **Email Follow-up Intelligence** | ✅ Done | - |
| **P8** | **Morning Briefing Engine** | ✅ Done | - |
| **P9** | **Ollama Local Fallback** | ✅ Done | - |
| **P10** | **Obsidian Vault Sync** | ✅ Done | - |
| **P11** | **Web Monitoring Service** | ✅ Done | - |
| **P12** | **Executive Reflection Loop** | ✅ Done | - |

---

## 🛠️ Immediate Roadmap (Next Sprint)

### 1. Stability & Fixes
- [ ] **Standardize Models**: Align `config.py` with `README.md` and move toward Gemini 2.0.
- [ ] **Dynamic Location**: Remove hardcoded "Chennai" weather; pull from `.env`.
- [ ] **Modularize Tools**: Split `core/tools.py` into feature-specific modules.

### 2. Implementation
- [ ] **WhatsApp Completion**: Restore proactive heartbeats to the WhatsApp channel.
- [ ] **Phase 1 (Voice)**: Add OGG to MP3 transcription using Faster-Whisper.
- [ ] **Regional Context**: Optimize system prompt for Indian languages (Tamil/Hindi).

## 🚀 Vision Backlog (Future)
- [ ] **HomeKit Integration**: Control local smart devices via chat.
- [ ] **Secure Web Dashboard**: Visualization for expenses and tasks using FastAPI.
- [ ] **Contextual Memory Cleanup**: Logic for the LLM to archive old/obsolete "memories" automatically.

