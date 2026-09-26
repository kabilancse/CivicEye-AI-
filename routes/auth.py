"""
Auth routes.

POST /api/auth/register
POST /api/auth/login
"""

import sqlite3

from flask import Blueprint, g, jsonify, request

from config import Config
from services.auth_service import authenticate, create_user, issue_token, login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role") or "citizen"
    organization_name = data.get("organization_name")

    if not username or not email or not password:
        return jsonify({"error": "username, email and password are required"}), 400
    if role not in Config.VALID_ROLES:
        return jsonify({"error": f"role must be one of {Config.VALID_ROLES}"}), 400
    if role == "organization" and not organization_name:
        return jsonify({"error": "organization_name is required for the organization role"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400

    try:
        user = create_user(username, email, password, role, organization_name)
    except sqlite3.IntegrityError:
        return jsonify({"error": "username or email already registered"}), 409
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    token = issue_token(user["id"])
    return jsonify({"user": user, "token": token}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "username/email and password are required"}), 400

    user = authenticate(identifier, password)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    token = issue_token(user["id"])
    return jsonify({
        "user": {
            "id": user["id"], "username": user["username"], "email": user["email"],
            "role": user["role"], "organization_name": user["organization_name"],
        },
        "token": token,
    }), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user = g.current_user
    return jsonify({
        "id": user["id"], "username": user["username"], "email": user["email"],
        "role": user["role"], "organization_name": user["organization_name"],
    }), 200
