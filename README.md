# 📎 Paperclip Telegram Bot

A production-ready Telegram bot for managing [Paperclip](https://paperclip.dev) projects — issues, agents, environments, and more — right from your chat.

## ✨ Features

| Category | Features |
|---|---|
| **Issue Management** | List (with filters), create (wizard), update (inline keyboard) |
| **Resources** | Projects, agents, environments, members, invites |
| **Interactive UI** | Inline keyboards, pagination, rich HTML formatting, emoji indicators |
| **Natural Language** | Type "show me critical bugs" instead of memorising commands |
| **Scheduled Digest** | Daily summary of open issues sent to all users |
| **Admin Tools** | `/stats`, `/broadcast`, rate limiting, audit logging |
| **Observability** | Structured JSON logging, Prometheus metrics (`/metrics`) |
| **Security** | User-ID allowlist, admin role, per-user rate limiting |
| **Deployment** | Docker + docker-compose, webhook & polling modes |

## 🚀 Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/youruser/Paperclip_telegramBot.git
cd Paperclip_telegramBot
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN and ALLOWED_USER_IDS
```

### 2. Run Locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### 3. Run with Docker

```bash
docker-compose up -d
```

## 📖 Commands

### General
| Command | Description |
|---|---|
| `/start` | Welcome message with quick-action buttons |
| `/help` | Show all available commands |
| `/health` | Check Paperclip API health |
| `/company` | Show current company details |

### Issues
| Command | Description |
|---|---|
| `/issues` | List all issues (paginated) |
| `/issues open` | Filter by status |
| `/issues open high` | Filter by status + priority |
| `/create_issue` | Multi-step issue creation wizard |
| `/update_issue <id>` | Update an issue field |

### Resources
| Command | Description |
|---|---|
| `/projects` | List all projects |
| `/agents` | List all agents |
| `/environments` | List all environments |
| `/members` | List team members |
| `/invites` | List pending invites |

### Admin (requires `ADMIN_USER_IDS`)
| Command | Description |
|---|---|
| `/stats` | Bot uptime, command count, API status |
| `/broadcast <msg>` | Send a message to all allowed users |

### Natural Language
You can also type naturally:
- *"show me all open issues"*
- *"list critical bugs"*
- *"create a new ticket"*
- *"is the api alive?"*

## ⚙️ Configuration

All settings are in `.env`. See [`.env.example`](.env.example) for the full list.

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Bot token from @BotFather |
| `ALLOWED_USER_IDS` | ✅ | — | Comma-separated Telegram user IDs |
| `PAPERCLIP_API_URL` | — | `http://127.0.0.1:3100` | Paperclip API base URL |
| `ADMIN_USER_IDS` | — | — | Users with admin privileges |
| `WEBHOOK_URL` | — | — | Set to enable webhook mode |
| `LOG_FORMAT` | — | `text` | `text` or `json` |
| `METRICS_ENABLED` | — | `false` | Enable Prometheus metrics |
| `DIGEST_ENABLED` | — | `false` | Enable daily issue digest |
| `RATE_LIMIT_RPM` | — | `30` | Max requests/minute/user |
| `LOCALE` | — | `en` | Interface language |

## 🧪 Testing

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## 📁 Project Structure

```
├── bot.py                  # Entry point
├── config.py               # Configuration loader
├── paperclip_client.py     # Async API client (with retry)
├── metrics_server.py       # Prometheus /metrics endpoint
├── handlers/               # Telegram command handlers
│   ├── basic.py            # /start, /help, /health, /company
│   ├── issues.py           # /issues, /create_issue, /update_issue
│   ├── projects.py         # /projects
│   ├── agents.py           # /agents
│   ├── resources.py        # /environments, /members, /invites
│   ├── admin.py            # /stats, /broadcast
│   └── digest.py           # Scheduled daily digest
├── middleware/              # Cross-cutting concerns
│   ├── auth.py             # @restricted, @admin_only
│   ├── rate_limit.py       # Token-bucket rate limiter
│   ├── audit.py            # Command audit logging
│   ├── errors.py           # Global error handler
│   └── metrics.py          # Prometheus counters
├── utils/                  # Shared utilities
│   ├── formatting.py       # Rich HTML formatters
│   ├── pagination.py       # Paginated inline keyboards
│   ├── chunking.py         # 4096-char message splitting
│   └── nlp.py              # Natural language parser
├── i18n/                   # Internationalisation
│   ├── base.py             # String template class
│   └── en.py               # English strings
├── tests/                  # Test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 📄 License

MIT
