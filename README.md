# MEDUSA-X — Setup Instructions

## Prerequisites
- **Python 3.11+** (with pip)
- **Node.js 20+** (with npm)
- **MySQL 8.0+**
- An SMS provider account (Twilio or MSG91) **OR** set `MOCK_OTP=true` for local development

---

## 1 — Database Setup

```bash
# Log into MySQL and run the migration:
mysql -u root -p < backend/migrations/001_initial_schema.sql

# Then generate a real bcrypt password hash for the demo doctor:
python -c "import bcrypt; print(bcrypt.hashpw(b'doctor123', bcrypt.gensalt()).decode())"
# Replace the placeholder hash in the SQL, or use Flask seed (step 3).
```

---

## 2 — Backend Setup (Flask)

```bash
cd backend

# Copy and edit environment variables:
copy .env.example .env
# Edit .env — set DATABASE_URL, JWT_SECRET_KEY, SMS provider details, MOCK_OTP=true for dev

# Create a virtual environment:
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies:
pip install -r requirements.txt

# Create database tables (Flask-Migrate):
set FLASK_APP=run.py
flask db init
flask db migrate -m "initial schema"
flask db upgrade

# Seed the demo doctor account (DR-001 / doctor123):
flask seed

# Run the Flask development server:
python run.py
# Backend available at http://localhost:5000
```

---

## 3 — Frontend Setup (React + Vite)

```bash
cd frontend

# Install Node packages:
npm install

# Start the Vite dev server (proxies /api → Flask on :5000):
npm run dev
# Frontend available at http://localhost:3000
```

---

## 4 — Application Workflow

### Doctor Flow
1. Open **http://localhost:3000** → click **Doctor Login**
2. Log in with `DR-001` / `doctor123`
3. Use **Register New Patient** — enter the patient's mobile number; this is the number used for OTP login
4. Add visits, prescriptions, test results, and upload medical documents

### Patient Flow
1. Open **http://localhost:3000** → click **Patient Login**
2. Enter registered mobile number → click **Send OTP**
3. In development (MOCK_OTP=true): the OTP is printed in the Flask console and returned in the API response
4. Enter the OTP → **Verify OTP & Login**
5. Patient dashboard shows: Profile, Medical History, Test Results, My Documents, Notifications

---

## 5 — SMS Configuration

### Mock Mode (Development)
```
MOCK_OTP=true
```
OTP is logged to the Flask console and returned in the `/send-otp` JSON response as `mock_otp`.
**Never deploy MOCK_OTP=true to production.**

### Twilio
```
MOCK_OTP=false
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+1xxxxxxxxxx
```

### MSG91 (India)
```
MOCK_OTP=false
MSG91_AUTH_KEY=xxxxxxxxxxxx
MSG91_SENDER_ID=MEDUSA
MSG91_TEMPLATE_ID=xxxxxxxxxxxx
```

---

## 6 — API Reference

### Patient Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/patient-auth/send-otp` | Send OTP to registered mobile |
| POST | `/api/patient-auth/verify-otp` | Verify OTP → JWT access token |
| POST | `/api/patient-auth/resend-otp` | Resend OTP (rate limited, 60s cooldown) |
| POST | `/api/patient-auth/logout` | Invalidate patient session |

### Patient Portal (JWT required: patient role)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/patient/profile` | Patient demographic profile |
| GET | `/api/patient/medical-history` | All visits, diagnoses, prescriptions |
| GET | `/api/patient/test-results` | Lab and investigation results |
| GET | `/api/patient/documents` | Medical documents list |
| GET | `/api/patient/documents/<file_ref>/download` | Secure authenticated file download |
| GET | `/api/patient/notifications` | Notifications with unread count |
| POST | `/api/patient/notifications/<id>/read` | Mark notification as read |

### Doctor Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/doctor-auth/login` | Doctor ID + password login |
| POST | `/api/doctor-auth/logout` | End doctor session |
| GET | `/api/doctor-auth/me` | Current doctor info |

### Doctor Dashboard (JWT required: doctor role)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/doctor/patients` | List all patients (search + pagination) |
| POST | `/api/doctor/patients` | Register new patient (sets mobile for OTP) |
| GET | `/api/doctor/patients/<id>` | Get patient profile |
| PUT | `/api/doctor/patients/<id>` | Update patient profile |
| DELETE | `/api/doctor/patients/<id>` | Deactivate patient |
| GET | `/api/doctor/patients/<id>/full-record` | Full patient record |
| POST | `/api/doctor/patients/<id>/visits` | Add visit + prescriptions |
| POST | `/api/doctor/patients/<id>/documents` | Upload medical document |
| POST | `/api/doctor/patients/<id>/test-results` | Add test result |

---

## 7 — Security Notes

- OTPs are **bcrypt-hashed** before storage — plain-text OTPs are never persisted
- OTP expires in **5 minutes**, max **5 incorrect attempts**, **60-second resend cooldown**
- OTP requests are **rate-limited** (5/min, 20/hr on send; 10/min on verify)
- JWT tokens contain `role` claim — backend enforces `patient` vs `doctor` on every endpoint
- Document downloads require a valid patient JWT and confirm document ownership
- Uploaded files are stored with UUID filenames in the `backend/uploads/` directory
- Use **HTTPS + a secret JWT key** in production
- Enable Redis-backed JWT blocklist in production (replace the in-memory set in `patient_auth.py`)
