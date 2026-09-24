from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS

from config.config import get_config
from extensions.database import db


def create_app():
    app = Flask(__name__)
    config_class = get_config()
    if hasattr(config_class, "__init__") and config_class.__name__ == "ProductionConfig":
        config_class()  # runs fail-fast validation (real secrets, non-SQLite DB)
    app.config.from_object(config_class)

    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)
    CORS(app)

    # Import models so SQLAlchemy/Flask-Migrate can discover every table.
    import models  # noqa: F401

    from routes.auth_routes import auth_bp
    from routes.issue_routes import issue_bp
    from routes.vehicle_routes import vehicle_bp
    from routes.driver_routes import driver_bp
    from routes.hub_routes import hub_bp
    from routes.charging_routes import charging_bp
    from routes.maintenance_routes import maintenance_bp
    from routes.ai_routes import ai_bp
    from routes.analytics_routes import analytics_bp
    from routes.notification_routes import notification_bp
    from routes.audit_routes import audit_bp
    from routes.user_routes import user_bp
    from routes.view_routes import view_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(issue_bp, url_prefix="/api/issues")
    app.register_blueprint(vehicle_bp, url_prefix="/api/vehicles")
    app.register_blueprint(driver_bp, url_prefix="/api/drivers")
    app.register_blueprint(hub_bp, url_prefix="/api/hubs")
    app.register_blueprint(charging_bp, url_prefix="/api/charging")
    app.register_blueprint(maintenance_bp, url_prefix="/api/maintenance")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(notification_bp, url_prefix="/api/notifications")
    app.register_blueprint(audit_bp, url_prefix="/api/audit-logs")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(view_bp)

    @app.route("/api/health")
    def health():
        return jsonify({"success": True, "message": "API is running"}), 200

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "message": "Bad request", "errors": {}}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found", "errors": {}}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "message": "Internal server error", "errors": {}}), 500

    return app
