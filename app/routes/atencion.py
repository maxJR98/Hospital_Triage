"""
Rutas de Atención Médica
Hospital del Norte

Cola de atención dinámica, llamado de pacientes y diagnóstico (RF4, RF2.4)
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.ficha import Ficha
from app.models.paciente import Paciente
from app.models.historial_estado import HistorialEstadoFicha
from app.models.configuracion import Configuracion
from app.models.bitacora import BitacoraAuditoria
from app.utils.decorators import roles_requeridos

atencion_bp = Blueprint('atencion', __name__)


@atencion_bp.route('/cola')
@login_required
@roles_requeridos('Médico Tratante', 'Médico de Triage', 'Recepcionista', 'Administrador')
def cola():
    """Cola de atención en tiempo real (RF4.1)."""
    return render_template('atencion/cola.html')


@atencion_bp.route('/cola/datos')
@login_required
def cola_datos():
    """API JSON de la cola de atención para actualización en tiempo real."""
    fichas_espera = Ficha.query.join(Paciente).filter(
        Ficha.estado.in_(['En espera', 'En triage']),
        Ficha.prioridad_final.isnot(None)
    ).order_by(
        db.case(
            (Ficha.prioridad_final == 'P1', 1),
            (Ficha.prioridad_final == 'P2', 2),
            (Ficha.prioridad_final == 'P3', 3),
            (Ficha.prioridad_final == 'P4', 4),
            (Ficha.prioridad_final == 'P5', 5),
        ),
        Ficha.fecha_hora_llegada.asc()
    ).all()

    fichas_atencion = Ficha.query.join(Paciente).filter(
        Ficha.estado == 'En atención'
    ).order_by(Ficha.fecha_hora_llegada.desc()).all()

    # Obtener umbrales de alerta
    umbrales = {
        'P1': Configuracion.get_int('alerta_p1_minutos', 0),
        'P2': Configuracion.get_int('alerta_p2_minutos', 15),
        'P3': Configuracion.get_int('alerta_p3_minutos', 30),
        'P4': Configuracion.get_int('alerta_p4_minutos', 60),
        'P5': Configuracion.get_int('alerta_p5_minutos', 120),
    }

    def ficha_to_dict(f):
        minutos = f.minutos_espera
        umbral = umbrales.get(f.prioridad_final, 999)
        return {
            'id': f.id,
            'numero_ficha': f.numero_ficha,
            'paciente_nombre': f.paciente.nombre_completo,
            'paciente_ci': f.paciente.ci,
            'prioridad': f.prioridad_final,
            'color': f.color_prioridad,
            'estado': f.estado,
            'motivo': f.motivo_consulta,
            'minutos_espera': minutos,
            'alerta': minutos >= umbral if umbral > 0 else False,
        }

    return jsonify({
        'en_espera': [ficha_to_dict(f) for f in fichas_espera],
        'en_atencion': [ficha_to_dict(f) for f in fichas_atencion],
        'total_espera': len(fichas_espera),
        'total_atencion': len(fichas_atencion),
    })


@atencion_bp.route('/llamar/<int:ficha_id>', methods=['POST'])
@login_required
@roles_requeridos('Médico Tratante', 'Administrador')
def llamar_paciente(ficha_id):
    """Llamar al siguiente paciente de la cola (RF4.2)."""
    ficha = Ficha.query.get_or_404(ficha_id)

    if ficha.estado != 'En espera':
        flash('Este paciente no está en estado de espera.', 'warning')
        return redirect(url_for('atencion.cola'))

    HistorialEstadoFicha.registrar_cambio(ficha, 'En atención', current_user.id)
    ficha.medico_tratante_id = current_user.id
    db.session.commit()

    BitacoraAuditoria.registrar(
        accion='LLAMAR_PACIENTE',
        tabla_afectada='fichas',
        registro_id=ficha.id,
        detalle=f'Paciente {ficha.paciente.nombre_completo} llamado a atención (Ficha {ficha.numero_ficha})'
    )

    flash(f'Paciente {ficha.paciente.nombre_completo} llamado a consulta.', 'success')
    return redirect(url_for('atencion.diagnostico', ficha_id=ficha.id))


@atencion_bp.route('/diagnostico/<int:ficha_id>', methods=['GET', 'POST'])
@login_required
@roles_requeridos('Médico Tratante', 'Administrador')
def diagnostico(ficha_id):
    """Registro de diagnóstico y cierre de ficha (RF2.4)."""
    ficha = Ficha.query.get_or_404(ficha_id)

    if ficha.estado != 'En atención':
        flash('Esta ficha no está en atención actualmente.', 'warning')
        return redirect(url_for('atencion.cola'))

    if request.method == 'POST':
        diagnostico_texto = request.form.get('diagnostico', '').strip()

        if not diagnostico_texto:
            flash('El diagnóstico de egreso es obligatorio.', 'danger')
            return render_template('atencion/diagnostico.html', ficha=ficha)

        # Cerrar ficha (RF2.4)
        ficha.cerrar(diagnostico_texto, current_user.id)
        HistorialEstadoFicha.registrar_cambio(ficha, 'Finalizado', current_user.id)
        db.session.commit()

        BitacoraAuditoria.registrar(
            accion='CERRAR_FICHA',
            tabla_afectada='fichas',
            registro_id=ficha.id,
            detalle=(
                f'Ficha {ficha.numero_ficha} cerrada. '
                f'Diagnóstico: {diagnostico_texto[:100]}. '
                f'Tiempo total: {ficha.tiempo_total_segundos // 60} min'
            )
        )

        flash(
            f'Ficha {ficha.numero_ficha} finalizada exitosamente. '
            f'Tiempo total de atención: {ficha.tiempo_total_segundos // 60} minutos.',
            'success'
        )
        return redirect(url_for('atencion.cola'))

    return render_template('atencion/diagnostico.html', ficha=ficha)
