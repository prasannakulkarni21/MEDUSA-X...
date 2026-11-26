"""
MEDUSA-X Flask Application Factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])


def create_app():
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/medusa_x"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False   # handled per-token
    app.config["UPLOAD_FOLDER"] = os.path.join(
        os.path.dirname(__file__), "..", os.getenv("UPLOAD_FOLDER", "uploads")
    )
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH_MB", 25)) * 1024 * 1024

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173"]}})

    # ── Blueprints ────────────────────────────────────────────────────────────
    from app.routes.patient_auth import patient_auth_bp
    from app.routes.doctor_auth import doctor_auth_bp
    from app.routes.patient_portal import patient_portal_bp
    from app.routes.doctor_dashboard import doctor_dashboard_bp

    app.register_blueprint(patient_auth_bp, url_prefix="/api/patient-auth")
    app.register_blueprint(doctor_auth_bp, url_prefix="/api/doctor-auth")
    app.register_blueprint(patient_portal_bp, url_prefix="/api/patient")
    app.register_blueprint(doctor_dashboard_bp, url_prefix="/api/doctor")

    # ── Health ────────────────────────────────────────────────────────────────
    @app.get("/api/health")
    def health():
        return {"status": "ok", "app": "MEDUSA-X"}

    return app
