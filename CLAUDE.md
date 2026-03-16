# CLAUDE.md — WhatsApp Assistant

## Project Overview
A WhatsApp-based personal assistant chatbot powered by **Claude API with tool use**. Helps the user manage to-dos, track priorities, get recommendations on what to focus on next, and have natural conversations — all through WhatsApp messages.

Inspired by the **AgentOfAgents** project architecture (Discord orchestrator), adapted for WhatsApp with a focus on personal productivity.

## Current Status
**Phase 1 — Core implementation complete.**

### What exists:
- Flask webhook server for Meta WhatsApp Business Cloud API
- Claude API tool-use loop (multi-turn, tools dispatch)
- To-do management tools (add, list, complete, update, delete, priority, due dates)
- Recommendation engine (analyzes to-dos, suggests next actions)
- SQLite persistence (to-dos, conversation history)
- Per-user scoping (multiple WhatsApp users supported)
- Message chunking for WhatsApp's character limit
- Health check endpoint

---

## Architecture

```
You (Phone / WhatsApp)
        │
        ▼  webhook (HTTPS POST)
  Flask Server (bot/whatsapp_bot.py)
        │  extract message, verify sender
        ▼
  Orchestrator Core (core/orchestrator.py)
        │  Claude API with tool_use
        ▼
  Tool Registry (tools/)
        ├── todo_manager.py     # CRUD for to-do items
        └── recommendation.py   # Smart prioritization advice
        │
        ▼
  State Store (state/database.py)  # SQLite via peewee
        ├── Todo                   # user's to-do items
        └── ConversationHistory    # per-user message history
        │
        ▼
  WhatsApp Cloud API (send reply back)
```

---

## Tech Stack

| Component       | Library         | Version  |
|-----------------|-----------------|----------|
| Claude AI       | anthropic       | ^0.25    |
| Web server      | flask           | ^3.0     |
| HTTP client     | requests        | ^2.31    |
| ORM / SQLite    | peewee          | ^3.17    |
| Config          | python-dotenv   | ^1.0     |
| Production WSGI | gunicorn        | ^21.2    |

---

## Directory Structure

```
Assistant/
├── CLAUDE.md                  # ← you are here
├── main.py                    # Entry point — starts Flask server
├── requirements.txt
├── .env.example               # Required env vars
├── .gitignore
├── config/
│   ├── __init__.py
│   └── settings.py            # Loads env, exposes typed config
├── core/
│   ├── __init__.py
│   └── orchestrator.py        # Claude API tool-use loop
├── tools/
│   ├── __init__.py            # Tool registry — exports TOOLS + dispatch()
│   ├── todo_manager.py        # To-do CRUD operations
│   └── recommendation.py      # Priority analysis and path-forward advice
├── bot/
│   ├── __init__.py
│   └── whatsapp_bot.py        # Flask webhook, WhatsApp API integration
└── state/
    ├── __init__.py
    └── database.py            # Peewee models: Todo, ConversationHistory
```

---

## Environment Variables (`.env`)

```env
# Required
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ALLOWED_NUMBERS=1234567890
ANTHROPIC_API_KEY=your_api_key

# Optional
CLAUDE_MODEL=claude-sonnet-4-20250514
DB_PATH=./assistant.db
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO
MAX_HISTORY=30
```

---

## Claude Tools

| Tool                | Description                                           |
|---------------------|-------------------------------------------------------|
| add_todo            | Add a new to-do with optional priority/due date/category |
| list_todos          | List to-dos with filtering by status/priority/category |
| complete_todo       | Mark a to-do as done                                  |
| update_todo         | Update title, description, category, or status        |
| delete_todo         | Permanently remove a to-do                            |
| set_priority        | Change priority (low/medium/high/urgent)              |
| set_due_date        | Set or clear a due date                               |
| get_todo_summary    | Statistics: counts by status, priority, overdue items |
| get_recommendations | Analyze to-dos and recommend what to focus on next    |

---

## Running the Project

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in .env values

# Development
python main.py

# Production
gunicorn -w 1 -b 0.0.0.0:8080 bot.whatsapp_bot:app
```

---

## WhatsApp Business API Setup (one-time)

1. Go to https://developers.facebook.com/ and create a new app (type: Business)
2. Add the **WhatsApp** product to your app
3. In WhatsApp → Getting Started:
   - Note your **Phone Number ID** → `WHATSAPP_PHONE_NUMBER_ID`
   - Generate a **temporary access token** → `WHATSAPP_ACCESS_TOKEN`
   - For production, create a System User token with `whatsapp_business_messaging` permission
4. Set up your webhook:
   - URL: `https://your-server.com/webhook`
   - Verify token: whatever you set as `WHATSAPP_VERIFY_TOKEN`
   - Subscribe to: `messages`
5. You need HTTPS — use ngrok for development: `ngrok http 8080`
6. Add your phone number (with country code, no +) to `WHATSAPP_ALLOWED_NUMBERS`

---

## Phases Roadmap

### ✅ Phase 1 — Core Loop (done)
- Flask webhook ↔ Claude ↔ tools pipeline
- To-do CRUD (add, list, complete, update, delete, priority, due dates)
- Recommendation engine
- Conversation history persistence
- Per-user to-do scoping

### 📋 Phase 2 — Reminders & Scheduling
- Daily summary message (morning brief of what's due)
- Reminder scheduling via APScheduler
- Recurring to-dos
- "Snooze" a to-do to a future date

### 🧠 Phase 3 — Smart Features
- Natural language date parsing ("due next Friday")
- To-do categorization suggestions
- Weekly review prompt (reflect on completed, plan ahead)
- Goal tracking (link to-dos to larger goals)

### 🎨 Phase 4 — Polish
- WhatsApp interactive buttons and list messages
- Voice message transcription (Whisper API)
- Image/document attachment handling
- Multi-language support

---

## Key Implementation Notes

- **Security**: `WHATSAPP_ALLOWED_NUMBERS` filters who can interact. Never respond to unknown numbers.
- **Conversation history**: last N messages per user in SQLite, injected into Claude context each turn.
- **Tool dispatch**: passes `user_id` (phone number) to all tools to scope data per user.
- **WhatsApp limits**: ~4096 chars per message. Messages are auto-chunked.
- **Webhook**: Meta sends a GET for verification, POST for incoming messages. Both handled.
- **HTTPS required**: Meta requires HTTPS for webhooks. Use ngrok for dev, reverse proxy for prod.
- **Stateless server**: all state is in SQLite. Safe to restart without losing data.
