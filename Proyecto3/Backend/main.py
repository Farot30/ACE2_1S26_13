"""
Punto de entrada de la aplicación Park-Guard Backend

Ejecutar con:
    python main.py

En desarrollo, la aplicación estará disponible en: http://localhost:5000
WebSocket disponible en: ws://localhost:5000/socket.io
"""

import os
from app import create_app
from config import config
from app.services import MQTTService, ParkingService

# Crear aplicación y socketio
config_name = os.getenv('FLASK_ENV', 'development')
app, socketio = create_app(config_name)

# Inicializar MQTT
@app.before_request
def init_mqtt():
    """Inicializar MQTT antes de la primera solicitud"""
    mqtt = MQTTService()
    if not hasattr(app, 'mqtt_initialized'):
        try:
            mqtt.connect()
            app.mqtt_initialized = True
            
            # Inicializar espacios de parqueo
            ParkingService.initialize_parking_spaces()
        except Exception as e:
            print(f"Error inicializando MQTT o parking spaces: {e}")

@app.teardown_appcontext
def shutdown_mqtt(exception=None):
    """Desconectar MQTT al cerrar la aplicación"""
    mqtt = MQTTService()
    mqtt.disconnect()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print(f"""
================== Park-Guard 2.0 Backend API ==================                   
======== Sistema IoT de Gestión y Analítica de Parqueos ========
================================================================
    
    Ambiente: {os.getenv('FLASK_ENV', 'development').upper()}
    Puerto: {port}
    Debug: {debug}
    
    Endpoints:
    - REST API: http://localhost:{port}/api/*
    - Health Check: http://localhost:{port}/api/health
    - WebSocket: ws://localhost:{port}/socket.io
    
    MongoDB: {os.getenv('MONGO_URI', 'mongodb://localhost:27017')}
    MQTT Broker: {os.getenv('MQTT_BROKER', 'localhost')}:{os.getenv('MQTT_PORT', '1883')}
    """)
    
    # Ejecutar con SocketIO
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
