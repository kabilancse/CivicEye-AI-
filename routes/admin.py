"""
Admin routes.

Platform Administrator: manages users/roles and platform-level oversight.
Data & Intelligence Administrator: manages the underlying dataset and
can trigger re-runs of the AI pipeline.

GET   /api/admin/users                     (platform_admin)
PATCH /api/admin/users/<id>/role           (platform_admin)
GET   /api/admin/dataset/summary           (data_admin, platform_admin)
POST  /api/admin/dataset/reload            (data_admin, platform_admin)
GET   /api/admin/civic-items               (data_admin, platform_admin)
POST  /api/admin/civic-items               (data_admin, platform_admin)
"""

from flask import Blueprint, g, jsonify, request

from config import Config
from models.database import db_cursor
from services.auth_service import login_required, roles_required
from services.data_service import get_education_data

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ---------- Platform Administrator ----------

@admin_bp.route("/users", methods=["GET"])
@login_required
@roles_required(*Config.PLATFORM_ADMIN_ROLES)
def list_users():
    with db_cursor() as cur:
        cur.execute("SELECT id, username, email, role, organization_name, created_at FROM users ORDER BY created_at DESC")
        rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"users": rows, "count": len(rows)}), 200


@admin_bp.route("/users/<int:user_id>/role", methods=["PATCH"])
@login_required
@roles_required(*Config.PLATFORM_ADMIN_ROLES)
def update_user_role(user_id):
    data = request.get_json(silent=True) or {}
    new_role = data.get("role")
    if new_role not in Config.VALID_ROLES:
        return jsonify({"error": f"role must be one of {Config.VALID_ROLES}"}), 400

    with db_cursor(commit=True) as cur:
        cur.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        if cur.rowcount == 0:
            return jsonify({"error": "User not found"}), 404
        cur.execute("SELECT id, username, email, role FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()

    return jsonify(dict(row)), 200


# ---------- Data & Intelligence Administrator ----------

@admin_bp.route("/dataset/summary", methods=["GET"])
@login_required
@roles_required(*Config.DATA_ADMIN_ROLES)
def dataset_summary():
    df = get_education_data()
    return jsonify({
        "row_count": len(df),
        "areas": sorted(df["area"].unique().tolist()) if "area" in df.columns else [],
        "years_covered": [int(df["year"].min()), int(df["year"].max())] if "year" in df.columns else None,
        "columns": list(df.columns),
    }), 200


@admin_bp.route("/dataset/reload", methods=["POST"])
@login_required
@roles_required(*Config.DATA_ADMIN_ROLES)
def dataset_reload():
    """Forces a re-read + re-clean of the source CSV (e.g. after an update)."""
    df = get_education_data(force_reload=True)
    return jsonify({"message": "Dataset reloaded", "row_count": len(df)}), 200


@admin_bp.route("/civic-items", methods=["GET"])
@login_required
@roles_required(*Config.DATA_ADMIN_ROLES)
def list_civic_items_admin():
    with db_cursor() as cur:
        cur.execute("SELECT * FROM civic_items ORDER BY item_date DESC")
        rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"items": rows, "count": len(rows)}), 200


@admin_bp.route("/civic-items", methods=["POST"])
@login_required
@roles_required(*Config.DATA_ADMIN_ROLES)
def create_civic_item():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    item_type = data.get("item_type")
    source = (data.get("source") or "").strip()
    valid_types = ["local_info", "identified_pattern", "ongoing_initiative", "completed_initiative"]

    if not title or item_type not in valid_types or not source:
        return jsonify({"error": f"title, source, and item_type (one of {valid_types}) are required"}), 400

    with db_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO civic_items (title, description, area, item_type, source, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, data.get("description"), data.get("area"), item_type, source,
             data.get("status", "active")),
        )
        new_id = cur.lastrowid
        cur.execute("SELECT * FROM civic_items WHERE id = ?", (new_id,))
        row = cur.fetchone()

    return jsonify(dict(row)), 201
