"""
Modelo: Rol
Catálogo de roles del sistema (RBAC)
Roles: Administrador, Médico de Triage, Recepcionista, Médico Tratante, Director
"""
from app.extensions import db


class Rol(db.Model):
    """Rol del sistema para control de acceso basado en roles (RNF2.3)."""

    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))

    # Relaciones
    usuarios = db.relationship('Usuario', backref='rol', lazy='dynamic')

    def __repr__(self):
        return f'<Rol {self.nombre}>'
