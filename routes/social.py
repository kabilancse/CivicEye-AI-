"""
Social Explorer routes.

GET  /api/social/patterns
GET  /api/social/relationships
GET  /api/social/impact
GET  /api/social/trends
POST /api/social/simulation
"""

from flask import Blueprint, jsonify, request

from services.analysis_service import (
    get_social_impact,
    get_social_patterns,
    get_social_relationships,
    get_social_trends,
)
from services.simulation_service import run_whatif_simulation

social_bp = Blueprint("social", __name__, url_prefix="/api/social")


@social_bp.route("/patterns", methods=["GET"])
def patterns():
    top_n = request.args.get("limit", default=8, type=int)
    return jsonify(get_social_patterns(top_n=top_n)), 200


@social_bp.route("/relationships", methods=["GET"])
def relationships():
    return jsonify(get_social_relationships()), 200


@social_bp.route("/impact", methods=["GET"])
def impact():
    pattern_id = request.args.get("pattern_id")
    return jsonify(get_social_impact(pattern_id=pattern_id)), 200


@social_bp.route("/trends", methods=["GET"])
def trends():
    area = request.args.get("area")
    return jsonify(get_social_trends(area=area)), 200


@social_bp.route("/simulation", methods=["POST"])
def simulation():
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "Request body must include at least one scenario field"}), 400

    area = data.pop("area", None)
    outcome_field = data.pop("outcome_field", None)

    if not data:
        return jsonify({"error": "Provide at least one indicator value to simulate "
                                  "(e.g. transport_access, internet_access)"}), 400

    try:
        result = run_whatif_simulation(data, area=area, outcome_field=outcome_field)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(result), 200
