"""
Decoradores de Autorización
Hospital del Norte

Implementa RBAC (Control de Acceso Basado en Roles) (RNF2.3)
mediante decoradores para proteger las rutas del sistema.
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def roles_requeridos(*roles):
    """Decorador que restringe el acceso a usuarios con los roles indicados.

    Uso:
        @roles_requeridos('Administrador', 'Director')
        def vista_protegida():
            ...

    Args:
        *roles: Nombres de roles permitidos.

    Returns:
        403 Forbidden si el usuario no tiene un rol autorizado.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debe iniciar sesión para acceder a esta página.', 'warning')
                return redirect(url_for('auth.login'))

            if not current_user.tiene_rol(*roles):
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def solo_admin(f):
    """Decorador de acceso exclusivo para Administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.tiene_rol('Administrador'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
