"""
Modelo: Paciente
Datos personales de los pacientes (RF2.1)
"""
from app.extensions import db


class Paciente(db.Model):
    """Paciente registrado en el sistema."""

    __tablename__ = 'pacientes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ci = db.Column(db.String(20), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=False, index=True)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    sexo = db.Column(db.Enum('Masculino', 'Femenino', 'Otro'), nullable=False)
    contacto = db.Column(db.String(15), nullable=False)

    # Relaciones
    fichas = db.relationship('Ficha', backref='paciente', lazy='dynamic')

    @property
    def edad(self):
        """Calcula la edad actual del paciente."""
        from datetime import date
        hoy = date.today()
        return hoy.year - self.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )

    def __repr__(self):
        return f'<Paciente {self.nombre_completo} CI={self.ci}>'
