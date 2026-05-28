"""
App Factory del Sistema Inteligente de Triage
Hospital del Norte

Patrón Factory para crear la aplicación Flask con todas sus
extensiones, blueprints y configuraciones.
"""
from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, csrf, mail, socketio


def create_app(config_class=Config):
    """Crea y configura la instancia de la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    _init_extensions(app)

    # Registrar blueprints
    _register_blueprints(app)

    # Registrar manejadores de errores
    _register_error_handlers(app)

    # Configurar Flask-Login
    _configure_login_manager(app)

    return app


def _init_extensions(app):
    """Inicializa todas las extensiones de Flask."""
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*')


def _register_blueprints(app):
    """Registra todos los blueprints (módulos de rutas)."""
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.recepcion import recepcion_bp
    from app.routes.triage import triage_bp
    from app.routes.atencion import atencion_bp
    from app.routes.reportes import reportes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(recepcion_bp, url_prefix='/recepcion')
    app.register_blueprint(triage_bp, url_prefix='/triage')
    app.register_blueprint(atencion_bp, url_prefix='/atencion')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')


def _register_error_handlers(app):
    """Registra manejadores de errores personalizados."""
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500


def _configure_login_manager(app):
    """Configura Flask-Login para la autenticación."""
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debe iniciar sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    login_manager.session_protection = 'strong'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.usuario import Usuario
        return Usuario.query.get(int(user_id))
