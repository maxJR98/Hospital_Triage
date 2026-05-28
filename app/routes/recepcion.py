"""
Rutas de Recepción
Hospital del Norte

Registro de llegada de pacientes y gestión de fichas (RF2)
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.paciente import Paciente
from app.models.ficha import Ficha
from app.models.historial_estado import HistorialEstadoFicha
from app.models.bitacora import BitacoraAuditoria
from app.utils.decorators import roles_requeridos

recepcion_bp = Blueprint('recepcion', __name__)


@recepcion_bp.route('/registro', methods=['GET', 'POST'])
@login_required
@roles_requeridos('Recepcionista', 'Administrador')
def registrar_paciente():
    """Registro de llegada de paciente y creación de ficha (RF2.1)."""
    if request.method == 'POST':
        # Datos del paciente
        ci = request.form.get('ci', '').strip()
        nombre = request.form.get('nombre_completo', '').strip()
        fecha_nacimiento = request.form.get('fecha_nacimiento')
        sexo = request.form.get('sexo')
        contacto = request.form.get('contacto', '').strip()
        motivo = request.form.get('motivo_consulta', '').strip()

        # Validaciones
        errores = []
        if not ci or len(ci) < 5:
            errores.append('La cédula de identidad es obligatoria (mínimo 5 caracteres).')
        if not nombre:
            errores.append('El nombre completo es obligatorio.')
        if not fecha_nacimiento:
            errores.append('La fecha de nacimiento es obligatoria.')
        if not sexo:
            errores.append('Seleccione el sexo del paciente.')
        if not contacto:
            errores.append('El número de contacto es obligatorio.')
        if not motivo:
            errores.append('El motivo de consulta es obligatorio.')

        if errores:
            for error in errores:
                flash(error, 'danger')
            return render_template('recepcion/registro_paciente.html')

        # Buscar o crear paciente
        paciente = Paciente.query.filter_by(ci=ci).first()
        if paciente is None:
            paciente = Paciente(
                ci=ci,
                nombre_completo=nombre,
                fecha_nacimiento=fecha_nacimiento,
                sexo=sexo,
                contacto=contacto
            )
            db.session.add(paciente)
            db.session.flush()  # Para obtener el ID antes del commit
        else:
            # Actualizar datos del paciente existente
            paciente.nombre_completo = nombre
            paciente.contacto = contacto

        # Generar número de ficha (formato YYYY-MM-DD-NNN)
        numero_ficha = Ficha.generar_numero_ficha()

        # Crear ficha
        ficha = Ficha(
            numero_ficha=numero_ficha,
            paciente_id=paciente.id,
            recepcionista_id=current_user.id,
            motivo_consulta=motivo,
            estado='En espera'
        )
        db.session.add(ficha)
        db.session.commit()

        # Registrar en bitácora
        BitacoraAuditoria.registrar(
            accion='CREAR_FICHA',
            tabla_afectada='fichas',
            registro_id=ficha.id,
            detalle=f'Ficha {numero_ficha} creada para paciente {nombre} (CI: {ci})'
        )

        flash(f'Ficha {numero_ficha} creada exitosamente. Paciente en espera.', 'success')
        return redirect(url_for('recepcion.lista_fichas'))

    return render_template('recepcion/registro_paciente.html')


@recepcion_bp.route('/fichas')
@login_required
@roles_requeridos('Recepcionista', 'Administrador', 'Médico de Triage', 'Médico Tratante')
def lista_fichas():
    """Lista de fichas del día (RF2.2)."""
    from datetime import datetime
    hoy = datetime.utcnow().date()

    # Filtro de búsqueda
    busqueda = request.args.get('buscar', '').strip()

    query = Ficha.query.join(Paciente)

    if busqueda:
        query = query.filter(
            db.or_(
                Ficha.numero_ficha.contains(busqueda),
                Paciente.nombre_completo.contains(busqueda),
                Paciente.ci.contains(busqueda)
            )
        )
    else:
        query = query.filter(db.func.date(Ficha.fecha_hora_llegada) == hoy)

    fichas = query.order_by(Ficha.fecha_hora_llegada.desc()).all()
    return render_template('recepcion/lista_fichas.html', fichas=fichas, busqueda=busqueda)


@recepcion_bp.route('/fichas/<int:ficha_id>')
@login_required
@roles_requeridos('Recepcionista', 'Administrador', 'Médico de Triage', 'Médico Tratante')
def detalle_ficha(ficha_id):
    """Detalle de una ficha (RF2.2)."""
    ficha = Ficha.query.get_or_404(ficha_id)
    return render_template('recepcion/detalle_ficha.html', ficha=ficha)


@recepcion_bp.route('/fichas/<int:ficha_id>/abandonar', methods=['POST'])
@login_required
@roles_requeridos('Recepcionista', 'Administrador')
def marcar_abandono(ficha_id):
    """Marca una ficha como abandonada."""
    ficha = Ficha.query.get_or_404(ficha_id)

    if ficha.estado not in ('En espera', 'En triage'):
        flash('Solo se pueden marcar como abandonadas fichas en espera o en triage.', 'warning')
        return redirect(url_for('recepcion.lista_fichas'))

    HistorialEstadoFicha.registrar_cambio(ficha, 'Abandonó', current_user.id)

    BitacoraAuditoria.registrar(
        accion='MARCAR_ABANDONO',
        tabla_afectada='fichas',
        registro_id=ficha.id,
        detalle=f'Ficha {ficha.numero_ficha} marcada como abandonada'
    )

    flash(f'Ficha {ficha.numero_ficha} marcada como abandonada.', 'info')
    return redirect(url_for('recepcion.lista_fichas'))
