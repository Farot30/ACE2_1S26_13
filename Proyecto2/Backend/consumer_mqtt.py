"""
Consumer MQTT para Park-Guard 2.0
Lee eventos de sensores desde el broker MQTT y los persiste en MongoDB.
También emite eventos Socket.IO en tiempo real al Frontend.

Uso:
    python consumer_mqtt.py

Variables de entorno:
    MQTT_BROKER: IP/host del broker (default: localhost)
    MQTT_PORT: Puerto MQTT (default: 1883)
    MONGO_HOST: Host de MongoDB (default: localhost)
    MONGO_PORT: Puerto de MongoDB (default: 27017)
    MONGO_USER: Usuario MongoDB (default: park_user)
    MONGO_PASSWORD: Contraseña MongoDB (default: park_password)
    MONGO_DB: Base de datos (default: park_guard)
"""

import json
import os
import time
import threading
from datetime import datetime
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import logging

# Cargar variables de entorno
load_dotenv()

# Configuración
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_KEEPALIVE = 60

MONGO_USER = os.getenv('MONGO_USER', 'park_user')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'park_password')
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB = os.getenv('MONGO_DB', 'park_guard')
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin&retryWrites=true&w=majority"

# Topics MQTT a escuchar
TOPICS_MQTT = {
    'parking':   'park-guard/parking/+/status',
    'gas':       'park-guard/gas/sensor',
    'rfid':      'park-guard/rfid/read',
    'emergency': 'park-guard/emergency/trigger',
    'ventilator': 'park-guard/ventilator/command',
}

