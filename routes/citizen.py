"""
Citizen Mode routes.

GET /api/citizen/statistics
GET /api/citizen/problems
"""

from flask import Blueprint, jsonify, request

from models.database import db_cursor
from services.analysis_service import get_citizen_statistics

citizen_bp = Blueprint("citizen", __name__, url_prefix="/api/citizen")


@citizen_bp.route("/statistics", methods=["GET"])
def statistics():
    return jsonify(get_citizen_statistics()), 200


@citizen_bp.route("/problems", methods=["GET"])
def problems():
    """
    Returns Citizen Mode content items: local civic info, identified
    patterns/issues, ongoing initiatives, and verified completed
    initiatives. Every item carries source/date/type/status so
    AI-derived content is never mistaken for live news.
    """
    area = request.args.get("area")
    item_type = request.args.get("type")  # local_info | identified_pattern | ongoing_initiative | completed_initiative

    query = "SELECT * FROM civic_items WHERE 1=1"
    params = []
    if area:
        query += " AND area = ?"
        params.append(area)
    if item_type:
        query += " AND item_type = ?"
        params.append(item_type)
    query += " ORDER BY item_date DESC"

    with db_cursor() as cur:
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]

    for r in rows:
        r["is_ai_generated_content"] = r["source"] not in ("Official Records",)

    return jsonify({"items": rows, "count": len(rows)}), 200
