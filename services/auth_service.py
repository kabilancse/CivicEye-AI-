"""
Authentication service.

Uses werkzeug's password hashing (bundled with Flask) and a simple
opaque random token stored in SQLite with an expiry — enough for an
academic-project MVP without pulling in a JWT dependency. Swappable
for JWT later without changing the route layer's interface.
"""

import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models.database import db_cursor


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def create_user(username: str, email: str, password: str, role: str, organization_name: str = None) -> dict:
    if role not in Config.VALID_ROLES:
        raise ValueError(f"Invalid role. Must be one of {Config.VALID_ROLES}")

    password_hash = hash_password(password)
    with db_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO users (username, email, password_hash, role, organization_name)
               VALUES (?, ?, ?, ?, ?)""",
            (username, email, password_hash, role, organization_name),
        )
        user_id = cur.lastrowid

    return {"id": user_id, "username": username, "email": email, "role": role}


def authenticate(username_or_email: str, password: str) -> dict | None:
    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username_or_email, username_or_email),
        )
        row = cur.fetchone()

    if row is None or not verify_password(password, row["password_hash"]):
        return None

    return dict(row)


def issue_token(user_id: int) -> str:
    token = secrets.token_hex(32)
    expires_at = (datetime.utcnow() + timedelta(hours=Config.TOKEN_LIFETIME_HOURS)).isoformat()
    with db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO auth_tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at),
        )
    return token


def get_user_from_token(token: str) -> dict | None:
    with db_cursor() as cur:
        cur.execute("SELECT * FROM auth_tokens WHERE token = ?", (token,))
        token_row = cur.fetchone()
        if token_row is None:
            return None
        if datetime.fromisoformat(token_row["expires_at"]) < datetime.utcnow():
            return None
        cur.execute("SELECT * FROM users WHERE id = ?", (token_row["user_id"],))
        user_row = cur.fetchone()
        return dict(user_row) if user_row else None


def _extract_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):].strip()
    return request.headers.get("X-Auth-Token")


def login_required(f):
    """Attaches the authenticated user to flask.g.current_user, or 401s."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Authentication token required"}), 401
        user = get_user_from_token(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return wrapper


def roles_required(*allowed_roles):
    """Combine with login_required (put this decorator closer to the function)."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if user is None:
                return jsonify({"error": "Authentication required"}), 401
            if user["role"] not in allowed_roles:
                return jsonify({"error": "Insufficient permissions for this action"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
