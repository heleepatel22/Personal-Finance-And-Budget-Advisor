import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from config import Config
from extensions import db, login_manager, mail


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    _ensure_runtime_folders(app)
    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _configure_logging(app)

    return app


def _ensure_runtime_folders(app):
    """Create instance/uploads/exports/models/logs folders if they don't exist yet."""
    for path in [
        app.instance_path,
        app.config["UPLOAD_FOLDER"],
        os.path.join(app.config["UPLOAD_FOLDER"], "statements"),
        os.path.join(app.config["UPLOAD_FOLDER"], "profile_pictures"),
        os.path.join(app.config["UPLOAD_FOLDER"], "temp"),
        app.config["EXPORT_FOLDER"],
        os.path.join(app.config["EXPORT_FOLDER"], "pdf"),
        os.path.join(app.config["EXPORT_FOLDER"], "excel"),
        os.path.join(app.config["EXPORT_FOLDER"], "csv"),
        app.config["MODEL_FOLDER"],
    ]:
        os.makedirs(path, exist_ok=True)


def _init_extensions(app):
    """Bind every extension created in extensions.py to this app instance."""
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)


def _register_blueprints(app):
    pass
    # """Register every Flask Blueprint with its URL prefix."""
    # from auth.routes import auth_bp

    # app.register_blueprint(auth_bp, url_prefix="/auth")

    # NOTE: dashboard, profile, transactions, budgets, goals, categories, reports,
    # currency, notifications, and api blueprints follow the same pattern
    # and are added here as each module is built, e.g.:
    #   from profile.routes import profile_bp
    #   app.register_blueprint(profile_bp, url_prefix="/profile")


def _register_error_handlers(app):
    """Friendly error pages instead of raw stack traces / default Werkzeug pages."""
    from flask import render_template

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error")
        return render_template("errors/500.html"), 500


def _configure_logging(app):
    """Rotating file logger, active outside debug/testing so logs/app.log fills up sensibly."""
    if app.debug or app.testing:
        return

    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)

    handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"), maxBytes=1_000_000, backupCount=5
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


# Module-level app object so `flask --app app run` and WSGI servers
# (gunicorn app:app) can find it without extra arguments.
app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
