"""
Rutas de Reportes y Estadísticas
Hospital del Norte

Dashboard operativo, reportes por fecha, exportación PDF/CSV (RF5)
"""
import csv
import io
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, make_response
from flask_login import login_required
from app.extensions import db
from app.models.ficha import Ficha
from app.models.bitacora import BitacoraAuditoria
from app.utils.decorators import roles_requeridos

reportes_bp = Blueprint('reportes', __name__)


@reportes_bp.route('/dashboard')
@login_required
@roles_requeridos('Director', 'Administrador')
def dashboard():
    """Dashboard operativo con indicadores en tiempo real (RF5.3)."""
    return render_template('reportes/dashboard.html')


@reportes_bp.route('/dashboard/datos')
@login_required
@roles_requeridos('Director', 'Administrador')
def dashboard_datos():
    """API JSON de indicadores para el dashboard (RF5.3)."""
    hoy = datetime.utcnow().date()

    # Total pacientes hoy
    fichas_hoy = Ficha.query.filter(
        db.func.date(Ficha.fecha_hora_llegada) == hoy
    ).all()

    en_espera = sum(1 for f in fichas_hoy if f.estado in ('En espera', 'En triage'))
    en_atencion = sum(1 for f in fichas_hoy if f.estado == 'En atención')
    finalizados = sum(1 for f in fichas_hoy if f.estado == 'Finalizado')
    abandonaron = sum(1 for f in fichas_hoy if f.estado == 'Abandonó')

    # Tiempo promedio de espera (solo finalizados)
    tiempos = [f.tiempo_total_segundos for f in fichas_hoy
               if f.estado == 'Finalizado' and f.tiempo_total_segundos]
    promedio_espera = sum(tiempos) / len(tiempos) / 60 if tiempos else 0

    # Distribución por prioridad
    distribucion = {}
    for nivel in ['P1', 'P2', 'P3', 'P4', 'P5']:
        distribucion[nivel] = sum(1 for f in fichas_hoy if f.prioridad_final == nivel)

    # Alertas activas (pacientes que superan umbral)
    from app.models.configuracion import Configuracion
    alertas_activas = 0
    for f in fichas_hoy:
        if f.estado in ('En espera', 'En triage') and f.prioridad_final:
            umbral = Configuracion.get_int(f'alerta_{f.prioridad_final.lower()}_minutos', 999)
            if umbral > 0 and f.minutos_espera >= umbral:
                alertas_activas += 1

    return jsonify({
        'total_hoy': len(fichas_hoy),
        'en_espera': en_espera,
        'en_atencion': en_atencion,
        'finalizados': finalizados,
        'abandonaron': abandonaron,
        'promedio_espera_min': round(promedio_espera, 1),
        'distribucion': distribucion,
        'alertas_activas': alertas_activas,
    })


@reportes_bp.route('/generar', methods=['GET', 'POST'])
@login_required
@roles_requeridos('Director', 'Administrador')
def generar_reporte():
    """Generación de reportes por rango de fechas (RF5.1, RF5.2)."""
    if request.method == 'POST':
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        formato = request.form.get('formato', 'pantalla')

        if not fecha_inicio or not fecha_fin:
            from flask import flash
            flash('Debe seleccionar un rango de fechas.', 'warning')
            return render_template('reportes/generar.html')

        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

        fichas = Ficha.query.filter(
            db.func.date(Ficha.fecha_hora_llegada).between(fecha_inicio, fecha_fin)
        ).order_by(Ficha.fecha_hora_llegada).all()

        # Calcular estadísticas
        stats = _calcular_estadisticas(fichas)

        # Registrar acceso a reporte en bitácora
        BitacoraAuditoria.registrar(
            accion='GENERAR_REPORTE',
            tabla_afectada='fichas',
            detalle=f'Reporte generado: {fecha_inicio} a {fecha_fin} ({len(fichas)} fichas)'
        )

        if formato == 'csv':
            return _exportar_csv(fichas, stats, fecha_inicio, fecha_fin)

        return render_template(
            'reportes/resultado.html',
            fichas=fichas, stats=stats,
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
        )

    return render_template('reportes/generar.html')


def _calcular_estadisticas(fichas):
    """Calcula estadísticas del conjunto de fichas."""
    total = len(fichas)
    atendidos = sum(1 for f in fichas if f.estado == 'Finalizado')
    abandonaron = sum(1 for f in fichas if f.estado == 'Abandonó')

    tiempos = [f.tiempo_total_segundos for f in fichas
               if f.estado == 'Finalizado' and f.tiempo_total_segundos]
    promedio_min = sum(tiempos) / len(tiempos) / 60 if tiempos else 0

    # Por prioridad
    por_prioridad = {}
    for nivel in ['P1', 'P2', 'P3', 'P4', 'P5']:
        fichas_nivel = [f for f in fichas if f.prioridad_final == nivel]
        tiempos_nivel = [f.tiempo_total_segundos for f in fichas_nivel
                         if f.estado == 'Finalizado' and f.tiempo_total_segundos]
        por_prioridad[nivel] = {
            'total': len(fichas_nivel),
            'promedio_min': round(sum(tiempos_nivel) / len(tiempos_nivel) / 60, 1) if tiempos_nivel else 0,
        }

    return {
        'total': total,
        'atendidos': atendidos,
        'abandonaron': abandonaron,
        'promedio_espera_min': round(promedio_min, 1),
        'por_prioridad': por_prioridad,
    }


def _exportar_csv(fichas, stats, fecha_inicio, fecha_fin):
    """Exporta el reporte en formato CSV (RF5.2)."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['Reporte de Atención - Hospital del Norte'])
    writer.writerow([f'Período: {fecha_inicio} a {fecha_fin}'])
    writer.writerow([])
    writer.writerow(['Resumen'])
    writer.writerow(['Total pacientes', stats['total']])
    writer.writerow(['Atendidos', stats['atendidos']])
    writer.writerow(['Abandonaron', stats['abandonaron']])
    writer.writerow(['Tiempo promedio de espera (min)', stats['promedio_espera_min']])
    writer.writerow([])

    writer.writerow([
        'Número Ficha', 'Fecha Llegada', 'Paciente', 'CI',
        'Prioridad', 'Estado', 'Motivo', 'Diagnóstico',
        'Tiempo Total (min)'
    ])

    for f in fichas:
        writer.writerow([
            f.numero_ficha,
            f.fecha_hora_llegada.strftime('%Y-%m-%d %H:%M'),
            f.paciente.nombre_completo,
            f.paciente.ci,
            f.prioridad_final or 'Sin triage',
            f.estado,
            f.motivo_consulta[:80] if f.motivo_consulta else '',
            f.diagnostico_egreso[:80] if f.diagnostico_egreso else '',
            f.tiempo_total_segundos // 60 if f.tiempo_total_segundos else ''
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = (
        f'attachment; filename=reporte_{fecha_inicio}_{fecha_fin}.csv'
    )
    return response
