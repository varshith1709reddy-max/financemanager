import os
import sys
from flask import Flask, render_template, jsonify, session

# Add current directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import init_db
from backend.auth import auth_bp, generate_auth_token
from backend.routes_accounts import accounts_bp
from backend.routes_transactions import transactions_bp
from backend.routes_budgets import budgets_bp
from backend.routes_goals import goals_bp
from backend.routes_dashboard import dashboard_bp
from backend.routes_reports import reports_bp
from backend.routes_categories import categories_bp
from backend.seed_data import seed_demo_user

def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
        static_folder=os.path.join(BASE_DIR, "frontend", "static")
    )

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "finance-manager-super-secret-key-2026")
    
    if test_config:
        app.config.update(test_config)

    # Initialize DB
    db_path = app.config.get("DATABASE_PATH")
    init_db(db_path)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(categories_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "healthy",
            "service": "Finance Manager",
            "version": "1.0.0"
        }), 200

    @app.route("/api/demo/seed", methods=["POST"])
    def seed_demo():
        user_id = seed_demo_user()
        token = generate_auth_token(user_id)
        session["user_id"] = user_id
        return jsonify({
            "message": "Demo data ready",
            "token": token,
            "user": {
                "id": user_id,
                "username": "demo",
                "email": "demo@student.college.edu",
                "full_name": "Rahul Sharma (Student)",
                "currency": "INR"
            }
        }), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found", "code": "NOT_FOUND"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error", "code": "SERVER_ERROR"}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    # Seed demo user on startup if not present
    seed_demo_user()
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Personal Finance Manager on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
