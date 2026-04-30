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
    'doors':     'park-guard/doors/+/status',
    'events':    'park-guard/events',
    "viv":       'park-guard/viv/vehiculos',
}

COBRO_POR_INGRESO = 1.0

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
            elif topic == 'park-guard/events':
                accion = payload.get('action')
                if accion in ('emergency_on', 'emergency_off'):
                    self._procesar_emergency({
                        'type': 'emergency',
                        'is_active': accion == 'emergency_on',
                        'timestamp': payload.get('timestamp', datetime.utcnow().isoformat())
                    })
                elif accion == 'door_update':
                    self._procesar_puerta({
                        'type': 'door_update',
                        'door': payload.get('door'),
                        'is_open': payload.get('is_open', False),
                        'timestamp': payload.get('timestamp', datetime.utcnow().isoformat())
                    })
            elif 'doors' in topic or 'door_update' in topic:
                self._procesar_puerta(payload)
            elif 'viv' in topic:
                self._procesar_viv(payload)
            
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
        try:
            space_number = int(payload.get('space'))
        except (TypeError, ValueError):
            space_number = None
        is_occupied = payload.get('is_occupied', False)
        timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
        
        if space_number is None:
            logger.warning(f"Space number no definido en payload: {payload}")
            return
        if space_number < 1 or space_number > 5:
            logger.warning(f"Space number fuera de rango (1-5): {space_number}")
            return
        
        # Actualizar en MongoDB (siempre, para histórico y Grafana)
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
        
        # Guardar estadística en MongoDB (siempre, para Grafana)
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

    def _procesar_viv(self, payload):
        """
        Procesar detección VIV - SOLO ENTRADA
        Payload esperado:
        {
            "event_type": "viv_vehicle_detected",
            "source": "viv",
            "vehicle_type": "car" | "motorcycle" | "truck",
            "plate_text": "JNU540",
            "fee_quetzales": 10.0,
            "timestamp": "2026-04-28T02:00:09.266052+00:00"
        }
        """
        try:
            # Extraer datos del payload
            event_type = payload.get('event_type')
            source = payload.get('source', 'viv')
            vehicle_type = payload.get('vehicle_type')
            plate_text = payload.get('plate_text')
            fee_quetzales = payload.get('fee_quetzales', 0.0)
            timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
            
            # Validar datos esenciales
            if not plate_text:
                logger.warning(f"Placa no definida en payload VIV: {payload}")
                return
            
            if not vehicle_type:
                logger.warning(f"Tipo de vehículo no definido en payload VIV: {payload}")
                return
            
            # Convertir timestamp
            try:
                timestamp_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp_obj = datetime.utcnow()
            
            # Verificar que no haya entrada reciente (últimos 5 minutos) del mismo vehículo
            from datetime import timedelta
            hace_5_minutos = timestamp_obj - timedelta(minutes=5)
            
            entrada_reciente = self.db.registros_entrada_salida.find_one({
                'plate_text': plate_text,
                'timestamp_entrada': {'$gte': hace_5_minutos},
                'tipo': 'entrada',
                'timestamp_salida': None  # Aún sin salida
            })
            
            if entrada_reciente:
                logger.warning(f"⚠ VIV: Placa {plate_text} ya registrada recientemente, omitiendo duplicado")
                return
            
            # CREAR REGISTRO DE ENTRADA
            registro_entrada = {
                'plate_text': plate_text,
                'vehicle_type': vehicle_type,
                'timestamp_entrada': timestamp_obj,
                'timestamp_salida': None,
                'tarifa_por_hora': fee_quetzales,
                'tarifa_cobrada': None,
                'tiempo_estacionado_minutos': None,
                'tipo': 'entrada',  # VIV solo es entrada
                'source': 'viv',
                'usuario_id': None,  # VIV no requiere usuario
                'metodo_deteccion': 'vision',
                'estado': 'activo'
            }
            
            result = self.db.registros_entrada_salida.insert_one(registro_entrada)
            logger.info(f"✓ ENTRADA VIV: {vehicle_type.upper()} - Placa: {plate_text} - Tarifa: Q{fee_quetzales:.2f}")
            
            # Guardar también en registros_viv (histórico específico)
            self.db.registros_viv.insert_one({
                'event_type': event_type,
                'source': source,
                'vehicle_type': vehicle_type,
                'plate_text': plate_text,
                'fee_quetzales': fee_quetzales,
                'timestamp': timestamp_obj,
                'registro_entrada_salida_id': result.inserted_id,
                'procesado': True
            })
            
            # Guardar evento general
            self.db.events.insert_one({
                'event_type': 'entrada_viv',
                'vehicle_type': vehicle_type,
                'plate_text': plate_text,
                'timestamp': timestamp_obj,
                'tarifa_por_hora': fee_quetzales,
                'description': f"Entrada VIV: {vehicle_type} ({plate_text})",
                'source': 'viv'
            })
            
            # Socket.IO
            if self.socketio:
                try:
                    self.socketio.emit('viv_entrada', {
                        'vehicle_type': vehicle_type,
                        'plate_text': plate_text,
                        'tarifa_por_hora': fee_quetzales,
                        'timestamp': timestamp,
                        'source': source
                    }, broadcast=True)
                    logger.info(f"Socket.IO: viv_entrada emitido")
                except Exception as e:
                    logger.error(f"Error emitiendo Socket.IO VIV: {e}")
                
        except Exception as e:
            logger.error(f"Error procesando VIV: {e}", exc_info=True)
    
    def _procesar_rfid(self, payload):
        """
        Procesar lectura RFID
        Payload: {"card_id": "ABC123", "timestamp": "..."}
        """
        card_id = payload.get('card_id')
        timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
        
        if not card_id:
            logger.warning(f"Card ID no definido en payload RFID: {payload}")
            return
        
        try:
            # 1. BUSCAR USUARIO por tarjeta RFID en la colección 'users'
            usuario = self.db.users.find_one({'rfid_card': card_id.upper()})
            
            access_granted = False
            user_name = "Desconocido"
            
            if usuario:
                user_name = usuario.get('name', 'Usuario')
                # 2. VALIDAR si el usuario está activo y tiene saldo
                if usuario.get('is_active', False) and usuario.get('balance', 0) >= COBRO_POR_INGRESO:
                    access_granted = True
                    # Descontar saldo y aumentar contador
                    self.db.users.update_one(
                        {'_id': usuario['_id']},
                        {
                            '$inc': {'balance': -COBRO_POR_INGRESO, 'access_count': 1},
                            '$set': {'last_access': datetime.utcnow()}
                        }
                    )
                    logger.info(f"✓ ACCESO CONCEDIDO: {user_name} ({card_id})")
                else:
                    razon = "Inactivo" if not usuario.get('is_active') else "Saldo insuficiente"
                    logger.warning(f"❌ ACCESO DENEGADO ({razon}): {user_name} ({card_id})")
            else:
                logger.warning(f"❌ RFID NO REGISTRADO: {card_id}")

            # 3. PUBLICAR COMANDO DE ACCESO AL HARDWARE (Inmediato)
            self._publicar_comando_acceso(access_granted, card_id, timestamp, user_name)
            
            # 4. REGISTRAR EVENTO EN BD
            self.db.events.insert_one({
                'event_type': 'access_granted' if access_granted else 'access_denied',
                'rfid_card': card_id,
                'user_id': usuario['_id'] if usuario else None,
                'user_name': user_name,
                'timestamp': datetime.utcnow(),
                'description': f"{'Acceso concedido' if access_granted else 'Acceso denegado'} a {user_name}",
                'data': {'rfid_card': card_id}
            })

            # 5. DETECTAR ACTIVIDAD SOSPECHOSA (Si el acceso fue denegado)
            if not access_granted:
                self._detectar_actividad_sospechosa(card_id)

            # 6. EMITIR POR SOCKET.IO
            if self.socketio:
                self.socketio.emit('rfid_read', {
                    'card_id': card_id,
                    'user_name': user_name,
                    'granted': access_granted,
                    'timestamp': timestamp
                }, broadcast=True)

        except Exception as e:
            logger.error(f"Error procesando RFID: {e}", exc_info=True)
    
    def _detectar_actividad_sospechosa(self, card_id):
        """
        Lógica inteligente para detectar múltiples intentos fallidos
        """
        try:
            from datetime import timedelta
            hace_5_minutos = datetime.utcnow() - timedelta(minutes=5)
            
            # Contar intentos fallidos en la colección de eventos
            intentos_fallidos = self.db.events.count_documents({
                'event_type': 'access_denied',
                'rfid_card': card_id,
                'timestamp': {'$gte': hace_5_minutos}
            })
            
            if intentos_fallidos >= 3:
                logger.warning(f"🚨 ALERTA: Actividad sospechosa detectada para tarjeta {card_id} ({intentos_fallidos} intentos)")
                
                # Registrar en la colección 'suspicious_activity'
                self.db.suspicious_activity.insert_one({
                    'activity_type': 'multiple_failed_attempts',
                    'rfid_card': card_id,
                    'severity': 'high' if intentos_fallidos >= 5 else 'medium',
                    'details': {
                        'failed_attempts': intentos_fallidos,
                        'time_window': '5 minutes'
                    },
                    'timestamp': datetime.utcnow(),
                    'resolved': False
                })
                
                # Emitir alerta por Socket.IO para el Frontend
                if self.socketio:
                    self.socketio.emit('suspicious_alert', {
                        'title': 'Intrusión detectada',
                        'message': f'La tarjeta {card_id} ha intentado ingresar {intentos_fallidos} veces sin éxito.',
                        'severity': 'high'
                    }, room='parking-updates')
                    
        except Exception as e:
            logger.error(f"Error detectando actividad sospechosa: {e}")
    
    def _publicar_comando_acceso(self, access_granted, card_id, timestamp, user_name=None):
        """
        Publicar comando de acceso al Arduino a través de MQTT
        Este comando hace que el Arduino abra la talanquera o muestre denegado
        CRÍTICO: Se llama INMEDIATAMENTE después de validar en BD, antes de inserciones
        
        Args:
            access_granted: bool - Si el acceso fue concedido
            card_id: str - ID de la tarjeta RFID
            timestamp: str - Timestamp del evento
        """
        try:
            if self.mqtt_client is None:
                logger.error("ERROR CRÍTICO: mqtt_client es None, no se puede publicar comando de acceso")
                return
            
            # El Arduino espera recibir este comando en el serial via MqttArduino.py
            comando = {
                "cmd": "access",
                "granted": access_granted,
                "card_id": card_id,
                "timestamp": timestamp,
                "user_name": user_name or "Desconocido"
            }
            
            # Publicar en topic de comandos para que MqttArduino.py lo traduzca al Arduino
            topic = "park-guard/commands/access"
            self.mqtt_client.publish(topic, json.dumps(comando), qos=1)
            
            estado = "concedido" if access_granted else "denegado"
            logger.info(f"⚡ COMANDO DE ACCESO PUBLICADO (RÁPIDO): {estado} para {card_id}")
        except Exception as e:
            logger.error(f"ERROR al publicar comando de acceso: {e}")

    def _procesar_emergency(self, payload):
        """
        Procesar activación de emergencia (para todo el parqueo)
        Payload: {"type": "emergency", "timestamp": "..."}
        """
        timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
        is_active = bool(payload.get('is_active', True))
        descripcion = 'Alerta de emergencia activada en todo el parqueo' if is_active else 'Alerta de emergencia desactivada'
        event_type = 'emergency_alert' if is_active else 'emergency_cleared'
        
        # Registrar evento de emergencia (siempre, para Grafana)
        self.db.events.insert_one({
            'event_type': event_type,
            'timestamp': timestamp,
            'description': descripcion,
            'is_active': is_active
        })
        
        # Emitir Socket.IO
        if self.socketio:
            try:
                self.socketio.emit('emergency_alert', {
                    'alert_type': 'system',
                    'timestamp': timestamp,
                    'is_active': is_active
                }, room='parking-updates')
                logger.info(f"Socket.IO: emergency_alert")
            except Exception as e:
                logger.error(f"Error Socket.IO emergencia: {e}")
        
        if is_active:
            logger.warning("EMERGENCIA ACTIVADA EN TODO EL PARQUEO")
        else:
            logger.info("EMERGENCIA DESACTIVADA")
    
    def _procesar_ventilador(self, payload):
        """
        Procesar estado del ventilador
        Payload: {"type": "ventilator", "is_active": true, "gas_level": 150, "timestamp": "..."}
        """
        is_active = payload.get('is_active', False)
        gas_level = payload.get('gas_level')
        timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
        
        # Actualizar estadísticas
        if not self.socketio:
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
    
    def _procesar_puerta(self, payload):
        """
        Procesar estado de talanqueras (puertas entrada/salida)
        Payload: {"type": "door_update", "door": "entrance", "is_open": true, "timestamp": "..."}
        """
        door = payload.get('door')  # 'entrance' o 'exit'
        is_open = payload.get('is_open', False)
        timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
        
        if not door:
            logger.warning(f"Door no definido en payload: {payload}")
            return
        
        # Guardar evento de puerta en MongoDB (siempre, para Grafana)
        self.db.events.insert_one({
            'event_type': 'door_update',
            'door': door,
            'is_open': is_open,
            'description': f"Talanquera {door} {'abierta' if is_open else 'cerrada'}",
            'timestamp': datetime.utcnow(),
            'resolved': False
        })
        
        # Emitir Socket.IO
        if self.socketio:
            try:
                self.socketio.emit('door_update', {
                    'door': door,
                    'is_open': is_open,
                    'timestamp': timestamp
                }, room='parking-updates')
                logger.info(f"Socket.IO: door_update {door}")
            except Exception as e:
                logger.error(f"Error Socket.IO puerta: {e}")
        
        logger.info(f"Talanquera {door}: {'Abierta' if is_open else 'Cerrada'}")
    
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
