from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_page():
    response = client.get("/")
    assert response.status_code == 200
    assert b"aClick" in response.content


def test_login_and_patient_booking_flow():
    login = client.post("/api/auth/login", json={"email":"patient@aclick.demo","password":"password"})
    assert login.status_code == 200
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    booking = client.post("/api/bookings", headers=headers, json={"type":"General Consultation","service_id":1,"amount":25,"details":"Routine check","scheduled_at":"2026-12-01 10:00"})
    assert booking.status_code == 200
    assert len(client.get("/api/bookings", headers=headers).json()) >= 1


def test_admin_stats_require_admin_role():
    patient = client.post("/api/auth/login", json={"email":"patient@aclick.demo","password":"password"}).json()
    response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {patient['token']}"})
    assert response.status_code == 403
