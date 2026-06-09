"""
CareFlow — Tests
Run: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.api.database import Base, get_db

# ── In-memory SQLite for testing ──────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test_careflow.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)
client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture
def doctor_token():
    """Register a doctor and return their JWT token."""
    client.post("/auth/register", json={
        "name": "Test Doctor",
        "specialization": "General",
        "email": "testdoc@careflow.test",
        "password": "testpassword123",
    })
    r = client.post("/auth/login", json={
        "email": "testdoc@careflow.test",
        "password": "testpassword123",
    })
    return r.json()["access_token"]


# ── Tests ─────────────────────────────────────────────────────────────────────
def test_health_check():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_doctor():
    r = client.post("/auth/register", json={
        "name": "Dr. Raj",
        "specialization": "Cardiology",
        "email": "raj@careflow.test",
        "password": "securepass",
    })
    assert r.status_code == 201
    assert r.json()["name"] == "Dr. Raj"


def test_login():
    client.post("/auth/register", json={
        "name": "Login Doc",
        "email": "login@careflow.test",
        "password": "mypassword",
    })
    r = client.post("/auth/login", json={"email": "login@careflow.test", "password": "mypassword"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password():
    r = client.post("/auth/login", json={"email": "login@careflow.test", "password": "wrongpass"})
    assert r.status_code == 401


def test_book_appointment():
    r = client.post("/appointments", json={
        "patient_name": "Arjun Kumar",
        "age": 35,
        "gender": "male",
        "phone": "+919876543210",
        "location": "Hyderabad",
        "scheduled_time": "2026-12-01T10:00:00",
        "notes": "Routine checkup",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["patient"]["name"] == "Arjun Kumar"
    assert data["token_number"] == 1  # First token of the day


def test_book_second_appointment_gets_token_2():
    client.post("/appointments", json={
        "patient_name": "First Patient",
        "phone": "+910000000001",
        "scheduled_time": "2026-12-02T09:00:00",
    })
    r = client.post("/appointments", json={
        "patient_name": "Second Patient",
        "phone": "+910000000002",
        "scheduled_time": "2026-12-02T10:00:00",
    })
    assert r.status_code == 201
    assert r.json()["token_number"] == 2


def test_get_appointment_by_id():
    r = client.post("/appointments", json={
        "patient_name": "Fetch Test",
        "phone": "+911111111111",
        "scheduled_time": "2026-12-03T11:00:00",
    })
    appt_id = r.json()["id"]
    r2 = client.get(f"/appointments/{appt_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == appt_id


def test_list_appointments_requires_auth():
    r = client.get("/appointments")
    assert r.status_code == 401


def test_list_appointments_with_auth(doctor_token):
    r = client.get("/appointments", headers={"Authorization": f"Bearer {doctor_token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_update_appointment_status(doctor_token):
    booking = client.post("/appointments", json={
        "patient_name": "Update Patient",
        "phone": "+912222222222",
        "scheduled_time": "2026-12-04T09:30:00",
    })
    appt_id = booking.json()["id"]
    r = client.put(f"/appointments/{appt_id}",
        json={"status": "checked_in"},
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "checked_in"


def test_cancel_appointment(doctor_token):
    booking = client.post("/appointments", json={
        "patient_name": "Cancel Patient",
        "phone": "+913333333333",
        "scheduled_time": "2026-12-05T14:00:00",
    })
    appt_id = booking.json()["id"]
    r = client.delete(f"/appointments/{appt_id}",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert r.status_code == 204
    # Verify it's cancelled
    get_r = client.get(f"/appointments/{appt_id}")
    assert get_r.json()["status"] == "cancelled"


def test_get_dashboard_stats(doctor_token):
    r = client.get("/queue/stats", headers={"Authorization": f"Bearer {doctor_token}"})
    assert r.status_code == 200
    data = r.json()
    assert "today_total" in data
    assert "week_total" in data


def test_appointment_not_found():
    r = client.get("/appointments/99999")
    assert r.status_code == 404
