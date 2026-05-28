# Sistema Inteligente de Triage y Gestión de Fichas - Hospital del Norte

Este es un sistema web moderno diseñado para automatizar y optimizar el proceso de Triage médico y la gestión de la cola de atención en tiempo real en el **Hospital del Norte (La Paz, El Alto)**. Basado en criterios clínicos estandarizados (Escala de Manchester adaptada), clasifica de forma automática a los pacientes según su gravedad y prioriza su orden de atención médica.

---

## 🚀 Características Principales

*   **Autenticación y Seguridad (RF1)**: Gestión de usuarios bajo modelo RBAC (Administrador, Médico de Triage, Médico Tratante, Recepcionista, Director) con bloqueo automático por intentos fallidos.
*   **Gestión de Recepción (RF2)**: Registro rápido de pacientes y emisión de fichas diarias con numeración única `YYYY-MM-DD-NNN`.
*   **Módulo de Triage Inteligente (RF3)**: Registro de signos vitales (presión, pulso, saturación, dolor, temperatura) con clasificación sugerida automática mediante reglas parametrizables.
*   **Cola de Atención en Tiempo Real (RF4)**: Panel interactivo que muestra dinámicamente a los pacientes en espera ordenados estrictamente por prioridad de gravedad y tiempo de espera.
*   **Dashboard y Reportes Estadísticos (RF5)**: Visualización de indicadores clave (tiempos promedio, pacientes atendidos, nivel de abandono) y exportación a archivos CSV y PDF.
*   **Bitácora de Auditoría Inmutable (RNF2.4)**: Registro DB de acciones críticas protegido mediante disparadores (triggers) a nivel de base de datos para impedir cualquier modificación o eliminación.

---

## 🛠️ Stack Tecnológico

*   **Backend**: Python 3.13 + Flask (Microframework)
*   **Base de Datos**: MySQL / MariaDB
*   **Frontend**: HTML5, Bootstrap 5, CSS3 (Glassmorphism & Diseño Premium), JavaScript ES6 (Vanilla)
*   **Tiempo Real**: Flask-SocketIO (WebSockets)
*   **Seguridad**: Encriptación de contraseñas mediante `bcrypt`

---

## 📦 Guía de Instalación y Configuración

### 1. Clonar el repositorio
Si acabas de clonar el proyecto, sitúate en el directorio raíz en tu terminal:
```bash
cd "Proyecto Fase II"
```

### 2. Configurar el Entorno Virtual (venv)
Si no cuentas con el entorno virtual creado, inicialízalo e instala las dependencias necesarias:

**En Windows (PowerShell):**
```powershell
python -m venv venv
& ".\venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

### 3. Configurar la Base de Datos
1. Inicia tu servidor local de MySQL (XAMPP, WampServer o MySQL directo).
2. Importa el esquema y los datos semilla desde tu consola o gestor visual (como phpMyAdmin o DBeaver):
   ```powershell
   cmd.exe /c "mysql -u root -p < hospital_triage.sql"
   ```
   *(Si el usuario `root` no tiene contraseña, puedes omitir la opción `-p`)*.

### 4. Configurar las Variables de Entorno
Copia el archivo `.env.example` y renombralo como `.env`:
```powershell
copy .env.example .env
```
Abre el archivo `.env` en tu editor y ajusta las credenciales de conexión a tu base de datos local (`DB_USER`, `DB_PASSWORD`, etc.) si es necesario.

### 5. Sembrar Cuentas de Usuario de Prueba
Para poder probar todos los roles del sistema, ejecuta el script de semillas en tu terminal activa:
```powershell
python seed_users.py
```
Este script creará o actualizará cuentas de prueba con contraseñas encriptadas con `bcrypt`:
*   **Administrador**: `admin@hospitalnorte.bo` (Clave: `Admin2026!`)
*   **Médico de Triage**: `triage@hospitalnorte.bo` (Clave: `Triage2026!`)
*   **Recepcionista**: `recepcion@hospitalnorte.bo` (Clave: `Recepcion2026!`)
*   **Médico Tratante**: `medico@hospitalnorte.bo` (Clave: `Medico2026!`)
*   **Director**: `director@hospitalnorte.bo` (Clave: `Director2026!`)

---

## ⚡ Ejecución de la Aplicación

Para iniciar el servidor local en modo desarrollo:
```powershell
python run.py
```

Abre tu navegador y entra en la siguiente URL:
👉 **[http://localhost:5000](http://localhost:5000)**

---

## 📂 Estructura del Proyecto

```text
├── app/                      # Código fuente de la aplicación Flask
│   ├── models/               # Modelos de base de datos (SQLAlchemy)
│   ├── routes/               # Blueprints (Controladores de rutas)
│   ├── services/             # Lógica de negocio (Autenticación, Triage)
│   ├── static/               # Recursos estáticos (CSS, JS)
│   ├── templates/            # Vistas en HTML (Motor de plantillas Jinja2)
│   ├── utils/                # Utilidades y decoradores (RBAC, etc.)
│   ├── __init__.py           # Inicialización del App Factory
│   ├── config.py             # Archivo de configuraciones generales
│   └── extensions.py         # Registro de extensiones (db, socketio, etc.)
├── venv/                     # Carpeta del entorno virtual (Ignorada por Git)
├── .env                      # Variables de entorno activas (Ignorado por Git)
├── .env.example              # Plantilla para variables de entorno
├── .gitignore                # Archivos y carpetas a ignorar por Git
├── hospital_triage.sql       # Script de creación de DB, Triggers y Semillas
├── requirements.txt          # Dependencias y librerías del proyecto
├── run.py                    # Punto de entrada de la aplicación
└── seed_users.py             # Script de siembra para usuarios de prueba
```
