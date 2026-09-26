"""
Action Center routes — an INTERVENTION workflow for authorized
organizations/admins responding to identified patterns. Not a
complaint/ticket-management system: there is no "citizen files a
complaint" path here. Citizens only ever read this data (surfaced via
Citizen Mode); only organization/admin roles can write to it.

GET  /api/actions
POST /api/actions
PUT  /api/actions/{id}
"""

from flask import Blueprint, g, jsonify, request

from config import Config
from models.database import db_cursor
from services.auth_service import login_required, roles_required

actions_bp = Blueprint("actions", __name__, url_prefix="/api/actions")


def _row_to_dict(row):
    return dict(row)


@actions_bp.route("", methods=["GET"])
def list_actions():
    """
    Publicly readable (citizens can view ongoing/verified interventions
    via this or the citizen feed) — filterable by area/status/problem_id.
    """
    area = request.args.get("area")
    status = request.args.get("status")
    problem_id = request.args.get("problem_id")

    query = "SELECT * FROM interventions WHERE 1=1"
    params = []
    if area:
        query += " AND area = ?"
        params.append(area)
    if status:
        query += " AND status = ?"
        params.append(status)
    if problem_id:
        query += " AND problem_id = ?"
        params.append(problem_id)
    query += " ORDER BY updated_at DESC"

    with db_cursor() as cur:
        cur.execute(query, params)
        rows = [_row_to_dict(r) for r in cur.fetchall()]

    return jsonify({"interventions": rows, "count": len(rows)}), 200


@actions_bp.route("", methods=["POST"])
@login_required
@roles_required(*Config.ACTION_CENTER_ROLES)
def create_action():
    """An authorized organization/admin proposes an intervention against an identified pattern."""
    data = request.get_json(silent=True) or {}
    problem_id = data.get("problem_id")
    title = (data.get("title") or "").strip()
    description = data.get("description")
    area = data.get("area")
    evidence = data.get("evidence")

    if not problem_id or not title:
        return jsonify({"error": "problem_id and title are required"}), 400

    organization_id = g.current_user["id"]

    with db_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO interventions (problem_id, title, description, area, organization_id, evidence)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (problem_id, title, description, area, organization_id, evidence),
        )
        new_id = cur.lastrowid
        cur.execute("SELECT * FROM interventions WHERE id = ?", (new_id,))
        row = cur.fetchone()

    return jsonify(_row_to_dict(row)), 201


@actions_bp.route("/<int:action_id>", methods=["PUT"])
@login_required
@roles_required(*Config.ACTION_CENTER_ROLES)
def update_action(action_id):
    """
    Update progress, status, or record an outcome. Only the organization
    that created the intervention, or a platform/data admin, may update it.
    Marking status 'verified' represents a verified-completed intervention.
    """
    with db_cursor() as cur:
        cur.execute("SELECT * FROM interventions WHERE id = ?", (action_id,))
        existing = cur.fetchone()

    if existing is None:
        return jsonify({"error": "Intervention not found"}), 404

    user = g.current_user
    if user["role"] not in Config.PLATFORM_ADMIN_ROLES and existing["organization_id"] != user["id"]:
        return jsonify({"error": "You may only update interventions you created"}), 403

    data = request.get_json(silent=True) or {}
    allowed_fields = ["title", "description", "status", "evidence", "progress_notes", "outcome"]
    valid_statuses = ["proposed", "in_progress", "completed", "verified"]

    if "status" in data and data["status"] not in valid_statuses:
        return jsonify({"error": f"status must be one of {valid_statuses}"}), 400

    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    params = list(updates.values()) + [action_id]

    with db_cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE interventions SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            params,
        )
        cur.execute("SELECT * FROM interventions WHERE id = ?", (action_id,))
        row = cur.fetchone()

    return jsonify(_row_to_dict(row)), 200
