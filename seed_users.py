"""
Script de Semilla (Seed) para Usuarios de Prueba
Hospital del Norte - Sistema Inteligente de Triage

Este script crea cuentas de prueba para cada uno de los roles definidos en la base de datos
utilizando contraseñas seguras generadas mediante bcrypt.
"""
from app import create_app
from app.extensions import db
from app.models.usuario import Usuario
from app.models.rol import Rol

# Crear la aplicación Flask con el contexto
app = create_app()

def seed_users():
    with app.app_context():
        print("====== INICIANDO GENERACIÓN DE USUARIOS SEMILLA ======")
        
        # Verificar que los roles existan
        roles_necesarios = {
            1: 'Administrador',
            2: 'Médico de Triage',
            3: 'Recepcionista',
            4: 'Médico Tratante',
            5: 'Director'
        }
        
        for r_id, r_nombre in roles_necesarios.items():
            rol = Rol.query.get(r_id)
            if not rol:
                nuevo_rol = Rol()
                nuevo_rol.id = r_id
                nuevo_rol.nombre = r_nombre
                nuevo_rol.descripcion = f"Rol de {r_nombre}"
                db.session.add(nuevo_rol)
        db.session.commit()
        
        # Definición de usuarios semilla a registrar
        usuarios_semilla = [
            {
                "email": "admin@hospitalnorte.bo",
                "nombre_completo": "Administrador del Sistema",
                "ci": "9999999",
                "rol_id": 1,
                "password": "Admin2026!"
            },
            {
                "email": "triage@hospitalnorte.bo",
                "nombre_completo": "Dr. Jorge Flores (Triage)",
                "ci": "8888888",
                "rol_id": 2,
                "password": "Triage2026!"
            },
            {
                "email": "recepcion@hospitalnorte.bo",
                "nombre_completo": "Lic. Ana Quispe (Recepción)",
                "ci": "7777777",
                "rol_id": 3,
                "password": "Recepcion2026!"
            },
            {
                "email": "medico@hospitalnorte.bo",
                "nombre_completo": "Dra. Elena Mamani (Médico Tratante)",
                "ci": "6666666",
                "rol_id": 4,
                "password": "Medico2026!"
            },
            {
                "email": "director@hospitalnorte.bo",
                "nombre_completo": "Dr. Walter Gomez (Director)",
                "ci": "5555555",
                "rol_id": 5,
                "password": "Director2026!"
            }
        ]
        
        for u_data in usuarios_semilla:
            # Buscar si el usuario ya existe
            user = Usuario.query.filter_by(email=u_data["email"]).first()
            
            if user:
                print(f"-> Actualizando contraseña para {u_data['nombre_completo']} ({u_data['email']})...")
                user.set_password(u_data["password"])
                user.nombre_completo = u_data["nombre_completo"]
                user.ci = u_data["ci"]
                user.rol_id = u_data["rol_id"]
                user.estado = "activo"
            else:
                print(f"-> Creando nuevo usuario: {u_data['nombre_completo']} ({u_data['email']})...")
                user = Usuario()
                user.nombre_completo = u_data["nombre_completo"]
                user.ci = u_data["ci"]
                user.email = u_data["email"]
                user.rol_id = u_data["rol_id"]
                user.estado = "activo"
                user.set_password(u_data["password"])
                db.session.add(user)
                
        db.session.commit()
        print("\n====== SEMILLA DE USUARIOS GENERADA CON ÉXITO ======")
        print("\nCuentas disponibles para pruebas:")
        print("--------------------------------------------------------------------------------")
        for u_data in usuarios_semilla:
            rol_name = roles_necesarios[u_data['rol_id']]
            print(f" Rol: {rol_name:<20} | Correo: {u_data['email']:<28} | Clave: {u_data['password']}")
        print("--------------------------------------------------------------------------------")

if __name__ == "__main__":
    seed_users()
