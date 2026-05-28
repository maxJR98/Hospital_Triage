"""
Modelo: Usuario
Personal hospitalario con acceso al sistema (RF1)
Incluye lógica de bloqueo por intentos fallidos (RF1.2)
"""
from datetime import datetime
from flask_login import UserMixin
import bcrypt
from app.extensions import db


class Usuario(UserMixin, db.Model):
    """Usuario del sistema hospitalario."""

    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_completo = db.Column(db.String(150), nullable=False)
    ci = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    estado = db.Column(db.Enum('activo', 'inactivo'), nullable=False, default='activo')
    intentos_fallidos = db.Column(db.Integer, nullable=False, default=0)
    fecha_bloqueo = db.Column(db.DateTime, default=None)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relaciones
    tokens_recuperacion = db.relationship('TokenRecuperacion', backref='usuario', lazy='dynamic')

    def set_password(self, password):
        """Genera hash bcrypt de la contraseña (RNF2.2)."""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        """Verifica la contraseña contra el hash almacenado."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    @property
    def is_active(self):
        """Flask-Login: el usuario solo está activo si su estado es 'activo'."""
        return self.estado == 'activo'

    @property
    def esta_bloqueado(self):
        """Verifica si la cuenta está temporalmente bloqueada (RF1.2)."""
        if self.fecha_bloqueo is None:
            return False
        from app.models.configuracion import Configuracion
        minutos_bloqueo = Configuracion.get_int('bloqueo_minutos', 15)
        diferencia = (datetime.utcnow() - self.fecha_bloqueo).total_seconds() / 60
        if diferencia >= minutos_bloqueo:
            # El bloqueo expiró, resetear
            self.intentos_fallidos = 0
            self.fecha_bloqueo = None
            db.session.commit()
            return False
        return True

    def registrar_intento_fallido(self):
        """Registra un intento fallido de login y bloquea si es necesario (RF1.2)."""
        from app.models.configuracion import Configuracion
        self.intentos_fallidos += 1
        max_intentos = Configuracion.get_int('intentos_max_login', 5)
        if self.intentos_fallidos >= max_intentos:
            self.fecha_bloqueo = datetime.utcnow()
        db.session.commit()

    def resetear_intentos(self):
        """Resetea el contador de intentos tras un login exitoso."""
        self.intentos_fallidos = 0
        self.fecha_bloqueo = None
        db.session.commit()

    @property
    def nombre_rol(self):
        """Retorna el nombre del rol del usuario."""
        return self.rol.nombre if self.rol else 'Sin rol'

    def tiene_rol(self, *roles):
        """Verifica si el usuario tiene alguno de los roles indicados."""
        return self.rol.nombre in roles

    def __repr__(self):
        return f'<Usuario {self.email} ({self.nombre_rol})>'
