from flask import Flask


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('app.config.Config')

    # Register available blueprints from app.routes
    try:
        from .routes.dashboard import bp as dashboard_bp
        app.register_blueprint(dashboard_bp)
    except Exception:
        pass
    try:
        from .routes.admin import bp as admin_bp
        app.register_blueprint(admin_bp)
    except Exception:
        pass
    try:
        from .routes.chat import bp as chat_bp
        app.register_blueprint(chat_bp)
    except Exception:
        pass
    try:
        from routes.ro import ro as ro_bp
        app.register_blueprint(ro_bp)
    except Exception:
        pass

    return app
