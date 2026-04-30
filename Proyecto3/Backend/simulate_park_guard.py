#!/usr/bin/env python3
"""
Script de Simulación Park-Guard 2.0
Publica eventos MQTT simulados y verifica que lleguen a MongoDB y Grafana
"""
import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime
from pymongo import MongoClient
import os
from datetime import timezone

MQTT_BROKER = os.getenv('MQTT_BROKER', 'mosquitto')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))

MONGO_HOST = os.getenv('MONGO_HOST', 'mongodb')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USER = os.getenv('MONGO_USER', 'park_user')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'park_password')
MONGO_DB = os.getenv('MONGO_DB', 'park_guard')
METRICS_URL = os.getenv('METRICS_URL', 'http://localhost:8080/metrics')

def utc_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

class ParkGuardSimulator:
    def __init__(self):
        self.client = mqtt.Client()
        self.mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
    
    def get_active_rfid_card(self):
        """Obtener una tarjeta RFID válida para simular acceso autorizado."""
        try:
            client = MongoClient(self.mongo_uri)
            db = client[MONGO_DB]
            user = db.users.find_one(
                {"is_active": True, "balance": {"$gte": 1}, "rfid_card": {"$exists": True, "$ne": ""}},
                {"rfid_card": 1}
            )
            client.close()
            return user.get("rfid_card") if user else None
        except Exception:
            return None

    def ensure_test_user_for_authorized(self):
        """Crear/actualizar usuario de prueba para forzar accesos autorizados."""
        try:
            client = MongoClient(self.mongo_uri)
            db = client[MONGO_DB]
            db.users.update_one(
                {"rfid_card": "SIM-ACCESS-OK"},
                {
                    "$set": {
                        "name": "Sim User",
                        "email": "sim.user@parkguard.local",
                        "rfid_card": "SIM-ACCESS-OK",
                        "is_active": True,
                        "balance": 50,
                        "updated_at": datetime.now(timezone.utc)
                    },
                    "$setOnInsert": {
                        "access_count": 0,
                        "created_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            client.close()
            return "SIM-ACCESS-OK"
        except Exception:
            return None
        
    def connect_mqtt(self):
        """Conectar al broker MQTT"""
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print(f"✓ Conectado a MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
            return True
        except Exception as e:
            print(f"✗ Error conectando a MQTT: {e}")
            return False
    
    def publish(self, topic, payload):
        """Publicar mensaje MQTT"""
        result = self.client.publish(topic, json.dumps(payload))
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"  → Published to {topic}: {json.dumps(payload)[:80]}...")
            return True
        else:
            print(f"  ✗ Error publishing to {topic}")
            return False
    
    def simulate_parking_status(self):
        """Simular estado de espacios de parqueo"""
        occupied_target = random.randint(0, 5)
        occupied_spaces = set(random.sample(range(1, 6), occupied_target))
        for space in range(1, 6):
            is_occupied = space in occupied_spaces
            payload = {
                "space": space,
                "is_occupied": is_occupied,
                "timestamp": utc_iso()
            }
            self.publish(f"park-guard/parking/{space}/status", payload)
        print()
    
    def simulate_rfid_read(self):
        """Simular lectura de tarjeta RFID"""
        rfid_cards = [
            "A1B2C3D4E5F6",
            "1234567890AB",
            "ABCD12345678",
            "FAKE12345678"
        ]
        valid_card = self.get_active_rfid_card()
        card = valid_card if valid_card else random.choice(rfid_cards)
        payload = {
            "card_id": card,
            "timestamp": utc_iso()
        }
        self.publish("park-guard/rfid/read", payload)
        print()
    
    def simulate_rfid_authorized(self, count=2):
        """Forzar eventos de acceso autorizado si existe tarjeta activa."""
        valid_card = self.get_active_rfid_card()
        if not valid_card:
            valid_card = self.ensure_test_user_for_authorized()
        if not valid_card:
            print("  ⚠ No se pudo preparar tarjeta para acceso autorizado.")
            return
        for _ in range(count):
            payload = {
                "card_id": valid_card,
                "timestamp": utc_iso()
            }
            self.publish("park-guard/rfid/read", payload)
            time.sleep(0.5)
        print()
    
    def simulate_gas_sensor(self):
        """Simular sensor de gas"""
        ppm = random.randint(100, 800)
        status = "normal" if ppm < 400 else "warning" if ppm < 600 else "critical"
        payload = {
            "ppm": ppm,
            "status": status,
            "timestamp": utc_iso()
        }
        self.publish("park-guard/gas/sensor", payload)
        print()
    
    def simulate_emergency(self):
        """Simular activación de emergencia"""
        payload = {
            "triggered": True,
            "reason": "Prueba de emergencia",
            "timestamp": utc_iso()
        }
        self.publish("park-guard/emergency/trigger", payload)
        print()
    
    def simulate_ventilator(self):
        """Simular control de ventilador"""
        payload = {
            "command": random.choice(["activate", "deactivate"]),
            "timestamp": utc_iso()
        }
        self.publish("park-guard/ventilator/command", payload)
        print()
    
    def simulate_door_status(self):
        """Simular apertura y cierre de talanqueras"""
        for door in ["entrance", "exit"]:
            payload_open = {
                "door": door,
                "is_open": True,
                "timestamp": utc_iso()
            }
            self.publish(f"park-guard/doors/{door}/status", payload_open)
            time.sleep(0.4)
            payload_close = {
                "door": door,
                "is_open": False,
                "timestamp": utc_iso()
            }
            self.publish(f"park-guard/doors/{door}/status", payload_close)
        print()
    
    def check_mongodb(self):
        """Verificar datos en MongoDB"""
        try:
            client = MongoClient(self.mongo_uri)
            db = client[MONGO_DB]
            
            print("\n=== VERIFICACIÓN EN MONGODB ===")
            
            events_count = db.events.count_documents({})
            print(f"📊 Total de eventos en colección 'events': {events_count}")
            
            spaces_count = db.parking_spaces.count_documents({})
            print(f"📊 Total de espacios en colección 'parking_spaces': {spaces_count}")
            
            recent_events = list(db.events.find().sort('timestamp', -1).limit(5))
            print(f"\n📋 Últimos 5 eventos:")
            for e in recent_events:
                print(f"  - {e.get('event_type', 'N/A')} | {e.get('timestamp', 'N/A')}")
            
            return True
        except Exception as e:
            print(f"✗ Error verificando MongoDB: {e}")
            return False
    
    def check_metrics_api(self):
        """Verificar el endpoint de métricas"""
        import requests
        try:
            response = requests.get(METRICS_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"\n=== VERIFICACIÓN API MÉTRICAS ===")
                print(f"✓ API responding: {data.get('parking', {}).get('total_spaces', 0)} spaces")
                print(f"  Occupied: {data.get('parking', {}).get('occupied_spaces', 0)}")
                print(f"  Events today: {data.get('events', {})}")
                return True
            else:
                print(f"✗ API returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error verificando API métricas: {e}")
            return False
    
    def run_full_simulation(self):
        """Ejecutar simulación completa"""
        print("\n" + "="*60)
        print("🅿️  PARK-GUARD 2.0 - SIMULADOR DE PRUEBAS")
        print("="*60)
        
        if not self.connect_mqtt():
            return
        
        print("\n--- ENVIANDO EVENTOS SIMULADOS ---\n")
        
        print("1️⃣  Simulando estado de espacios de parqueo...")
        self.simulate_parking_status()
        time.sleep(1)
        
        print("2️⃣  Simulando lectura RFID...")
        self.simulate_rfid_read()
        time.sleep(1)

        print("2️⃣.1 Simulando accesos autorizados (x2)...")
        self.simulate_rfid_authorized(count=2)
        time.sleep(1)
        
        print("3️⃣  Simulando sensor de gas...")
        self.simulate_gas_sensor()
        time.sleep(1)
        
        print("4️⃣  Simulando activación de emergencia (x2)...")
        self.simulate_emergency()
        time.sleep(1)
        self.simulate_emergency()
        time.sleep(1)
        
        print("5️⃣  Simulando control de ventilador...")
        self.simulate_ventilator()
        time.sleep(1)
        
        print("6️⃣  Simulando estado de puertas...")
        self.simulate_door_status()
        
        self.client.disconnect()
        
        print("\n--- VERIFICANDO RESULTADOS ---\n")
        
        time.sleep(2)
        self.check_mongodb()
        
        print("\n")
        self.check_metrics_api()
        
        print("\n" + "="*60)
        print("✅ SIMULACIÓN COMPLETADA")
        print("="*60)
        print("\n📝 Resumen:")
        print("  - Eventos MQTT enviados al broker")
        print("  - Verifica MongoDB para datos persistidos")
        print("  - Verifica Grafana para visualización")
        print("\n🌐 Accesos:")
        print(f"  - Grafana: http://192.168.0.6:3001")
        print(f"  - Backend API: http://192.168.0.6:5000")
        print(f"  - Metrics API: http://192.168.0.6:8080/metrics")

if __name__ == "__main__":
    simulator = ParkGuardSimulator()
    simulator.run_full_simulation()