# Variables globales para Socket.IO
# Se inicializarán cuando se importe desde main.py
socketio_instance = None

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConsumerMQTT:
    """Consumidor de eventos MQTT que persiste en MongoDB y emite por Socket.IO"""
    
    def __init__(self, mqtt_broker, mqtt_port, mongo_uri, socketio=None):
        """
        Inicializar Consumer MQTT
        
        Args:
            mqtt_broker: Host del broker MQTT
            mqtt_port: Puerto del broker MQTT
            mongo_uri: URI de conexión a MongoDB
            socketio: Instancia de SocketIO (opcional)
        """
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mongo_uri = mongo_uri
        self.socketio = socketio
        
        # Clientes
        self.mqtt_client = None
        self.mongo_client = None
        self.db = None
        
        # Estado
        self.conectado = False
        self.corriendo = False
    
    def conectar(self):
        """Conectar a MQTT y MongoDB"""
        self._conectar_mqtt()
        self._conectar_mongodb()
        self.corriendo = True
        logger.info("Consumer MQTT iniciado")
    
    def _conectar_mqtt(self):
        """Conectar al broker MQTT"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            self.mqtt_client.on_message = self._on_mqtt_message
            
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, MQTT_KEEPALIVE)
            self.mqtt_client.loop_start()
            
            logger.info(f"Conectado a MQTT broker: {self.mqtt_broker}:{self.mqtt_port}")
        except Exception as e:
            logger.error(f"Error conectando a MQTT: {e}")
            raise
    
    def _conectar_mongodb(self):
        """Conectar a MongoDB"""
        try:
            self.mongo_client = MongoClient(self.mongo_uri)
            self.db = self.mongo_client[MONGO_DB]
            
            # Verificar conexión
            self.mongo_client.admin.command('ping')
            logger.info(f"Conectado a MongoDB: {MONGO_DB}")
        except Exception as e:
            logger.error(f"Error conectando a MongoDB: {e}")
            raise
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback de conexión MQTT"""
        if rc == 0:
            logger.info("MQTT broker conectado")
            self.conectado = True
            
            # Suscribirse a todos los topics
            for nombre, topic in TOPICS_MQTT.items():
                client.subscribe(topic, qos=1)
                logger.info(f"Suscrito a: {topic}")
        else:
            logger.error(f"Error de conexión MQTT: {rc}")
            self.conectado = False
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """Callback de desconexión MQTT"""
        if rc != 0:
            logger.warning(f"Desconexión inesperada de MQTT: {rc}")
        self.conectado = False
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Callback cuando se recibe un mensaje MQTT"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Procesar según el tipo de topic
            if 'parking' in topic:
                self._procesar_parking(topic, payload)
            elif 'gas' in topic:
                self._procesar_gas(payload)
            elif 'rfid' in topic:
                self._procesar_rfid(payload)
            elif 'emergency' in topic:
                self._procesar_emergency(payload)
            elif 'ventilator' in topic:
                self._procesar_ventilador(payload)
            
            logger.info(f"Procesado {topic}: {payload}")
        except json.JSONDecodeError:
            logger.warning(f"JSON inválido en {msg.topic}: {msg.payload}")
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
    
    def _procesar_parking(self, topic, payload):
        """
        Procesar actualización de espacio de parqueo
        Topic: park-guard/parking/{space}/status
        Payload: {"type": "parking", "space": 1, "is_occupied": true, "timestamp": "..."}
        """
        space_number = payload.get('space')
        is_occupied = payload.get('is_occupied', False)
        timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
        
        if space_number is None:
            logger.warning(f"Space number no definido en payload: {payload}")
            return
        
        # Actualizar en MongoDB
        self.db.parking_spaces.update_one(
            {'space_number': space_number},
            {
                '$set': {
                    'is_occupied': is_occupied,
                    'last_updated': timestamp
                }
            },
            upsert=True
        )
        
        # Emitir Socket.IO al Frontend
        if self.socketio:
            try:
                self.socketio.emit('parking_update', {
                    'space_number': space_number,
                    'is_occupied': is_occupied,
                    'timestamp': timestamp
                }, room='parking-updates')
                logger.info(f"Socket.IO: parking_update espacio {space_number}")
            except Exception as e:
                logger.error(f"Error Socket.IO: {e}")
        
        logger.info(f"Espacio {space_number}: {'Ocupado' if is_occupied else 'Libre'}")
    
    def _procesar_gas(self, payload):
        """
        Procesar lectura de sensor de gas
        Payload: {"type": "gas", "ppm": 150, "timestamp": "..."}
        """
        ppm = payload.get('ppm', 0)
        timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
        
        # Guardar estadística en MongoDB
        self.db.statistics.insert_one({
            'type': 'gas_reading',
            'ppm': ppm,
            'timestamp': timestamp
        })
        
        # Emitir Socket.IO
        if self.socketio:
            try:
                self.socketio.emit('gas_update', {
                    'ppm': ppm,
                    'timestamp': timestamp
                }, room='parking-updates')
                logger.info(f"Socket.IO: gas_update {ppm} ppm")
            except Exception as e:
                logger.error(f"Error Socket.IO gas: {e}")
        
        logger.info(f"Gas: {ppm} ppm")
    
    def _procesar_rfid(self, payload):
        """
        Procesar lectura RFID
        Payload: {"type": "rfid", "card_id": "ABC123", "timestamp": "..."}
        """
        card_id = payload.get('card_id')
        timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
        
        if not card_id:
            logger.warning(f"Card ID no definido en payload: {payload}")
            return
        
        # Buscar usuario con esta tarjeta
        usuario = self.db.users.find_one({'rfid_card': card_id})
        
        if usuario:
            # Crear evento de lectura exitosa
            self.db.events.insert_one({
                'event_type': 'rfid_read',
                'user_id': str(usuario.get('_id')),
                'user_name': usuario.get('name'),
                'rfid_card': card_id,
                'access_granted': True,
                'timestamp': timestamp,
                'description': f"RFID leída: {usuario.get('name')}"
            })
            logger.info(f"RFID válida: {usuario.get('name')}")
        else:
            # Crear evento de acceso denegado
            self.db.suspicious_activity.insert_one({
                'type': 'rfid_read_denied',
                'rfid_card': card_id,
                'timestamp': timestamp,
                'description': f"Intento con tarjeta no autorizada: {card_id}"
            })
            logger.warning(f"RFID desconocida: {card_id}")
        
        # Emitir Socket.IO
        if self.socketio:
            try:
                self.socketio.emit('rfid_event', {
                    'card_id': card_id,
                    'authorized': bool(usuario),
                    'user_name': usuario.get('name') if usuario else 'Desconocido',
                    'timestamp': timestamp
                }, room='parking-updates')
                logger.info(f"Socket.IO: rfid_event")
            except Exception as e:
                logger.error(f"Error Socket.IO rfid: {e}")

    def _procesar_emergency(self, payload):
        """
        Procesar activación de emergencia (para todo el parqueo)
        Payload: {"type": "emergency", "timestamp": "..."}
        """
        timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
        
        # Registrar evento de emergencia
        self.db.events.insert_one({
            'event_type': 'emergency_alert',
            'timestamp': timestamp,
            'description': 'Alerta de emergencia activada en todo el parqueo',
            'is_active': True
        })
        
        # Emitir Socket.IO
        if self.socketio:
            try:
                self.socketio.emit('emergency_alert', {
                    'alert_type': 'system',
                    'timestamp': timestamp,
                    'is_active': True
                }, room='parking-updates')
                logger.info(f"Socket.IO: emergency_alert")
            except Exception as e:
                logger.error(f"Error Socket.IO emergencia: {e}")
        
        logger.warning(f"EMERGENCIA ACTIVADA EN TODO EL PARQUEO")
    
    def _procesar_ventilador(self, payload):
        """
        Procesar estado del ventilador
        Payload: {"type": "ventilator", "is_active": true, "gas_level": 150, "timestamp": "..."}
        """
        is_active = payload.get('is_active', False)
        gas_level = payload.get('gas_level')
        timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
        
        # Actualizar estadísticas
        self.db.statistics.insert_one({
            'type': 'ventilator_status',
            'is_active': is_active,
            'gas_level': gas_level,
            'timestamp': timestamp
        })
        
        # Emitir Socket.IO
        if self.socketio:
            try:
                self.socketio.emit('ventilator_update', {
                    'is_active': is_active,
                    'gas_level': gas_level,
                    'timestamp': timestamp
                }, room='parking-updates')
                logger.info(f"Socket.IO: ventilator_update")
            except Exception as e:
                logger.error(f"Error Socket.IO ventilador: {e}")
        
        logger.info(f"Ventilador: {'Encendido' if is_active else 'Apagado'}")
    
    def desconectar(self):
        """Desconectar de MQTT y MongoDB"""
        self.corriendo = False
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT desconectado")
        
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("MongoDB desconectado")
        
        logger.info("Consumer MQTT detenido")


