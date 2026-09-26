"""
CivicEye AI+ backend entry point.

Run:
    python app.py

The API will be available at http://localhost:5000
See API_CONTRACT.md for the full endpoint reference.
"""

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from models.database import init_db, seed_demo_civic_items
from routes.actions import actions_bp
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.citizen import citizen_bp
from routes.social import social_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)  # open CORS for MVP/demo; tighten origins before any real deployment

    app.register_blueprint(auth_bp)
    app.register_blueprint(citizen_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(actions_bp)
    app.register_blueprint(admin_bp)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "CivicEye AI+ backend"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        init_db()
        seed_demo_civic_items()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, port=5000)
