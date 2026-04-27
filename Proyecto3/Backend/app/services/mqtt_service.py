"""Servicio para comunicación MQTT"""
import paho.mqtt.client as mqtt
from flask import current_app
import json
import threading

class MQTTService:
    """Servicio para comunicación con broker MQTT"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MQTTService, cls).__new__(cls)
        return cls._instance
    
    def connect(self):
        """Conectar al broker MQTT"""
        try:
            self._client = mqtt.Client()
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            
            broker = current_app.config.get('MQTT_BROKER', 'localhost')
            port = current_app.config.get('MQTT_PORT', 1883)
            
            self._client.connect(broker, port, keepalive=60)
            self._client.loop_start()
            
            print(f"✓ Conectado a MQTT broker: {broker}:{port}")
        except Exception as e:
            print(f"✗ Error conectando a MQTT: {str(e)}")
    
    def disconnect(self):
        """Desconectar del broker MQTT"""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            print("✓ Desconectado de MQTT broker")
    
    def publish(self, topic, payload, qos=1):
        """
        Publicar mensaje MQTT
        
        Args:
            topic: Tópico MQTT
            payload: Mensaje (será convertido a JSON si es diccionario)
            qos: Quality of Service (0, 1, 2)
        """
        if self._client is None:
            raise Exception("MQTT client no inicializado")
        
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        elif not isinstance(payload, str):
            payload = str(payload)
        
        try:
            self._client.publish(topic, payload, qos=qos)
            print(f"✓ Publicado en {topic}: {payload}")
        except Exception as e:
            print(f"✗ Error publicando en MQTT: {str(e)}")
    
    def subscribe(self, topic, qos=1):
        """
        Suscribirse a un tópico MQTT
        
        Args:
            topic: Tópico a suscribirse
            qos: Quality of Service
        """
        if self._client is None:
            raise Exception("MQTT client no inicializado")
        
        try:
            self._client.subscribe(topic, qos=qos)
            print(f"✓ Suscrito a: {topic}")
        except Exception as e:
            print(f"✗ Error suscribiéndose a MQTT: {str(e)}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        if rc == 0:
            print("✓ MQTT broker conectado")
        else:
            print(f"✗ MQTT error de conexión: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta del broker"""
        if rc != 0:
            print(f"✗ Desconexión inesperada de MQTT: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback cuando se recibe un mensaje"""
        print(f"Mensaje recibido en {msg.topic}: {msg.payload.decode()}")
