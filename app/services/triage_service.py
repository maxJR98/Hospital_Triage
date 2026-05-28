"""
Servicio de Triage Inteligente
Hospital del Norte

Lógica del módulo inteligente que evalúa signos vitales
contra reglas clínicas y sugiere nivel de prioridad (RF3.2).
"""
from app.models.regla_clinica import ReglaClinica


class TriageService:
    """Servicio de evaluación inteligente de triage."""

    # Mapeo de parámetros a nombres legibles
    NOMBRES_PARAMETROS = {
        'frecuencia_cardiaca': 'Frecuencia Cardíaca',
        'frecuencia_respiratoria': 'Frecuencia Respiratoria',
        'temperatura': 'Temperatura',
        'saturacion_oxigeno': 'Saturación de Oxígeno',
        'presion_sistolica': 'Presión Sistólica',
        'presion_diastolica': 'Presión Diastólica',
        'nivel_dolor': 'Nivel de Dolor',
    }

    # Orden de prioridad (menor índice = mayor prioridad)
    ORDEN_PRIORIDAD = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'P5': 5}

    @staticmethod
    def evaluar_signos_vitales(datos_clinicos):
        """Evalúa los signos vitales contra las reglas clínicas activas.

        Args:
            datos_clinicos: dict con los signos vitales del paciente.
                Ejemplo: {
                    'frecuencia_cardiaca': 140,
                    'temperatura': 39.8,
                    'saturacion_oxigeno': 88,
                    ...
                }

        Returns:
            dict con:
                - nivel_sugerido: str ('P1' a 'P5')
                - criterios_activados: list de dict con reglas que se activaron
                - todas las reglas evaluadas
        """
        reglas = ReglaClinica.obtener_activas()
        criterios_activados = []
        nivel_mas_alto = 'P5'  # Por defecto, no urgente

        for regla in reglas:
            valor = datos_clinicos.get(regla.parametro)
            if valor is not None and regla.evaluar(valor):
                criterios_activados.append({
                    'regla_id': regla.id,
                    'parametro': regla.parametro,
                    'parametro_nombre': TriageService.NOMBRES_PARAMETROS.get(
                        regla.parametro, regla.parametro
                    ),
                    'operador': regla.operador,
                    'valor_umbral': regla.valor_umbral,
                    'valor_paciente': valor,
                    'nivel_prioridad': regla.nivel_prioridad,
                    'descripcion': regla.descripcion,
                })

                # Mantener el nivel más alto (más urgente)
                if (TriageService.ORDEN_PRIORIDAD.get(regla.nivel_prioridad, 5) <
                        TriageService.ORDEN_PRIORIDAD.get(nivel_mas_alto, 5)):
                    nivel_mas_alto = regla.nivel_prioridad

        return {
            'nivel_sugerido': nivel_mas_alto,
            'criterios_activados': criterios_activados,
            'total_criterios': len(criterios_activados),
        }

    @staticmethod
    def obtener_nombre_prioridad(nivel):
        """Retorna el nombre descriptivo del nivel de prioridad."""
        nombres = {
            'P1': 'Resucitación',
            'P2': 'Emergencia',
            'P3': 'Urgente',
            'P4': 'Semi-urgente',
            'P5': 'No urgente',
        }
        return nombres.get(nivel, 'Desconocido')

    @staticmethod
    def obtener_color_prioridad(nivel):
        """Retorna el color CSS asociado al nivel de prioridad."""
        colores = {
            'P1': '#DC2626',
            'P2': '#F97316',
            'P3': '#EAB308',
            'P4': '#22C55E',
            'P5': '#3B82F6',
        }
        return colores.get(nivel, '#6B7280')
