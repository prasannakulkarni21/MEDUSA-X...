"""
MEDUSA-X SQLAlchemy Models
"""
import os
import uuid
from datetime import datetime, timezone
from app import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(150))
    email = db.Column(db.String(200), unique=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    patients = db.relationship("Patient", back_populates="doctor", lazy="dynamic")
    visits = db.relationship("PatientVisit", back_populates="doctor", lazy="dynamic")

    def __repr__(self):
        return f"<Doctor {self.doctor_id}>"


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    patient_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(200))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(30))
    address = db.Column(db.Text)
    blood_group = db.Column(db.String(10))
    emergency_contact = db.Column(db.String(100))
    medical_history_notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    doctor = db.relationship("Doctor", back_populates="patients")
    otp_records = db.relationship("OtpVerification", back_populates="patient", lazy="dynamic",
                                  cascade="all, delete-orphan")
    visits = db.relationship("PatientVisit", back_populates="patient", lazy="dynamic",
                              cascade="all, delete-orphan")
    documents = db.relationship("MedicalDocument", back_populates="patient", lazy="dynamic",
                                cascade="all, delete-orphan")
    test_results = db.relationship("TestResult", back_populates="patient", lazy="dynamic",
                                   cascade="all, delete-orphan")
    notifications = db.relationship("PatientNotification", back_populates="patient", lazy="dynamic",
                                    cascade="all, delete-orphan")

    def age(self):
        if not self.date_of_birth:
            return None
        today = datetime.now(timezone.utc).date()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def to_profile_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "phone": self.phone,
            "email": self.email,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age": self.age(),
            "gender": self.gender,
            "address": self.address,
            "blood_group": self.blood_group,
            "emergency_contact": self.emergency_contact,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Patient {self.patient_id}>"


class OtpVerification(db.Model):
    __tablename__ = "otp_verifications"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=False)
    otp_hash = db.Column(db.String(255), nullable=False)   # bcrypt hash — NEVER store plain OTP
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0)
    verified_at = db.Column(db.DateTime, nullable=True)
    last_sent_at = db.Column(db.DateTime, default=utcnow)
    created_at = db.Column(db.DateTime, default=utcnow)

    patient = db.relationship("Patient", back_populates="otp_records")

    def is_expired(self):
        return utcnow() > self.expires_at

    def is_verified(self):
        return self.verified_at is not None

    def __repr__(self):
        return f"<OTP patient_id={self.patient_id} expires={self.expires_at}>"


class PatientVisit(db.Model):
    __tablename__ = "patient_visits"

    id = db.Column(db.Integer, primary_key=True)
    visit_ref = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=True)
    visit_date = db.Column(db.Date, nullable=False)
    visit_type = db.Column(db.String(100), default="OPD")
    chief_complaint = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    treatment_plan = db.Column(db.Text)
    clinical_notes = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    patient = db.relationship("Patient", back_populates="visits")
    doctor = db.relationship("Doctor", back_populates="visits")
    prescriptions = db.relationship("Prescription", back_populates="visit", lazy="dynamic",
                                    cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "visit_ref": self.visit_ref,
            "visit_date": self.visit_date.isoformat() if self.visit_date else None,
            "visit_type": self.visit_type,
            "chief_complaint": self.chief_complaint,
            "diagnosis": self.diagnosis,
            "treatment_plan": self.treatment_plan,
            "clinical_notes": self.clinical_notes,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "doctor_name": self.doctor.name if self.doctor else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("patient_visits.id"), nullable=False, index=True)
    medication_name = db.Column(db.String(300), nullable=False)
    dosage = db.Column(db.String(100))
    frequency = db.Column(db.String(100))
    duration = db.Column(db.String(100))
    instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)

    visit = db.relationship("PatientVisit", back_populates="prescriptions")

    def to_dict(self):
        return {
            "id": self.id,
            "visit_id": self.visit_id,
            "visit_date": self.visit.visit_date.isoformat() if self.visit and self.visit.visit_date else None,
            "medication_name": self.medication_name,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "duration": self.duration,
            "instructions": self.instructions,
        }


class MedicalDocument(db.Model):
    __tablename__ = "medical_documents"

    CATEGORIES = [
        "PDF Medical Report",
        "Laboratory Report",
        "Prescription",
        "Admission Note",
        "Discharge Summary",
        "Progress Note",
        "Scanned Medical Document",
    ]

    id = db.Column(db.Integer, primary_key=True)
    file_ref = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("patient_visits.id"), nullable=True)
    uploaded_by_doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=True)
    category = db.Column(db.String(100), nullable=False, default="PDF Medical Report")
    original_filename = db.Column(db.String(500), nullable=False)
    stored_filename = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(100))
    file_size_bytes = db.Column(db.BigInteger)
    description = db.Column(db.Text)
    is_visible_to_patient = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    patient = db.relationship("Patient", back_populates="documents")

    def to_dict(self, include_download_url=True):
        d = {
            "id": self.id,
            "file_ref": self.file_ref,
            "category": self.category,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "file_size_bytes": self.file_size_bytes,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_download_url:
            d["download_url"] = f"/api/patient/documents/{self.file_ref}/download"
        return d


class TestResult(db.Model):
    __tablename__ = "test_results"

    id = db.Column(db.Integer, primary_key=True)
    result_ref = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("patient_visits.id"), nullable=True)
    test_name = db.Column(db.String(300), nullable=False)
    test_date = db.Column(db.Date)
    result_summary = db.Column(db.Text)
    result_value = db.Column(db.String(200))
    reference_range = db.Column(db.String(200))
    status = db.Column(db.String(50), default="Pending")   # Pending / Normal / Abnormal / Critical
    reviewed_by_doctor = db.Column(db.Boolean, default=False)
    document_id = db.Column(db.Integer, db.ForeignKey("medical_documents.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    patient = db.relationship("Patient", back_populates="test_results")

    def to_dict(self):
        return {
            "id": self.id,
            "result_ref": self.result_ref,
            "test_name": self.test_name,
            "test_date": self.test_date.isoformat() if self.test_date else None,
            "result_summary": self.result_summary,
            "result_value": self.result_value,
            "reference_range": self.reference_range,
            "status": self.status,
            "reviewed_by_doctor": self.reviewed_by_doctor,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PatientNotification(db.Model):
    __tablename__ = "patient_notifications"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    title = db.Column(db.String(300), nullable=False)
    message = db.Column(db.Text)
    notification_type = db.Column(db.String(50), default="info")
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    patient = db.relationship("Patient", back_populates="notifications")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
