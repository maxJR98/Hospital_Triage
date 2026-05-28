"""
Rutas de Administración
Hospital del Norte

Gestión de usuarios, roles, reglas clínicas y configuraciones (RF1.1, RF1.3, RF1.4, RF3.4)
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.regla_clinica import ReglaClinica
from app.models.configuracion import Configuracion
from app.models.bitacora import BitacoraAuditoria
from app.utils.decorators import solo_admin

admin_bp = Blueprint('admin', __name__)


# =========================================================
# GESTIÓN DE USUARIOS (RF1.1, RF1.3, RF1.4)
# =========================================================

@admin_bp.route('/usuarios')
@login_required
@solo_admin
def listar_usuarios():
    """Lista todos los usuarios del sistema."""
    usuarios = Usuario.query.join(Rol).order_by(Usuario.nombre_completo).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


@admin_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@solo_admin
def crear_usuario():
    """Formulario de registro de nuevo usuario (RF1.1)."""
    roles = Rol.query.order_by(Rol.id).all()

    if request.method == 'POST':
        nombre = request.form.get('nombre_completo', '').strip()
        ci = request.form.get('ci', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        rol_id = request.form.get('rol_id', type=int)

        # Validaciones
        errores = []
        if not nombre or len(nombre) < 3:
            errores.append('El nombre completo es obligatorio (mínimo 3 caracteres).')
        if not ci or len(ci) < 5:
            errores.append('La cédula de identidad es obligatoria (mínimo 5 caracteres).')
        if not email or '@' not in email:
            errores.append('Ingrese un correo electrónico válido.')
        if not password or len(password) < 8:
            errores.append('La contraseña debe tener al menos 8 caracteres.')
        if not rol_id:
            errores.append('Seleccione un rol para el usuario.')

        # Verificar duplicados (RF1.1)
        if Usuario.query.filter_by(ci=ci).first():
            errores.append('Ya existe un usuario con esa cédula de identidad.')
        if Usuario.query.filter_by(email=email).first():
            errores.append('Ya existe un usuario con ese correo electrónico.')

        if errores:
            for error in errores:
                flash(error, 'danger')
            return render_template('admin/usuario_form.html', roles=roles, modo='crear')

        # Crear usuario
        usuario = Usuario(
            nombre_completo=nombre,
            ci=ci,
            email=email,
            rol_id=rol_id,
            estado='activo'
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()

        # Registrar en bitácora
        BitacoraAuditoria.registrar(
            accion='CREAR_USUARIO',
            tabla_afectada='usuarios',
            registro_id=usuario.id,
            detalle=f'Usuario creado: {nombre} ({email}), Rol: {usuario.nombre_rol}'
        )

        flash(f'Usuario {nombre} creado exitosamente.', 'success')
        return redirect(url_for('admin.listar_usuarios'))

    return render_template('admin/usuario_form.html', roles=roles, modo='crear')


@admin_bp.route('/usuarios/<int:usuario_id>/editar', methods=['GET', 'POST'])
@login_required
@solo_admin
def editar_usuario(usuario_id):
    """Edición de datos de usuario (RF1.3)."""
    usuario = Usuario.query.get_or_404(usuario_id)
    roles = Rol.query.order_by(Rol.id).all()

    if request.method == 'POST':
        campos_modificados = []

        nombre = request.form.get('nombre_completo', '').strip()
        if nombre and nombre != usuario.nombre_completo:
            campos_modificados.append(f'nombre: {usuario.nombre_completo} → {nombre}')
            usuario.nombre_completo = nombre

        email = request.form.get('email', '').strip()
        if email and email != usuario.email:
            if Usuario.query.filter(Usuario.email == email, Usuario.id != usuario_id).first():
                flash('Ya existe otro usuario con ese correo electrónico.', 'danger')
                return render_template('admin/usuario_form.html', usuario=usuario, roles=roles, modo='editar')
            campos_modificados.append(f'email: {usuario.email} → {email}')
            usuario.email = email

        rol_id = request.form.get('rol_id', type=int)
        if rol_id and rol_id != usuario.rol_id:
            rol_anterior = usuario.nombre_rol
            usuario.rol_id = rol_id
            campos_modificados.append(f'rol: {rol_anterior} → {usuario.nombre_rol}')

        nueva_password = request.form.get('password', '')
        if nueva_password:
            if len(nueva_password) < 8:
                flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
                return render_template('admin/usuario_form.html', usuario=usuario, roles=roles, modo='editar')
            usuario.set_password(nueva_password)
            campos_modificados.append('contraseña actualizada')

        if campos_modificados:
            db.session.commit()
            # Registrar en bitácora (RF1.3)
            BitacoraAuditoria.registrar(
                accion='MODIFICAR_USUARIO',
                tabla_afectada='usuarios',
                registro_id=usuario.id,
                detalle=f'Campos modificados: {"; ".join(campos_modificados)}'
            )
            flash('Usuario actualizado exitosamente.', 'success')
        else:
            flash('No se realizaron cambios.', 'info')

        return redirect(url_for('admin.listar_usuarios'))

    return render_template('admin/usuario_form.html', usuario=usuario, roles=roles, modo='editar')


@admin_bp.route('/usuarios/<int:usuario_id>/desactivar', methods=['POST'])
@login_required
@solo_admin
def desactivar_usuario(usuario_id):
    """Desactivación de cuenta de usuario (RF1.4)."""
    usuario = Usuario.query.get_or_404(usuario_id)

    if usuario.id == current_user.id:
        flash('No puede desactivar su propia cuenta.', 'danger')
        return redirect(url_for('admin.listar_usuarios'))

    nuevo_estado = 'inactivo' if usuario.estado == 'activo' else 'activo'
    estado_anterior = usuario.estado
    usuario.estado = nuevo_estado
    db.session.commit()

    BitacoraAuditoria.registrar(
        accion='CAMBIO_ESTADO_USUARIO',
        tabla_afectada='usuarios',
        registro_id=usuario.id,
        detalle=f'Estado: {estado_anterior} → {nuevo_estado}'
    )

    accion = 'desactivada' if nuevo_estado == 'inactivo' else 'activada'
    flash(f'Cuenta de {usuario.nombre_completo} {accion} exitosamente.', 'success')
    return redirect(url_for('admin.listar_usuarios'))


# =========================================================
# GESTIÓN DE REGLAS CLÍNICAS (RF3.4)
# =========================================================

@admin_bp.route('/reglas')
@login_required
@solo_admin
def listar_reglas():
    """Lista las reglas clínicas del módulo inteligente."""
    reglas = ReglaClinica.query.order_by(ReglaClinica.nivel_prioridad, ReglaClinica.parametro).all()
    return render_template('admin/reglas.html', reglas=reglas)


@admin_bp.route('/reglas/nueva', methods=['GET', 'POST'])
@login_required
@solo_admin
def crear_regla():
    """Formulario de creación de regla clínica (RF3.4)."""
    if request.method == 'POST':
        regla = ReglaClinica(
            parametro=request.form.get('parametro'),
            operador=request.form.get('operador'),
            valor_umbral=request.form.get('valor_umbral', '').strip(),
            nivel_prioridad=request.form.get('nivel_prioridad'),
            descripcion=request.form.get('descripcion', '').strip(),
            activo=request.form.get('activo') == 'on'
        )
        db.session.add(regla)
        db.session.commit()

        BitacoraAuditoria.registrar(
            accion='CREAR_REGLA_CLINICA',
            tabla_afectada='reglas_clinicas',
            registro_id=regla.id,
            detalle=f'Regla: {regla.parametro} {regla.operador} {regla.valor_umbral} → {regla.nivel_prioridad}'
        )

        flash('Regla clínica creada exitosamente.', 'success')
        return redirect(url_for('admin.listar_reglas'))

    return render_template('admin/regla_form.html', modo='crear')


@admin_bp.route('/reglas/<int:regla_id>/toggle', methods=['POST'])
@login_required
@solo_admin
def toggle_regla(regla_id):
    """Activar/desactivar una regla clínica (RF3.4)."""
    regla = ReglaClinica.query.get_or_404(regla_id)
    regla.activo = not regla.activo
    db.session.commit()

    estado = 'activada' if regla.activo else 'desactivada'
    BitacoraAuditoria.registrar(
        accion='TOGGLE_REGLA_CLINICA',
        tabla_afectada='reglas_clinicas',
        registro_id=regla.id,
        detalle=f'Regla {estado}: {regla.descripcion}'
    )

    flash(f'Regla clínica {estado}.', 'success')
    return redirect(url_for('admin.listar_reglas'))


# =========================================================
# BITÁCORA DE AUDITORÍA (RNF2.4)
# =========================================================

@admin_bp.route('/bitacora')
@login_required
@solo_admin
def ver_bitacora():
    """Vista de la bitácora de auditoría."""
    page = request.args.get('page', 1, type=int)
    registros = BitacoraAuditoria.query.order_by(
        BitacoraAuditoria.fecha_hora.desc()
    ).paginate(page=page, per_page=50)
    return render_template('admin/bitacora.html', registros=registros)
