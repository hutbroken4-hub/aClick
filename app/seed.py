from app.database import SessionLocal
from app.models import Partner, Service, User
from app.security import hash_password


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            partners = [
                Partner(name="CityCare Hospital", type="hospital", status="verified", address="Central District", latitude=23.8103, longitude=90.4125, rating=4.8),
                Partner(name="HealthFirst Laboratory", type="lab", status="verified", address="North Avenue", latitude=23.7925, longitude=90.4078, rating=4.7),
                Partner(name="CarePlus Pharmacy", type="pharmacy", status="verified", address="Market Road", latitude=23.7777, longitude=90.3995, rating=4.6),
                Partner(name="Rapid Ambulance", type="ambulance", status="verified", address="Emergency Network", latitude=23.8100, longitude=90.4100, rating=4.9),
                Partner(name="Dr. Sara Rahman", type="doctor", status="verified", address="CityCare Hospital", latitude=23.8103, longitude=90.4125, rating=4.9),
            ]
            db.add_all(partners)
            db.flush()
            db.add_all([
                User(name="Demo Patient", email="patient@aclick.demo", phone="01700000001", role="patient", password_hash=hash_password("password")),
                User(name="Partner Admin", email="partner@aclick.demo", phone="01700000002", role="hospital", partner_id=partners[0].id, password_hash=hash_password("password")),
                User(name="System Admin", email="admin@aclick.demo", phone="01700000003", role="admin", password_hash=hash_password("password")),
                User(name="Dr. Sara Rahman", email="doctor@aclick.demo", phone="01700000004", role="doctor", partner_id=partners[4].id, password_hash=hash_password("password")),
                User(name="Rapid Ambulance", email="ambulance@aclick.demo", phone="01700000005", role="ambulance", partner_id=partners[3].id, password_hash=hash_password("password")),
            ])
            db.add_all([
                Service(partner_id=partners[4].id, name="General Consultation", category="appointment", description="30-minute doctor consultation", price=25),
                Service(partner_id=partners[0].id, name="Health Check-up Package", category="hospital", description="Complete routine health screening", price=120),
                Service(partner_id=partners[1].id, name="Complete Blood Count", category="lab", description="CBC test with home collection", price=18),
                Service(partner_id=partners[2].id, name="Medicine Delivery", category="pharmacy", description="Prescription fulfillment and delivery", price=5),
                Service(partner_id=partners[3].id, name="Advanced Life Support", category="ambulance", description="Emergency ALS ambulance", price=80),
                Service(partner_id=partners[4].id, name="Video Consultation", category="video", description="Secure telemedicine consultation", price=30),
            ])
            db.commit()
    finally:
        db.close()
