# Paperclip Telegram Bot

![Python](https://img.shields.io/badge/Python-99.6%25-3776AB?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)
![Telegram](https://img.shields.io/badge/Bot-API-26A5E4?style=for-the-badge&logo=telegram)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Production-ready Telegram bot for managing Paperclip projects — issues, agents, environments, and more — right from your chat.**

---

## What It Does

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   You (on Telegram)          Paperclip Telegram Bot        │
│   ┌──────────┐                ┌─────────────────────────┐  │
│   │ /issues │  ───────────►  │  • List projects        │  │
│   │          │                │  • Create issues        │  │
│   │ show me  │                │  • Manage agents        │  │
│   │ critical │                │  • View environments    │  │
│   │ bugs     │                │  • Daily digest         │  │
│   │          │                └──────────┬──────────────┘  │
│   │ /help    │                             │               │
│   │          │                             ▼               │
│   └──────────┘               ┌──────────────────────────┐  │
│                              │    Paperclip API         │  │
│                              │    (http://127.0.0.1:3100) │  │
│                              └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### Issue Management
| Command | What it does |
|---------|--------------|
| `/issues` | List all issues (paginated) |
| `/issues open high` | Filter by status + priority |
| `/create_issue` | Multi-step wizard with inline keyboards |
| `/update_issue <id>` | Edit status, priority, assignee |

### Natural Language
Type like a human — the bot understands:

- "show me all open critical bugs"
- "list high priority tickets"
- "create a new ticket for login bug"
- "is the api alive?"

### Admin Tools
| Command | Who | What it does |
|---------|-----|--------------|
| `/stats` | Admin | Uptime, command count, API status |
| `/broadcast <msg>` | Admin | Send message to all users |
| `/metrics` | Admin | Prometheus metrics endpoint |

### Scheduled Digest
- Daily summary of open issues → automatically sent to all users
- Configurable time and priority filters

---

## Quick Start

### 1. Clone & Configure
```bash
git clone https://github.com/unn-Known1/Paperclip_telegramBot.git
cd Paperclip_telegramBot
cp .env.example .env
```

### 2. Edit `.env`
```env
TELEGRAM_BOT_TOKEN=123456:ABCdefGHIjklMNOpqrsTUVwxyz
ALLOWED_USER_IDS=111222333,444555666
ADMIN_USER_IDS=111222333
PAPERCLIP_API_URL=http://127.0.0.1:3100
```

### 3. Run

**Option A: Python (local)**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

**Option B: Docker**
```bash
docker-compose up -d
```

---

## Architecture

```
Telegram Users
       │
       ▼
┌──────────────────────┐
│    Telegram API      │
│   (webhook/polling)  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐     ┌──────────────────┐
│   aiogram Bot        │────►│  Paperclip API   │
│   (handlers/)        │     │  (Async HTTP)    │
│                      │     └──────────────────┘
│  ┌────────────────┐  │
│  │ auth.py        │  │     ┌──────────────────┐
│  │ rate_limit.py  │  │────►│  Prometheus      │
│  │ audit.py       │  │     │  /metrics        │
│  │ errors.py      │  │     └──────────────────┘
│  └────────────────┘  │
└──────────────────────┘
```

---

## Project Structure

```
Paperclip_telegramBot/
├── bot.py                 # Entry point
├── config.py              # Config loader
├── paperclip_client.py    # Async API client (with retry)
├── metrics_server.py      # Prometheus /metrics endpoint
│
├── handlers/              # Telegram command handlers
│   ├── basic.py           # /start, /help, /health, /company
│   ├── issues.py          # /issues, /create_issue, /update_issue
│   ├── projects.py        # /projects
│   ├── agents.py          # /agents
│   ├── resources.py       # /environments, /members, /invites
│   ├── admin.py           # /stats, /broadcast
│   └── digest.py          # Daily digest scheduler
│
├── middleware/            # Cross-cutting concerns
│   ├── auth.py            # @restricted, @admin_only
│   ├── rate_limit.py      # Token-bucket rate limiter
│   ├── audit.py           # Command audit logging
│   ├── errors.py          # Global error handler
│   └── metrics.py         # Prometheus counters
│
├── utils/                 # Shared utilities
│   ├── formatting.py      # Rich HTML formatters
│   ├── pagination.py      # Paginated inline keyboards
│   ├── chunking.py        # 4096-char message splitting
│   └── nlp.py             # Natural language parser
│
├── tests/                 # Test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | From @BotFather |
| `ALLOWED_USER_IDS` | ✅ | — | Comma-separated user IDs |
| `PAPERCLIP_API_URL` | — | `http://127.0.0.1:3100` | Paperclip API |
| `ADMIN_USER_IDS` | — | — | Admin Telegram IDs |
| `WEBHOOK_URL` | — | — | Set for webhook mode |
| `METRICS_ENABLED` | — | `false` | Enable `/metrics` |
| `DIGEST_ENABLED` | — | `false` | Daily issue digest |
| `RATE_LIMIT_RPM` | — | `30` | Max requests/min/user |

---

## All Commands

### General
| Command | Description |
|---------|-------------|
| `/start` | Welcome + quick-action buttons |
| `/help` | Show all commands |
| `/health` | Check Paperclip API status |
| `/company` | Show company details |

### Issues
| Command | Description |
|---------|-------------|
| `/issues [status] [priority]` | List issues with filters |
| `/create_issue` | Interactive creation wizard |
| `/update_issue <id>` | Inline update with buttons |

### Resources
| Command | Description |
|---------|-------------|
| `/projects` | List all projects |
| `/agents` | List all agents |
| `/environments` | List environments |
| `/members` | List team members |
| `/invites` | List pending invites |

### Admin (requires ADMIN_USER_IDS)
| Command | Description |
|---------|-------------|
| `/stats` | Bot uptime + stats |
| `/broadcast <message>` | Broadcast to all users |
| `/metrics` | Prometheus metrics |

---

## Testing

```bash
# Install dev deps
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=html
```

---

## Contributing

1. **Fork** → **Branch** → **Commit** → **PR**
2. Follow `pep8` style guide
3. Add tests for new handlers
4. Update this README if adding commands

---

## Security

- **User allowlist** — only `ALLOWED_USER_IDS` can use the bot
- **Admin role** — sensitive commands need `ADMIN_USER_IDS`
- **Rate limiting** — token-bucket per user to prevent abuse
- **Audit logging** — all commands logged with timestamp + user ID

---

## Monitoring

### Prometheus Metrics
```
GET /metrics
```
Returns:
- `bot_commands_total{command="issues"}` — command counter
- `bot_errors_total` — error counter
- `api_requests_total{endpoint="/issues"}` — API call counter
- `api_latency_seconds` — latency histogram

### Logs
```bash
# Structured JSON (production)
LOG_FORMAT=json python bot.py

# Human-readable (development)
LOG_FORMAT=text python bot.py
```

---

## License

MIT — free to use, modify, distribute.

---

<p align="center">
  <sub>Built with <a href="https://github.com/aiogram/aiogram">aiogram</a> ·
  Made by <a href="https://github.com/unn-known1">Gaurang Patel</a></sub>
</p>