"""
Punto de entrada del Sistema Inteligente de Triage
Hospital del Norte - La Paz, El Alto
"""
from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=app.config.get('DEBUG', True)
    )
