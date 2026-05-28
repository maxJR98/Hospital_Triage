"""
Extensiones de Flask
Hospital del Norte

Instancias globales de las extensiones que se inicializan
en el app factory para evitar imports circulares.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_socketio import SocketIO

# ORM para la base de datos MySQL
db = SQLAlchemy()

# Gestión de sesiones y autenticación
login_manager = LoginManager()

# Protección CSRF para formularios
csrf = CSRFProtect()

# Envío de correos electrónicos (recuperación de contraseña)
mail = Mail()

# WebSocket para actualizaciones en tiempo real (cola de atención)
socketio = SocketIO()
