"""
Servicio de Autenticación
Hospital del Norte

Lógica de negocio para login, logout, bloqueo de cuenta
y recuperación de contraseña (RF1).
"""
from datetime import datetime
from app.extensions import db
from app.models.usuario import Usuario
from app.models.token_recuperacion import TokenRecuperacion
from app.models.bitacora import BitacoraAuditoria
from app.models.configuracion import Configuracion


class AuthService:
    """Servicio de autenticación y gestión de sesiones."""

    @staticmethod
    def autenticar(email, password):
        """Autentica un usuario por email y contraseña (RF1.2).

        Returns:
            tuple: (usuario, mensaje_error)
                - Si éxito: (usuario, None)
                - Si error: (None, mensaje)
        """
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario is None:
            return None, 'Correo electrónico o contraseña incorrectos.'

        # Verificar si la cuenta está bloqueada
        if usuario.esta_bloqueado:
            minutos = Configuracion.get_int('bloqueo_minutos', 15)
            return None, (
                f'Cuenta bloqueada temporalmente por múltiples intentos fallidos. '
                f'Intente nuevamente en {minutos} minutos.'
            )

        # Verificar si la cuenta está inactiva
        if usuario.estado == 'inactivo':
            return None, 'Su cuenta ha sido desactivada. Contacte al administrador del sistema.'

        # Verificar contraseña
        if not usuario.check_password(password):
            usuario.registrar_intento_fallido()
            intentos_restantes = Configuracion.get_int('intentos_max_login', 5) - usuario.intentos_fallidos
            if intentos_restantes > 0:
                return None, (
                    f'Correo electrónico o contraseña incorrectos. '
                    f'Le quedan {intentos_restantes} intento(s).'
                )
            else:
                minutos = Configuracion.get_int('bloqueo_minutos', 15)
                return None, (
                    f'Cuenta bloqueada por {minutos} minutos debido a múltiples intentos fallidos.'
                )

        # Login exitoso: resetear intentos
        usuario.resetear_intentos()

        # Registrar en bitácora
        BitacoraAuditoria.registrar(
            accion='INICIO_SESION',
            tabla_afectada='usuarios',
            registro_id=usuario.id,
            detalle=f'Inicio de sesión exitoso del usuario {usuario.email}',
            usuario_id=usuario.id
        )

        return usuario, None

    @staticmethod
    def cerrar_sesion(usuario_id):
        """Registra el cierre de sesión en la bitácora."""
        BitacoraAuditoria.registrar(
            accion='CIERRE_SESION',
            tabla_afectada='usuarios',
            registro_id=usuario_id,
            detalle='Cierre de sesión',
            usuario_id=usuario_id
        )

    @staticmethod
    def solicitar_recuperacion(email):
        """Genera un token de recuperación de contraseña (RF1.5).

        Returns:
            tuple: (token, mensaje_error)
        """
        usuario = Usuario.query.filter_by(email=email, estado='activo').first()

        if usuario is None:
            # Por seguridad, no revelar si el email existe
            return None, None

        minutos = Configuracion.get_int('token_recuperacion_minutos', 30)
        token = TokenRecuperacion.generar(usuario.id, minutos)

        BitacoraAuditoria.registrar(
            accion='SOLICITUD_RECUPERACION',
            tabla_afectada='tokens_recuperacion',
            registro_id=token.id,
            detalle=f'Solicitud de recuperación de contraseña para {email}',
            usuario_id=usuario.id
        )

        return token, None

    @staticmethod
    def restablecer_password(token_str, nueva_password):
        """Restablece la contraseña usando un token válido (RF1.5).

        Returns:
            tuple: (exito, mensaje)
        """
        token = TokenRecuperacion.query.filter_by(token=token_str).first()

        if token is None or not token.es_valido:
            return False, 'El enlace de recuperación es inválido o ha expirado.'

        if len(nueva_password) < 8:
            return False, 'La contraseña debe tener al menos 8 caracteres.'

        usuario = Usuario.query.get(token.usuario_id)
        usuario.set_password(nueva_password)
        token.marcar_usado()
        db.session.commit()

        BitacoraAuditoria.registrar(
            accion='RESTABLECIMIENTO_PASSWORD',
            tabla_afectada='usuarios',
            registro_id=usuario.id,
            detalle='Contraseña restablecida mediante token de recuperación',
            usuario_id=usuario.id
        )

        return True, 'Contraseña restablecida exitosamente.'
