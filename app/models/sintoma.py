"""
Modelo: Sintoma
Catálogo configurable de síntomas (RF3.1)
"""
from app.extensions import db


class Sintoma(db.Model):
    """Síntoma configurable del catálogo clínico."""

    __tablename__ = 'sintomas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    @staticmethod
    def obtener_activos():
        """Retorna todos los síntomas activos para selección múltiple."""
        return Sintoma.query.filter_by(activo=True).order_by(Sintoma.nombre).all()

    def __repr__(self):
        return f'<Sintoma {self.nombre}>'
