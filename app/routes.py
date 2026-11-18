from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking, HealthRecord, Partner, PharmacyOrder, Service, User
from app.security import hash_password, hash_token, verify_password
import secrets

router = APIRouter()


class AuthInput(BaseModel):
    email: str
    password: str
    name: str | None = None
    role: str = "patient"
    phone: str | None = None


class BookingInput(BaseModel):
    type: str
    partner_id: int | None = None
    service_id: int | None = None
    details: str | None = None
    scheduled_at: str | None = None
    amount: float = 0
    latitude: float | None = None
    longitude: float | None = None


class RecordInput(BaseModel):
    title: str
    record_type: str
    content: str | None = None
    file_url: str | None = None


class OrderInput(BaseModel):
    medicines: str
    partner_id: int | None = None
    delivery: str = "delivery"


class StatusInput(BaseModel):
    status: str


def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    token_hash = hash_token(authorization.removeprefix("Bearer ").strip())
    user = db.query(User).filter(User.token_hash == token_hash).first()
    if not user:
        raise HTTPException(401, "Invalid or expired session")
    return user


def as_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


@router.post("/auth/register")
def register(data: AuthInput, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    role = data.role if data.role in {"patient", "doctor", "hospital", "lab", "pharmacy", "ambulance", "admin"} else "patient"
    user = User(name=data.name or data.email.split("@")[0], email=data.email.lower(), phone=data.phone,
                role=role, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return login(AuthInput(email=data.email, password=data.password), db)


@router.post("/auth/login")
def login(data: AuthInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    token = secrets.token_urlsafe(32)
    user.token_hash = hash_token(token)
    db.commit()
    return {"token": token, "user": as_dict(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return as_dict(user)


@router.get("/services")
def services(category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Service).filter(Service.available == True)
    if category:
        query = query.filter(Service.category == category)
    return [as_dict(s) for s in query.all()]


@router.get("/partners")
def partners(type: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Partner).filter(Partner.status == "verified")
    if type:
        query = query.filter(Partner.type == type)
    return [as_dict(p) for p in query.all()]


@router.post("/bookings")
def create_booking(data: BookingInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "patient":
        raise HTTPException(403, "Patient access required")
    booking = Booking(patient_id=user.id, partner_id=data.partner_id, service_id=data.service_id,
                      type=data.type, details=data.details, scheduled_at=data.scheduled_at,
                      amount=data.amount, latitude=data.latitude, longitude=data.longitude)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return as_dict(booking)


@router.get("/bookings")
def bookings(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(Booking)
    if user.role == "patient":
        query = query.filter(Booking.patient_id == user.id)
    elif user.role != "admin":
        query = query.filter(Booking.partner_id == user.partner_id)
    return [as_dict(b) for b in query.order_by(Booking.created_at.desc()).all()]


@router.patch("/bookings/{booking_id}/status")
def update_booking_status(booking_id: int, data: StatusInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    if user.role not in {"admin", "ambulance", "doctor", "hospital", "lab"}:
        raise HTTPException(403, "Provider access required")
    allowed = {"pending", "confirmed", "in-progress", "completed", "cancelled", "arriving", "arrived"}
    if data.status not in allowed:
        raise HTTPException(400, "Invalid status")
    booking.status = data.status
    db.commit()
    return as_dict(booking)


@router.post("/records")
def create_record(data: RecordInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "patient":
        raise HTTPException(403, "Patient access required")
    record = HealthRecord(patient_id=user.id, title=data.title, record_type=data.record_type,
                          content=data.content, file_url=data.file_url)
    db.add(record)
    db.commit()
    db.refresh(record)
    return as_dict(record)


@router.get("/records")
def records(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "patient":
        raise HTTPException(403, "Patient access required")
    return [as_dict(r) for r in db.query(HealthRecord).filter(HealthRecord.patient_id == user.id).order_by(HealthRecord.created_at.desc()).all()]


@router.post("/pharmacy/orders")
def pharmacy_order(data: OrderInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "patient":
        raise HTTPException(403, "Patient access required")
    order = PharmacyOrder(patient_id=user.id, partner_id=data.partner_id, medicines=data.medicines,
                          delivery=data.delivery)
    db.add(order)
    db.commit()
    db.refresh(order)
    return as_dict(order)


@router.get("/pharmacy/orders")
def pharmacy_orders(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(PharmacyOrder)
    if user.role == "patient":
        query = query.filter(PharmacyOrder.patient_id == user.id)
    elif user.role != "admin":
        query = query.filter(PharmacyOrder.partner_id == user.partner_id)
    return [as_dict(o) for o in query.order_by(PharmacyOrder.created_at.desc()).all()]


@router.get("/admin/stats")
def admin_stats(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
    return {
        "users": db.query(func.count(User.id)).scalar() or 0,
        "partners": db.query(func.count(Partner.id)).scalar() or 0,
        "verified_partners": db.query(func.count(Partner.id)).filter(Partner.status == "verified").scalar() or 0,
        "bookings": db.query(func.count(Booking.id)).scalar() or 0,
        "orders": db.query(func.count(PharmacyOrder.id)).scalar() or 0,
        "health_records": db.query(func.count(HealthRecord.id)).scalar() or 0,
    }


@router.get("/admin/partners")
def admin_partners(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
    return [as_dict(p) for p in db.query(Partner).order_by(Partner.created_at.desc()).all()]


@router.patch("/admin/partners/{partner_id}/status")
def partner_status(partner_id: int, data: StatusInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(404, "Partner not found")
    if data.status not in {"pending", "verified", "suspended"}:
        raise HTTPException(400, "Invalid status")
    partner.status = data.status
    db.commit()
    return as_dict(partner)
