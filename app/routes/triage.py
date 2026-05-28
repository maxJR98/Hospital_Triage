"""
Rutas de Triage
Hospital del Norte

Evaluación clínica y asignación de prioridad (RF3)
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.ficha import Ficha
from app.models.triage import Triage, TriageSintoma
from app.models.sintoma import Sintoma
from app.models.historial_estado import HistorialEstadoFicha
from app.models.bitacora import BitacoraAuditoria
from app.services.triage_service import TriageService
from app.utils.decorators import roles_requeridos

triage_bp = Blueprint('triage', __name__)


@triage_bp.route('/pendientes')
@login_required
@roles_requeridos('Médico de Triage', 'Administrador')
def pendientes():
    """Lista de fichas pendientes de triage."""
    fichas = Ficha.query.filter(
        Ficha.estado.in_(['En espera', 'En triage'])
    ).order_by(Ficha.fecha_hora_llegada.asc()).all()
    return render_template('triage/pendientes.html', fichas=fichas)


@triage_bp.route('/evaluar/<int:ficha_id>', methods=['GET', 'POST'])
@login_required
@roles_requeridos('Médico de Triage', 'Administrador')
def evaluar(ficha_id):
    """Formulario de evaluación de triage (RF3.1, RF3.2, RF3.3)."""
    ficha = Ficha.query.get_or_404(ficha_id)
    sintomas = Sintoma.obtener_activos()

    if ficha.estado not in ('En espera', 'En triage'):
        flash('Esta ficha ya no puede ser evaluada.', 'warning')
        return redirect(url_for('triage.pendientes'))

    if request.method == 'POST':
        # Capturar signos vitales (RF3.1)
        datos_clinicos = {
            'presion_sistolica': request.form.get('presion_sistolica', type=float),
            'presion_diastolica': request.form.get('presion_diastolica', type=float),
            'frecuencia_cardiaca': request.form.get('frecuencia_cardiaca', type=float),
            'frecuencia_respiratoria': request.form.get('frecuencia_respiratoria', type=float),
            'temperatura': request.form.get('temperatura', type=float),
            'saturacion_oxigeno': request.form.get('saturacion_oxigeno', type=float),
            'nivel_dolor': request.form.get('nivel_dolor', type=int),
        }

        nivel_confirmado = request.form.get('nivel_confirmado')
        nivel_sugerido = request.form.get('nivel_sugerido', 'P5')
        justificacion = request.form.get('justificacion', '').strip()
        observaciones = request.form.get('observaciones', '').strip()
        sintomas_ids = request.form.getlist('sintomas', type=int)

        # Validar confirmación médica obligatoria (RF3.3)
        if not nivel_confirmado:
            flash('Debe confirmar el nivel de prioridad.', 'danger')
            return render_template('triage/evaluacion.html', ficha=ficha, sintomas=sintomas)

        # Validar justificación si se modifica el nivel sugerido (RF3.3)
        if nivel_confirmado != nivel_sugerido:
            if len(justificacion) < 20:
                flash(
                    'Al modificar el nivel sugerido, debe proporcionar una justificación '
                    'clínica de al menos 20 caracteres.',
                    'danger'
                )
                return render_template('triage/evaluacion.html', ficha=ficha, sintomas=sintomas)

        # Crear registro de triage
        triage = Triage(
            ficha_id=ficha.id,
            usuario_medico_id=current_user.id,
            presion_sistolica=datos_clinicos.get('presion_sistolica'),
            presion_diastolica=datos_clinicos.get('presion_diastolica'),
            frecuencia_cardiaca=datos_clinicos.get('frecuencia_cardiaca'),
            frecuencia_respiratoria=datos_clinicos.get('frecuencia_respiratoria'),
            temperatura=datos_clinicos.get('temperatura'),
            saturacion_oxigeno=datos_clinicos.get('saturacion_oxigeno'),
            nivel_dolor=datos_clinicos.get('nivel_dolor'),
            observaciones=observaciones or None,
            nivel_sugerido=nivel_sugerido,
            nivel_confirmado=nivel_confirmado,
            justificacion_modificacion=justificacion if nivel_confirmado != nivel_sugerido else None
        )
        db.session.add(triage)
        db.session.flush()

        # Asociar síntomas al triage (RF3.1)
        for sintoma_id in sintomas_ids:
            ts = TriageSintoma(triage_id=triage.id, sintoma_id=sintoma_id)
            db.session.add(ts)

        # Actualizar ficha con prioridad y médico de triage
        ficha.prioridad_final = nivel_confirmado
        ficha.medico_triage_id = current_user.id

        # Cambiar estado a "En espera" (ya clasificado, esperando atención)
        if ficha.estado == 'En triage':
            HistorialEstadoFicha.registrar_cambio(ficha, 'En espera', current_user.id)
        else:
            # Si venía directo de "En espera", mantener el estado
            pass

        db.session.commit()

        # Registrar en bitácora
        BitacoraAuditoria.registrar(
            accion='REALIZAR_TRIAGE',
            tabla_afectada='triajes',
            registro_id=triage.id,
            detalle=(
                f'Triage de ficha {ficha.numero_ficha}: '
                f'Sugerido={nivel_sugerido}, Confirmado={nivel_confirmado}'
                f'{", Justificación: " + justificacion if triage.fue_modificado else ""}'
            )
        )

        nombre_prioridad = TriageService.obtener_nombre_prioridad(nivel_confirmado)
        flash(
            f'Triage completado. Ficha {ficha.numero_ficha} clasificada como '
            f'{nivel_confirmado} ({nombre_prioridad}).',
            'success'
        )
        return redirect(url_for('triage.pendientes'))

    return render_template('triage/evaluacion.html', ficha=ficha, sintomas=sintomas)


@triage_bp.route('/evaluar/<int:ficha_id>/sugerencia', methods=['POST'])
@login_required
@roles_requeridos('Médico de Triage', 'Administrador')
def obtener_sugerencia(ficha_id):
    """API para obtener la sugerencia del módulo inteligente (RF3.2).

    Llamado por AJAX desde el formulario de triage.
    """
    datos = request.get_json()

    datos_clinicos = {
        'presion_sistolica': datos.get('presion_sistolica'),
        'presion_diastolica': datos.get('presion_diastolica'),
        'frecuencia_cardiaca': datos.get('frecuencia_cardiaca'),
        'frecuencia_respiratoria': datos.get('frecuencia_respiratoria'),
        'temperatura': datos.get('temperatura'),
        'saturacion_oxigeno': datos.get('saturacion_oxigeno'),
        'nivel_dolor': datos.get('nivel_dolor'),
    }

    resultado = TriageService.evaluar_signos_vitales(datos_clinicos)
    resultado['nombre_prioridad'] = TriageService.obtener_nombre_prioridad(resultado['nivel_sugerido'])
    resultado['color_prioridad'] = TriageService.obtener_color_prioridad(resultado['nivel_sugerido'])

    return jsonify(resultado)
