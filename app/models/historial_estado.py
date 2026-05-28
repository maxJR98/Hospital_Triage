"""
Modelo: HistorialEstadoFicha
Historial de cambios de estado de cada ficha (RF2.3)
"""
from datetime import datetime
from app.extensions import db


class HistorialEstadoFicha(db.Model):
    """Registro de cada cambio de estado de una ficha."""

    __tablename__ = 'historial_estados_ficha'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ficha_id = db.Column(db.Integer, db.ForeignKey('fichas.id', ondelete='CASCADE'), nullable=False)
    estado_anterior = db.Column(
        db.Enum('En espera', 'En triage', 'En atención', 'Finalizado', 'Abandonó'),
        nullable=False
    )
    estado_nuevo = db.Column(
        db.Enum('En espera', 'En triage', 'En atención', 'Finalizado', 'Abandonó'),
        nullable=False
    )
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relaciones
    usuario = db.relationship('Usuario', backref='cambios_estado_realizados')

    @staticmethod
    def registrar_cambio(ficha, estado_nuevo, usuario_id):
        """Registra un cambio de estado y actualiza la ficha.

        Args:
            ficha: Instancia de Ficha a actualizar.
            estado_nuevo: Nuevo estado a asignar.
            usuario_id: ID del usuario que realiza el cambio.

        Returns:
            Instancia del historial creado.
        """
        historial = HistorialEstadoFicha(
            ficha_id=ficha.id,
            estado_anterior=ficha.estado,
            estado_nuevo=estado_nuevo,
            usuario_id=usuario_id
        )
        ficha.estado = estado_nuevo
        db.session.add(historial)
        db.session.commit()
        return historial

    def __repr__(self):
        return f'<Historial ficha={self.ficha_id} {self.estado_anterior}→{self.estado_nuevo}>'
