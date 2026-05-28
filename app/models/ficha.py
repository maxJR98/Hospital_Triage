"""
Modelo: Ficha
Ficha de atención por visita del paciente (RF2)
Incluye relaciones a recepcionista, médico de triage y médico tratante
"""
from datetime import datetime
from app.extensions import db


class Ficha(db.Model):
    """Ficha digital de atención del paciente."""

    __tablename__ = 'fichas'

    ESTADOS = ['En espera', 'En triage', 'En atención', 'Finalizado', 'Abandonó']
    PRIORIDADES = ['P1', 'P2', 'P3', 'P4', 'P5']

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numero_ficha = db.Column(db.String(20), unique=True, nullable=False)
    fecha_hora_llegada = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    recepcionista_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    motivo_consulta = db.Column(db.Text, nullable=False)
    estado = db.Column(
        db.Enum('En espera', 'En triage', 'En atención', 'Finalizado', 'Abandonó'),
        nullable=False, default='En espera'
    )
    prioridad_final = db.Column(db.Enum('P1', 'P2', 'P3', 'P4', 'P5'))
    medico_triage_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    medico_tratante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    diagnostico_egreso = db.Column(db.Text)
    hora_fin_atencion = db.Column(db.DateTime)
    tiempo_total_segundos = db.Column(db.Integer)

    # Relaciones
    recepcionista = db.relationship('Usuario', foreign_keys=[recepcionista_id], backref='fichas_creadas')
    medico_triage = db.relationship('Usuario', foreign_keys=[medico_triage_id], backref='fichas_triadas')
    medico_tratante = db.relationship('Usuario', foreign_keys=[medico_tratante_id], backref='fichas_atendidas')
    triajes = db.relationship('Triage', backref='ficha', lazy='dynamic')
    historial_estados = db.relationship('HistorialEstadoFicha', backref='ficha', lazy='dynamic',
                                        order_by='HistorialEstadoFicha.fecha_hora.desc()')

    @staticmethod
    def generar_numero_ficha():
        """Genera el número de ficha con formato YYYY-MM-DD-NNN (único por día)."""
        hoy = datetime.utcnow().strftime('%Y-%m-%d')
        # Contar fichas de hoy para obtener el siguiente secuencial
        cantidad_hoy = Ficha.query.filter(
            db.func.date(Ficha.fecha_hora_llegada) == datetime.utcnow().date()
        ).count()
        secuencial = cantidad_hoy + 1
        return f"{hoy}-{secuencial:03d}"

    @property
    def minutos_espera(self):
        """Calcula los minutos de espera desde la llegada."""
        if self.estado in ('Finalizado', 'Abandonó'):
            if self.tiempo_total_segundos:
                return self.tiempo_total_segundos // 60
            return 0
        diferencia = datetime.utcnow() - self.fecha_hora_llegada
        return int(diferencia.total_seconds() / 60)

    @property
    def color_prioridad(self):
        """Retorna el color CSS asociado al nivel de prioridad."""
        colores = {
            'P1': '#DC2626',   # Rojo - Resucitación
            'P2': '#F97316',   # Naranja - Emergencia
            'P3': '#EAB308',   # Amarillo - Urgente
            'P4': '#22C55E',   # Verde - Semi-urgente
            'P5': '#3B82F6',   # Azul - No urgente
        }
        return colores.get(self.prioridad_final, '#6B7280')

    def cerrar(self, diagnostico, medico_tratante_id):
        """Cierra la ficha al finalizar la atención (RF2.4)."""
        self.diagnostico_egreso = diagnostico
        self.medico_tratante_id = medico_tratante_id
        self.hora_fin_atencion = datetime.utcnow()
        self.tiempo_total_segundos = int(
            (self.hora_fin_atencion - self.fecha_hora_llegada).total_seconds()
        )
        self.estado = 'Finalizado'

    def __repr__(self):
        return f'<Ficha {self.numero_ficha} estado={self.estado}>'
