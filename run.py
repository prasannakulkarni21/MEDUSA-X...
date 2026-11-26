"""MEDUSA-X Flask entrypoint"""
from app import create_app, db
from app.models import Doctor, Patient
import bcrypt
import os

app = create_app()


@app.cli.command("seed")
def seed_db():
    """Seed a demo doctor account for development."""
    with app.app_context():
        db.create_all()
        if not Doctor.query.filter_by(doctor_id="DR-001").first():
            pw = bcrypt.hashpw("doctor123".encode(), bcrypt.gensalt()).decode()
            doc = Doctor(
                doctor_id="DR-001",
                name="Dr. Admin",
                specialization="General Medicine",
                email="doctor@medusa-x.local",
                password_hash=pw,
            )
            db.session.add(doc)
            db.session.commit()
            print("✓ Seeded Doctor DR-001 / password: doctor123")
        else:
            print("Doctor DR-001 already exists.")


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_ENV") == "development", port=5000)
