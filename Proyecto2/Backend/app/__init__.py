from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from pymongo import MongoClient
from config import config
import os

# Instancias globales
mongo_client = None
db = None
socketio = None

def create_app(config_name=None):
    """Factory para crear la aplicación Flask"""
    
    global socketio
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Habilitar CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Inicializar SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        ping_timeout=60,
        ping_interval=25
    )
    
    # Inicializar MongoDB
    init_mongo(app)
    
    # Registrar blueprints
    from app.routes import auth_routes, users_routes, parking_routes, events_routes, commands_routes
    
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(users_routes.bp)
    app.register_blueprint(parking_routes.bp)
    app.register_blueprint(events_routes.bp)
    app.register_blueprint(commands_routes.bp)
    
    # Registrar eventos WebSocket
    from app.websocket import register_socketio_events
    register_socketio_events(socketio)
    
    # Ruta de health check
    @app.route('/api/health', methods=['GET'])
    def health():
        return {'status': 'OK', 'message': 'Backend is running'}, 200
    
    return app, socketio

def init_mongo(app):
    """Inicializar conexión a MongoDB"""
    global mongo_client, db
    
    try:
        mongo_client = MongoClient(app.config['MONGO_URI'])
        db = mongo_client[app.config['MONGO_DB']]
        
        # Verificar conexión
        mongo_client.admin.command('ping')
        print("✓ Conexión a MongoDB establecida")
    except Exception as e:
        print(f"✗ Error conectando a MongoDB: {e}")
        raise

def get_db():
    """Obtener la instancia de la base de datos"""
    global db
    if db is None:
        raise RuntimeError("Database not initialized")
    return db

def get_socketio():
    """Obtener la instancia de SocketIO"""
    global socketio
    if socketio is None:
        raise RuntimeError("SocketIO not initialized")
    return socketio
