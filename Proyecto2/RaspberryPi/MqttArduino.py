import json
import time
import serial
import paho.mqtt.client as mqtt

#Arduino
PUERTO_SERIAL = "/dev/ttyACM0"
BAUDRATE_SERIAL = 9600

# IP de ejemplo del broker MQTT cambiar
BROKER_MQTT = "192.168.1.100"
PUERTO_MQTT = 1883
KEEPALIVE_MQTT = 60

#Define a qué "canal" MQTT se envía cada tipo de mensaje
MAPA_TOPICS = {
    "parking": "park-guard/parking/{space}/status",
    "gas": "park-guard/gas/sensor",
    "rfid": "park-guard/rfid/read",
    "emergency": "park-guard/emergency/trigger",
    "ventilator": "park-guard/ventilator/command",
}


def resolver_topic(payload):
    tipo_mensaje = payload.get("type")
    if tipo_mensaje == "parking":
        espacio = payload.get("space")
        if espacio is None:
            return None
        return MAPA_TOPICS["parking"].format(space=espacio)

    return MAPA_TOPICS.get(tipo_mensaje)


def principal():
    conexion_serial = serial.Serial(PUERTO_SERIAL, BAUDRATE_SERIAL, timeout=1)
    cliente_mqtt = mqtt.Client()
    cliente_mqtt.connect(BROKER_MQTT, PUERTO_MQTT, KEEPALIVE_MQTT)
    cliente_mqtt.loop_start()

    try:
        while True:
            linea_cruda = conexion_serial.readline()
            if not linea_cruda:
                time.sleep(0.1)
                continue

            linea = linea_cruda.decode("utf-8").strip()
            if not linea:
                continue

            try:
                payload = json.loads(linea)
            except json.JSONDecodeError:
                print(f"Serial invalido: {linea}")
                continue

            topic = resolver_topic(payload)
            if not topic:
                print(f"Tipo desconocido: {payload}")
                continue

            cliente_mqtt.publish(topic, json.dumps(payload), qos=1)
            print(f"MQTT publicado {topic}: {payload}")

    except KeyboardInterrupt:
        print("Interrupcion del usuario. Cerrando conexion.")
    finally:
        cliente_mqtt.loop_stop()
        cliente_mqtt.disconnect()
        conexion_serial.close()


if __name__ == "__main__":
    principal()