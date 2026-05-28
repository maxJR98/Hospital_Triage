"""
Rutas de Autenticación
Hospital del Norte

Login, logout, recuperación de contraseña (RF1.2, RF1.5)
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    """Redirige al dashboard o al login según autenticación."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión del sistema (RF1.2)."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Por favor ingrese su correo electrónico y contraseña.', 'warning')
            return render_template('auth/login.html')

        usuario, error = AuthService.autenticar(email, password)

        if error:
            flash(error, 'danger')
            return render_template('auth/login.html')

        login_user(usuario, remember=False)
        flash(f'Bienvenido/a, {usuario.nombre_completo}.', 'success')

        # Redirigir a la página solicitada o al dashboard
        next_page = request.args.get('next')
        return redirect(next_page or url_for('auth.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Cierre de sesión (RNF2.4)."""
    AuthService.cerrar_sesion(current_user.id)
    logout_user()
    flash('Sesión cerrada exitosamente.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar_password():
    """Solicitud de recuperación de contraseña (RF1.5)."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash('Por favor ingrese su correo electrónico institucional.', 'warning')
            return render_template('auth/recuperar.html')

        token, error = AuthService.solicitar_recuperacion(email)

        # Siempre mostrar mensaje genérico por seguridad
        flash(
            'Si el correo electrónico está registrado, recibirá un enlace '
            'de recuperación en los próximos minutos.',
            'info'
        )
        return redirect(url_for('auth.login'))

    return render_template('auth/recuperar.html')


@auth_bp.route('/restablecer/<token>', methods=['GET', 'POST'])
def restablecer_password(token):
    """Restablecimiento de contraseña con token (RF1.5)."""
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('auth/restablecer.html', token=token)

        exito, mensaje = AuthService.restablecer_password(token, password)

        if exito:
            flash(mensaje, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(mensaje, 'danger')
            return render_template('auth/restablecer.html', token=token)

    return render_template('auth/restablecer.html', token=token)


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Panel de control principal con indicadores según rol (RF5.3)."""
    return render_template('dashboard.html')
