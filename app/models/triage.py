"""
Modelo: Triage y TriageSintoma
Evaluación clínica de triage con signos vitales (RF3)
Los síntomas se vinculan al triage, no a la ficha (RF3.1)
"""
from datetime import datetime
from app.extensions import db


class Triage(db.Model):
    """Evaluación de triage con signos vitales y sugerencia del módulo inteligente."""

    __tablename__ = 'triajes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ficha_id = db.Column(db.Integer, db.ForeignKey('fichas.id', ondelete='CASCADE'), nullable=False)
    usuario_medico_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Signos vitales (RF3.1)
    presion_sistolica = db.Column(db.SmallInteger)       # mmHg
    presion_diastolica = db.Column(db.SmallInteger)      # mmHg
    frecuencia_cardiaca = db.Column(db.SmallInteger)     # lpm
    frecuencia_respiratoria = db.Column(db.SmallInteger) # rpm
    temperatura = db.Column(db.Numeric(3, 1))            # °C
    saturacion_oxigeno = db.Column(db.SmallInteger)      # %
    nivel_dolor = db.Column(db.SmallInteger)              # 0-10
    observaciones = db.Column(db.Text)

    # Clasificación (RF3.2, RF3.3)
    nivel_sugerido = db.Column(db.Enum('P1', 'P2', 'P3', 'P4', 'P5'), nullable=False)
    nivel_confirmado = db.Column(db.Enum('P1', 'P2', 'P3', 'P4', 'P5'), nullable=False)
    justificacion_modificacion = db.Column(db.Text)

    fecha_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relaciones
    medico = db.relationship('Usuario', backref='triajes_realizados')
    sintomas = db.relationship('TriageSintoma', backref='triage', lazy='joined',
                                cascade='all, delete-orphan')

    @property
    def fue_modificado(self):
        """Indica si el médico cambió el nivel sugerido."""
        return self.nivel_sugerido != self.nivel_confirmado

    def __repr__(self):
        return f'<Triage ficha={self.ficha_id} sugerido={self.nivel_sugerido} confirmado={self.nivel_confirmado}>'


class TriageSintoma(db.Model):
    """Relación N:M entre triajes y síntomas (RF3.1)."""

    __tablename__ = 'triage_sintomas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    triage_id = db.Column(db.Integer, db.ForeignKey('triajes.id', ondelete='CASCADE'), nullable=False)
    sintoma_id = db.Column(db.Integer, db.ForeignKey('sintomas.id'), nullable=False)

    # Relación al catálogo de síntomas
    sintoma = db.relationship('Sintoma')

    __table_args__ = (
        db.UniqueConstraint('triage_id', 'sintoma_id', name='uk_triage_sintoma'),
    )

    def __repr__(self):
        return f'<TriageSintoma triage={self.triage_id} sintoma={self.sintoma_id}>'
