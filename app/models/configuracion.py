"""
Modelo: Configuracion
Parámetros del sistema configurables (umbrales de alerta, tiempos, etc.)
"""
from datetime import datetime
from app.extensions import db


class Configuracion(db.Model):
    """Parámetro configurable del sistema."""

    __tablename__ = 'configuraciones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.String(255))
    fecha_modificacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                                    onupdate=datetime.utcnow)

    @staticmethod
    def get(clave, default=None):
        """Obtiene el valor de una configuración por su clave."""
        config = Configuracion.query.filter_by(clave=clave).first()
        return config.valor if config else default

    @staticmethod
    def get_int(clave, default=0):
        """Obtiene el valor entero de una configuración."""
        valor = Configuracion.get(clave)
        try:
            return int(valor) if valor is not None else default
        except (ValueError, TypeError):
            return default

    @staticmethod
    def set(clave, valor, descripcion=None):
        """Establece el valor de una configuración."""
        config = Configuracion.query.filter_by(clave=clave).first()
        if config:
            config.valor = str(valor)
            if descripcion:
                config.descripcion = descripcion
        else:
            config = Configuracion(clave=clave, valor=str(valor), descripcion=descripcion)
            db.session.add(config)
        db.session.commit()
        return config

    def __repr__(self):
        return f'<Configuracion {self.clave}={self.valor}>'
