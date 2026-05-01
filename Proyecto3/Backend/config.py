import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base"""
    # Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    
    # MongoDB
    MONGO_USER = os.getenv('MONGO_USER', 'park_user')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'park_password')
    MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
    MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
    MONGO_DB = os.getenv('MONGO_DB', 'park_guard')
    MONGO_URI = os.getenv('MONGO_URI', f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin&retryWrites=true&w=majority")
    
    # JWT
    SECRET_KEY = os.getenv('SECRET_KEY', 'tu_clave_secreta_super_segura_aqui_cambiar_en_produccion')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    JWT_EXPIRATION = timedelta(hours=JWT_EXPIRATION_HOURS)
    
    # MQTT
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
    MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
    MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'username')
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'password')
    MQTT_KEEPALIVE = int(os.getenv('MQTT_KEEPALIVE', 60))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
