"""
Modelo: ReglaClinica
Reglas parametrizables del módulo inteligente de triage (RF3.4)
"""
from app.extensions import db


class ReglaClinica(db.Model):
    """Regla clínica para la sugerencia automática de prioridad."""

    __tablename__ = 'reglas_clinicas'

    PARAMETROS = [
        'frecuencia_cardiaca', 'frecuencia_respiratoria', 'temperatura',
        'saturacion_oxigeno', 'presion_sistolica', 'presion_diastolica', 'nivel_dolor'
    ]
    OPERADORES = ['>', '<', '>=', '<=', '=', 'BETWEEN']
    PRIORIDADES = ['P1', 'P2', 'P3', 'P4', 'P5']

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parametro = db.Column(
        db.Enum(*PARAMETROS),
        nullable=False
    )
    operador = db.Column(
        db.Enum(*OPERADORES),
        nullable=False
    )
    valor_umbral = db.Column(db.String(50), nullable=False)
    nivel_prioridad = db.Column(db.Enum(*PRIORIDADES), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    descripcion = db.Column(db.String(255))

    @staticmethod
    def obtener_activas():
        """Retorna todas las reglas clínicas activas."""
        return ReglaClinica.query.filter_by(activo=True).all()

    def evaluar(self, valor):
        """Evalúa si un valor de signo vital cumple con esta regla.

        Args:
            valor: Valor numérico del signo vital a evaluar.

        Returns:
            True si el valor cumple la condición de la regla.
        """
        if valor is None:
            return False

        valor = float(valor)

        if self.operador == '>':
            return valor > float(self.valor_umbral)
        elif self.operador == '<':
            return valor < float(self.valor_umbral)
        elif self.operador == '>=':
            return valor >= float(self.valor_umbral)
        elif self.operador == '<=':
            return valor <= float(self.valor_umbral)
        elif self.operador == '=':
            return valor == float(self.valor_umbral)
        elif self.operador == 'BETWEEN':
            partes = self.valor_umbral.split(',')
            if len(partes) == 2:
                return float(partes[0]) <= valor <= float(partes[1])
        return False

    def __repr__(self):
        return f'<ReglaClinica {self.parametro} {self.operador} {self.valor_umbral} → {self.nivel_prioridad}>'
