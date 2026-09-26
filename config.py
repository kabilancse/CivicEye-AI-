"""
Central configuration for CivicEye AI+ backend.
Keep secrets out of source control in a real deployment — this reads
from environment variables with safe local-dev fallbacks.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # --- General ---
    SECRET_KEY = os.environ.get("CIVICEYE_SECRET_KEY", "dev-secret-change-me")
    DEBUG = os.environ.get("CIVICEYE_DEBUG", "1") == "1"

    # --- Database ---
    DATABASE_PATH = os.path.join(BASE_DIR, "civiceye.db")

    # --- Data ---
    EDUCATION_CSV_PATH = os.path.join(BASE_DIR, "data", "education.csv")

    # --- Auth ---
    # Token lifetime for the simple auth-token scheme (see routes/auth.py)
    TOKEN_LIFETIME_HOURS = 12

    # --- AI / ML ---
    ANOMALY_CONTAMINATION = 0.15  # expected proportion of "unusual" area-years
    RANDOM_STATE = 42

    # Valid roles for registration / access control
    VALID_ROLES = ["citizen", "researcher", "organization", "platform_admin", "data_admin"]

    # Roles allowed to use the Action Center (create/update interventions)
    ACTION_CENTER_ROLES = ["organization", "platform_admin", "data_admin"]

    # Roles allowed to access admin-only endpoints
    PLATFORM_ADMIN_ROLES = ["platform_admin"]
    DATA_ADMIN_ROLES = ["data_admin", "platform_admin"]