def iniciar_consumer_mqtt(app, socketio):
    """
    Iniciar Consumer MQTT en segundo plano (para usar desde Flask)
    
    Args:
        app: Aplicación Flask
        socketio: Instancia SocketIO
    """
    consumer = ConsumerMQTT(
        mqtt_broker=app.config.get('MQTT_BROKER', MQTT_BROKER),
        mqtt_port=app.config.get('MQTT_PORT', MQTT_PORT),
        mongo_uri=app.config.get('MONGO_URI', MONGO_URI),
        socketio=socketio
    )
    
    try:
        consumer.conectar()
    except Exception as e:
        logger.error(f"No se pudo iniciar Consumer MQTT: {e}")
        logger.warning("El Backend funcionará, pero sin eventos en tiempo real")
    
    return consumer


def main():
    """Ejecutar Consumer MQTT de forma independiente"""
    logger.info("="*60)
    logger.info("Park-Guard 2.0 - Consumer MQTT")
    logger.info("="*60)
    logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"MongoDB: {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}")
    logger.info("="*60)
    
    consumer = ConsumerMQTT(MQTT_BROKER, MQTT_PORT, MONGO_URI)
    
    try:
        consumer.conectar()
        print("\n Consumer MQTT escuchando eventos...\n")
        while consumer.corriendo:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n Deteniendo Consumer MQTT...")
        consumer.desconectar()
    except Exception as e:
        logger.error(f"Error: {e}")
        consumer.desconectar()


if __name__ == '__main__':
    main()
