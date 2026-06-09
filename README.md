# 🏥 CareFlow — Healthcare Appointment & Queue Management API

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/Tests-13%20passed-brightgreen?logo=pytest)](./tests)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](./Dockerfile)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

> A production-grade REST API for clinic appointment booking and live queue management.
> Evolved from a B.Tech desktop app (Tkinter + SQLite, 2018) into a modern,
> deployable full-stack system with JWT auth, PostgreSQL, and Docker.

---

## ✨ Live Demo

| Link | Description |
|---|---|
| **[https://careflow.up.railway.app/docs](https://careflow.up.railway.app/docs)** | Interactive API — try every endpoint in the browser |
| **[https://careflow.up.railway.app/app](https://careflow.up.railway.app/app)** | Frontend dashboard |

> _Deploy your own instance in 5 minutes — see [Deployment](#-deploy-to-railway-free) below._

---

## 🗂️ Project Story

| | 2018 (B.Tech) | 2026 (This Repo) |
|---|---|---|
| UI | Tkinter desktop app | React-style HTML dashboard |
| Database | SQLite (single file) | PostgreSQL (multi-tenant ready) |
| API | None | FastAPI with auto Swagger docs |
| Auth | None | JWT bearer tokens |
| Notifications | `pyttsx3` TTS only | WhatsApp-ready webhook stubs |
| Deployment | Single Windows PC | Docker + Railway (one click) |
| Tests | None | 13 pytest tests, all passing |

The original `appointment.py`, `update.py`, and `display.py` are preserved in
`src/core/` as legacy reference — you can see exactly what was upgraded and why.

---

## 🏗️ Architecture

```
CareFlow/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI app + CORS + static file serving
│   │   ├── database.py          # SQLAlchemy engine (SQLite dev / PostgreSQL prod)
│   │   ├── schemas.py           # Pydantic v2 request/response models
│   │   └── routes/
│   │       ├── auth.py          # POST /auth/register, /auth/login
│   │       ├── appointments.py  # Full CRUD for appointments
│   │       ├── queue.py         # Live queue + dashboard stats
│   │       └── doctors.py       # Doctor management
│   ├── models/
│   │   └── models.py            # SQLAlchemy ORM models
│   ├── auth/
│   │   └── jwt.py               # JWT encode/decode + FastAPI dependency
│   └── core/
│       ├── appointment_legacy.py  # Original Tkinter code (reference)
│       ├── update_legacy.py       # Original update screen (reference)
│       └── display_legacy.py      # Original TTS queue (reference)
├── frontend/
│   └── index.html               # Single-file HTML/JS/Tailwind frontend
├── tests/
│   └── test_appointments.py     # 13 pytest tests (all passing)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🚀 Quick Start (Local)

### Option 1 — Docker (recommended, one command)

```bash
git clone https://github.com/YOUR_USERNAME/careflow.git
cd careflow
docker-compose up --build
```

Then open:
- **http://localhost:8000/docs** — Interactive Swagger UI
- **http://localhost:8000/app** — Frontend dashboard

### Option 2 — Python venv

```bash
git clone https://github.com/YOUR_USERNAME/careflow.git
cd careflow
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

---

## 📡 API Reference

### Authentication
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | None | Register doctor/staff account |
| POST | `/auth/login` | None | Login → receive JWT token |

### Appointments
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/appointments` | None | Book a new appointment |
| GET | `/appointments` | ✅ JWT | List all (filter by date/status) |
| GET | `/appointments/today` | ✅ JWT | Today's appointments |
| GET | `/appointments/{id}` | None | Get by ID |
| PUT | `/appointments/{id}` | ✅ JWT | Update status/time/notes |
| DELETE | `/appointments/{id}` | ✅ JWT | Cancel appointment |

### Queue
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/queue/today` | ✅ JWT | Full today's queue with tokens |
| POST | `/queue/{token}/call` | ✅ JWT | Call next patient |
| GET | `/queue/stats` | ✅ JWT | Dashboard summary stats |

---

## 🧪 Tests

```bash
pytest tests/ -v
# 13 passed in 4.3s
```

Test coverage includes: health check, doctor registration/login, appointment CRUD,
token assignment sequence, auth guard enforcement, cancel/update flows, stats endpoint.

---

## ☁️ Deploy to Railway (Free)

1. Fork this repo on GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Select your fork
4. Railway auto-detects the `Dockerfile` and builds it
5. Add a **PostgreSQL** plugin (one click in Railway dashboard)
6. Railway automatically sets `DATABASE_URL` — no config needed
7. Add env variable: `SECRET_KEY=your-random-secret-here`
8. Done. Your live URL appears in the Railway dashboard.

**Total time: ~5 minutes.**

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Framework | **FastAPI 0.110** | Auto Swagger docs, async, type-safe |
| ORM | **SQLAlchemy 2.0** | Works with SQLite (dev) and PostgreSQL (prod) |
| Validation | **Pydantic v2** | Request/response schema enforcement |
| Auth | **JWT (python-jose)** | Stateless, scalable |
| Password | **bcrypt (passlib)** | Industry-standard hashing |
| Database | **PostgreSQL / SQLite** | Same code, different env vars |
| Container | **Docker + Compose** | Reproducible builds |
| Tests | **pytest + httpx** | 13 tests, in-memory SQLite |
| Frontend | **Tailwind CSS (CDN)** | Zero build step, looks polished |

---

## 💡 Key Design Decisions

**Why SQLAlchemy over a raw ORM?** Allows the same codebase to use SQLite locally (zero setup for contributors) and PostgreSQL in production — controlled by one env variable.

**Why a single-file frontend?** No npm install, no build step, no broken CI. A technical reviewer can clone and `docker-compose up` and see a working UI in under a minute. That's the point.

**Why preserve the legacy Tkinter code?** It shows the evolution clearly — the git diff tells a story. Interviewers and reviewers appreciate seeing what problem was solved and how thinking matured.

---

## 📄 License

MIT — use freely, attribution appreciated.

---

> **Built by Raj** · [mr.loki549@gmail.com](mailto:mr.loki549@gmail.com) · [LinkedIn](#) · [Portfolio](#)
