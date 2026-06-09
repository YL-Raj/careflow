"""
CareFlow — FastAPI Application Entry Point
=========================================
Original project: Hospital Appointment System (Tkinter + SQLite, 2018)
Upgraded to:      Production FastAPI REST API with JWT auth, PostgreSQL, Docker

Run locally:
    uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

Then visit:
    http://localhost:8000/docs   ← Interactive Swagger UI (show this to HR!)
    http://localhost:8000/redoc  ← Alternative ReDoc documentation
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.database import engine, Base
from src.api.routes import appointments, queue, auth, doctors

# ── Create all DB tables on startup ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CareFlow API",
    description="""
## CareFlow — Healthcare Appointment & Queue Management

A modern REST API for clinic appointment booking and live queue management.

**Origin:** Upgraded from a B.Tech Tkinter + SQLite desktop app (2018) to a
production-grade FastAPI backend with JWT auth, PostgreSQL, and Docker.

### Key Features
- 📅 **Appointment Booking** — book, update, cancel appointments
- 👥 **Patient Management** — auto-create patients on first booking
- 🔢 **Queue System** — auto-assigned token numbers, call-next workflow
- 📊 **Dashboard Stats** — real-time today/week appointment counts
- 🔐 **JWT Auth** — secure doctor/staff login
- 🐳 **Docker Ready** — runs in one `docker-compose up` command

### Quick Demo
1. **POST /auth/register** — create a doctor account
2. **POST /auth/login** — get your JWT token
3. **POST /appointments** — book an appointment (no auth needed)
4. **GET /queue/today** — see the live queue (auth required)
5. **POST /queue/{token}/call** — call next patient
""",
    version="1.0.0",
    contact={"name": "Raj", "email": "mr.loki549@gmail.com"},
    lifespan=lifespan,
)

# ── CORS (allow all origins for demo — tighten for production) ────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(appointments.router)
app.include_router(queue.router)
app.include_router(doctors.router)

# ── Serve frontend static files ───────────────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/app", include_in_schema=False)
    def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "CareFlow API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "frontend": "/app",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
