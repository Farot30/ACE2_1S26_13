import json
import os
import time
import serial
import paho.mqtt.client as mqtt

def cargar_env(path):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            clave = clave.strip()
            valor = valor.strip().strip("\"'")
            if clave and clave not in os.environ:
                os.environ[clave] = valor


def obtener_entero(clave, default):
    valor = os.environ.get(clave)
    if valor is None:
        return default
    try:
        return int(valor)
    except ValueError:
        return default


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cargar_env(os.path.join(BASE_DIR, ".env"))

# Arduino
PUERTO_SERIAL = os.environ.get("PUERTO_SERIAL", "/dev/ttyACM0")
BAUDRATE_SERIAL = obtener_entero("BAUDRATE_SERIAL", 115200)

# IP del broker MQTT
BROKER_MQTT = os.environ.get("BROKER_MQTT", "52.14.176.227")
PUERTO_MQTT = obtener_entero("PUERTO_MQTT", 1883)
KEEPALIVE_MQTT = obtener_entero("KEEPALIVE_MQTT", 60)

# Topics esperados por el backend (consumer_mqtt.py)
TOPICO_PARQUEO = "park-guard/parking/{space}/status"
TOPICO_GAS = "park-guard/gas/sensor"
TOPICO_RFID = "park-guard/rfid/read"
TOPICO_EMERGENCIA = "park-guard/emergency/trigger"
TOPICO_VENTILADOR = "park-guard/ventilator/command"
TOPICO_EVENTOS = "park-guard/events"

# Topics de comandos publicados por el backend
TOPICOS_COMANDOS = [
    "park-guard/commands/fan",
    "park-guard/commands/emergency",
    "park-guard/commands/door/entrance",
    "park-guard/commands/door/exit",
    "park-guard/commands/access",
    "/park-guard/commands/fan",
    "/park-guard/commands/emergency",
    "/park-guard/commands/door/entrance",
    "/park-guard/commands/door/exit",
    "/park-guard/commands/access",
]


def a_booleano(valor):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return valor != 0
    if isinstance(valor, str):
        return valor.strip().lower() in ("1", "true", "si", "yes", "on")
    return False


def publicar_json(cliente, topico, payload):
    cliente.publish(topico, json.dumps(payload), qos=1)


def procesar_sensor(payload, cliente, estado):
    marca_tiempo = payload.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    espacios = payload.get("spaces", [])
    ultimo_sensor = estado.setdefault("ultimo_sensor", {})

    for indice, valor in enumerate(espacios, start=1):
        ocupado = a_booleano(valor)
        clave = f"space_{indice}"
        if ultimo_sensor.get(clave) != ocupado:
            publicar_json(cliente, TOPICO_PARQUEO.format(space=indice), {
                "type": "parking",
                "space": indice,
                "is_occupied": ocupado,
                "timestamp": marca_tiempo,
            })
            ultimo_sensor[clave] = ocupado

    gas = payload.get("gas")
    if gas is not None:
        if ultimo_sensor.get("gas") != gas:
            publicar_json(cliente, TOPICO_GAS, {
                "type": "gas",
                "ppm": gas,
                "timestamp": marca_tiempo,
            })
            ultimo_sensor["gas"] = gas

    ventilador = payload.get("fan")
    if ventilador is not None:
        ventilador_activo = a_booleano(ventilador)
        if ultimo_sensor.get("fan") != ventilador_activo:
            publicar_json(cliente, TOPICO_VENTILADOR, {
                "type": "ventilator",
                "is_active": ventilador_activo,
                "gas_level": gas,
                "timestamp": marca_tiempo,
            })
            ultimo_sensor["fan"] = ventilador_activo

    emergencia = payload.get("emergency")
    if emergencia is not None:
        activa = a_booleano(emergencia)
        if estado.get("emergencia") != activa:
            publicar_json(cliente, TOPICO_EMERGENCIA, {
                "type": "emergency",
                "is_active": activa,
                "timestamp": marca_tiempo,
            })
        estado["emergencia"] = activa


def procesar_rfid(payload, cliente):
    uid = payload.get("uid") or payload.get("card_id")
    if not uid:
        print(f"RFID sin uid: {payload}")
        return

    publicar_json(cliente, TOPICO_RFID, {
        "type": "rfid",
        "card_id": uid,
        "timestamp": payload.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    })


def procesar_evento(payload, cliente):
    evento = dict(payload)
    evento["type"] = "event"
    if "timestamp" not in evento:
        evento["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    publicar_json(cliente, TOPICO_EVENTOS, evento)
    print(f"Evento Arduino publicado MQTT: {evento}")


def al_conectar(cliente, userdata, flags, rc):
    if rc != 0:
        print(f"Error al conectar MQTT: {rc}")
        return

    for topico in TOPICOS_COMANDOS:
        cliente.subscribe(topico, qos=1)
    print("Suscrito a comandos MQTT")


def al_mensaje(cliente, userdata, msg):
    conexion_serial = userdata.get("conexion_serial")
    if not conexion_serial:
        return

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        print(f"Comando MQTT invalido: {msg.payload}")
        return

    comando = payload.get("command")
    if payload.get("cmd"):
        mensaje = payload
    elif "commands/fan" in msg.topic and comando:
        mensaje = {
            "cmd": "fan",
            "state": comando == "activate_fan",
        }
    elif "commands/emergency" in msg.topic and comando:
        mensaje = {
            "cmd": "emergency",
            "state": comando == "activate_emergency",
        }
    elif "commands/door/entrance" in msg.topic and comando:
        accion = "open" if comando == "open_door" else "close"
        mensaje = {
            "cmd": "door",
            "door": "entrance",
            "action": accion,
        }
    elif "commands/door/exit" in msg.topic and comando:
        accion = "open" if comando == "open_door" else "close"
        mensaje = {
            "cmd": "door",
            "door": "exit",
            "action": accion,
        }
    else:
        mensaje = payload

    # Arduino parsea por coincidencia de strings; sin espacios evita falsos negativos.
    conexion_serial.write((json.dumps(mensaje, separators=(",", ":")) + "\n").encode("utf-8"))
    print(f"Comando MQTT recibido {msg.topic}: {mensaje}")


def principal():
    conexion_serial = serial.Serial(PUERTO_SERIAL, BAUDRATE_SERIAL, timeout=1)
    cliente_mqtt = mqtt.Client()
    cliente_mqtt.user_data_set({"conexion_serial": conexion_serial})
    cliente_mqtt.on_connect = al_conectar
    cliente_mqtt.on_message = al_mensaje
    cliente_mqtt.connect(BROKER_MQTT, PUERTO_MQTT, KEEPALIVE_MQTT)
    cliente_mqtt.loop_start()
    estado = {"emergencia": None}

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

            tipo_mensaje = payload.get("type")
            if tipo_mensaje == "sensor":
                procesar_sensor(payload, cliente_mqtt, estado)
            elif tipo_mensaje == "rfid":
                procesar_rfid(payload, cliente_mqtt)
            elif tipo_mensaje == "event":
                procesar_evento(payload, cliente_mqtt)
            else:
                print(f"Tipo desconocido: {payload}")

    except KeyboardInterrupt:
        print("Interrupcion del usuario. Cerrando conexion.")
    finally:
        cliente_mqtt.loop_stop()
        cliente_mqtt.disconnect()
        conexion_serial.close()


if __name__ == "__main__":
    principal()