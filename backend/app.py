import logging
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database import db
from routes import make_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
)
logger = logging.getLogger("urbanshield")


def create_app(config_class=Config):
    """
    Application factory for UrbanShield backend.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    
    # Enable CORS for local development (supports Vite, React, Next, etc.)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Import and register route blueprints under /api
    from routes.system import system_bp
    from routes.dashboard import dashboard_bp
    from routes.assets import assets_bp
    from routes.risks import risks_bp
    from routes.recommendations import recommendations_bp
    from routes.simulations import simulations_bp

    api_prefix = config_class.API_PREFIX  # "/api"
    app.register_blueprint(system_bp, url_prefix=api_prefix)
    app.register_blueprint(dashboard_bp, url_prefix=api_prefix)
    app.register_blueprint(assets_bp, url_prefix=api_prefix)
    app.register_blueprint(risks_bp, url_prefix=api_prefix)
    app.register_blueprint(recommendations_bp, url_prefix=api_prefix)
    app.register_blueprint(simulations_bp, url_prefix=api_prefix)

    # Centralized HTTP Error Handlers
    @app.errorhandler(400)
    def handle_bad_request(e):
        return make_error("BAD_REQUEST", str(e.description if hasattr(e, 'description') else "Bad request"), status_code=400)

    @app.errorhandler(404)
    def handle_not_found(e):
        return make_error("NOT_FOUND", "The requested API endpoint was not found", status_code=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return make_error("METHOD_NOT_ALLOWED", "HTTP method is not allowed on this endpoint", status_code=405)

    @app.errorhandler(500)
    def handle_internal_server_error(e):
        logger.error("Unhandled server exception: %s", str(e))
        return make_error("INTERNAL_SERVER_ERROR", "An unexpected server error occurred", status_code=500)

    # Root health probe
    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "name": "UrbanShield API",
            "status": "online",
            "version": Config.API_VERSION,
            "docs_info": "Access backend endpoints under /api"
        })

    # Create tables automatically
    with app.app_context():
        db.create_all()
        logger.info("Database tables verified.")

    return app


if __name__ == "__main__":
    app = create_app()
    port = Config.PORT
    logger.info("Starting UrbanShield API Server on port %d (MOCK_MODE=%s)...", port, Config.MOCK_MODE)
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
