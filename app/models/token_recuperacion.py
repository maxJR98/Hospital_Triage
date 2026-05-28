"""
Modelo: TokenRecuperacion
Tokens para restablecimiento de contraseña (RF1.5)
Vigencia configurable (por defecto 30 minutos)
"""
import secrets
from datetime import datetime, timedelta
from app.extensions import db


class TokenRecuperacion(db.Model):
    """Token de recuperación de contraseña con expiración."""

    __tablename__ = 'tokens_recuperacion'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, nullable=False, default=False)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def generar(usuario_id, minutos_vigencia=30):
        """Genera un nuevo token de recuperación para un usuario."""
        token = TokenRecuperacion(
            usuario_id=usuario_id,
            token=secrets.token_urlsafe(48),
            fecha_expiracion=datetime.utcnow() + timedelta(minutes=minutos_vigencia)
        )
        db.session.add(token)
        db.session.commit()
        return token

    @property
    def es_valido(self):
        """Verifica si el token no ha expirado y no fue usado."""
        return not self.usado and datetime.utcnow() < self.fecha_expiracion

    def marcar_usado(self):
        """Marca el token como utilizado."""
        self.usado = True
        db.session.commit()

    def __repr__(self):
        return f'<TokenRecuperacion usuario_id={self.usuario_id} valido={self.es_valido}>'
