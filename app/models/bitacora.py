"""
Modelo: BitacoraAuditoria
Registro inmutable de acciones críticas del sistema (RNF2.4)
La inmutabilidad se garantiza con triggers en la BD.
"""
from datetime import datetime
from flask import request
from flask_login import current_user
from app.extensions import db


class BitacoraAuditoria(db.Model):
    """Registro inmutable de auditoría del sistema."""

    __tablename__ = 'bitacora_auditoria'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    accion = db.Column(db.String(100), nullable=False)
    tabla_afectada = db.Column(db.String(50))
    registro_id = db.Column(db.Integer)
    detalle = db.Column(db.Text)
    ip_origen = db.Column(db.String(45))
    fecha_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relaciones
    usuario = db.relationship('Usuario', backref='acciones_bitacora')

    @staticmethod
    def registrar(accion, tabla_afectada=None, registro_id=None, detalle=None, usuario_id=None):
        """Registra una acción en la bitácora de auditoría.

        Args:
            accion: Descripción de la acción realizada.
            tabla_afectada: Nombre de la tabla afectada.
            registro_id: ID del registro afectado.
            detalle: Detalle adicional de la acción.
            usuario_id: ID del usuario (si no se proporciona, usa current_user).
        """
        if usuario_id is None:
            try:
                usuario_id = current_user.id if current_user.is_authenticated else None
            except RuntimeError:
                usuario_id = None

        try:
            ip = request.remote_addr
        except RuntimeError:
            ip = None

        entrada = BitacoraAuditoria(
            usuario_id=usuario_id,
            accion=accion,
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            detalle=detalle,
            ip_origen=ip
        )
        db.session.add(entrada)
        db.session.commit()
        return entrada

    def __repr__(self):
        return f'<Bitacora {self.accion} por usuario_id={self.usuario_id} en {self.fecha_hora}>'
