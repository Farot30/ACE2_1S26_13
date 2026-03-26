#!/usr/bin/env python3
import json
import os
import random
import string
import sys
import time
from dataclasses import dataclass

import paho.mqtt.publish as mqtt_publish
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))


@dataclass
class TestResult:
    name: str
    ok: bool
    detail: str = ""


results = []


def add_result(name, ok, detail=""):
    results.append(TestResult(name=name, ok=ok, detail=detail))
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name} - {detail}")


def api(method, path, token=None, body=None, params=None, expected=200):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.request(
        method=method,
        url=f"{BASE_URL}{path}",
        headers=headers,
        json=body,
        params=params,
        timeout=15,
    )

    payload = {}
    try:
        payload = response.json()
    except Exception:
        pass

    if response.status_code != expected:
        raise RuntimeError(
            f"{method} {path} -> esperado {expected}, recibido {response.status_code}, body={payload}"
        )
    return payload


def random_rfid():
    chars = string.hexdigits.upper().replace("A", "A")
    pool = "0123456789ABCDEF"
    return "".join(random.choice(pool) for _ in range(8))


def wait_for(predicate, timeout=8, interval=0.5):
    start = time.time()
    while time.time() - start < timeout:
        if predicate():
            return True
        time.sleep(interval)
    return False


def publish_rfid(card_id):
    payload = {
        "type": "rfid",
        "card_id": card_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    mqtt_publish.single(
        topic="park-guard/rfid/read",
        payload=json.dumps(payload),
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        qos=1,
    )


def get_user_by_id(users, user_id):
    for user in users:
        if user.get("id") == user_id:
            return user
    return None


def main():
    print("== Smoke Test Simulado - Enunciado Park-Guard ==")

    # 1) Health
    try:
        health = api("GET", "/api/health")
        add_result("Backend health", health.get("status") == "OK", str(health))
    except Exception as e:
        add_result("Backend health", False, str(e))
        return 1

    # 2) Registro/Login JWT
    email = f"sim_{int(time.time())}@test.com"
    password = "Test12345"
    name = "Tester Simulado"

    try:
        api("POST", "/api/auth/register", body={"email": email, "name": name, "password": password}, expected=201)
        add_result("Registro admin", True, email)
    except Exception as e:
        add_result("Registro admin", False, str(e))
        return 1

    try:
        login = api("POST", "/api/auth/login", body={"email": email, "password": password}, expected=200)
        token = login.get("data", {}).get("token")
        add_result("Login JWT", bool(token), "token obtenido" if token else "sin token")
        if not token:
            return 1
    except Exception as e:
        add_result("Login JWT", False, str(e))
        return 1

    # 3) Espacios de parqueo + gestión administrativa
    try:
        api("POST", "/api/parking/initialize", token=token, expected=200)
        spaces_payload = api("GET", "/api/parking/spaces", token=token, expected=200)
        spaces = spaces_payload.get("data") or []
        add_result("Inicialización espacios", len(spaces) == 5, f"espacios={len(spaces)}")

        api("PATCH", "/api/parking/spaces/1/disable", token=token, expected=200)
        api("PATCH", "/api/parking/spaces/1/enable", token=token, expected=200)
        add_result("Habilitar/Deshabilitar espacio", True, "espacio 1 OK")
    except Exception as e:
        add_result("Gestión espacios", False, str(e))

    # 4) CRUD usuario + saldo inicial
    test_rfid = random_rfid()
    user_id = None
    try:
        create = api("POST", "/api/users", token=token, body={"name": "Usuario Saldo", "rfid_card": test_rfid}, expected=201)
        user_id = create.get("data", {}).get("user_id")
        users = api("GET", "/api/users", token=token, params={"limit": 500}, expected=200).get("data") or []
        created = get_user_by_id(users, user_id)
        balance = float(created.get("balance", 0)) if created else -1
        add_result("Crear usuario RFID", bool(created), f"id={user_id}")
        add_result("Saldo inicial Q5", abs(balance - 5.0) < 0.001, f"balance={balance}")
    except Exception as e:
        add_result("CRUD usuario/saldo inicial", False, str(e))
        return 1

    # 5) Recargar saldo y reiniciar
    try:
        api("PATCH", f"/api/users/{user_id}/balance", token=token, body={"amount": 20}, expected=200)
        users = api("GET", "/api/users", token=token, params={"limit": 500}, expected=200).get("data") or []
        user = get_user_by_id(users, user_id)
        balance = float(user.get("balance", 0)) if user else -1
        add_result("Recarga saldo", abs(balance - 25.0) < 0.001, f"balance={balance}")

        api("PATCH", f"/api/users/{user_id}/balance/reset", token=token, expected=200)
        users = api("GET", "/api/users", token=token, params={"limit": 500}, expected=200).get("data") or []
        user = get_user_by_id(users, user_id)
        balance = float(user.get("balance", 0)) if user else -1
        add_result("Reinicio saldo Q5", abs(balance - 5.0) < 0.001, f"balance={balance}")
    except Exception as e:
        add_result("Recarga/Reinicio saldo", False, str(e))

    # 6) Simulación RFID por MQTT (cobro Q1)
    try:
        publish_rfid(test_rfid)
        publish_rfid(test_rfid)
        publish_rfid(test_rfid)

        def charged_three():
            users_local = api("GET", "/api/users", token=token, params={"limit": 500}, expected=200).get("data") or []
            user_local = get_user_by_id(users_local, user_id)
            if not user_local:
                return False
            return abs(float(user_local.get("balance", 0)) - 2.0) < 0.001

        ok_charge = wait_for(charged_three, timeout=12)
        add_result("Cobro Q1 por paso RFID", ok_charge, "balance esperado=2")

        granted = api("GET", "/api/events/type/access_granted", token=token, params={"limit": 20}, expected=200).get("data") or []
        granted_for_card = [e for e in granted if (e.get("data") or {}).get("rfid_card") == test_rfid]
        add_result("Evento access_granted", len(granted_for_card) >= 3, f"eventos={len(granted_for_card)}")
    except Exception as e:
        add_result("Simulación cobro RFID", False, str(e))

    # 7) Saldo insuficiente (denegado)
    try:
        api("PATCH", f"/api/users/{user_id}/balance/reset", token=token, expected=200)

        # Dejar en Q1: reset a 100 y luego restar 99 con una actualización negativa no permitida,
        # así que hacemos una forma simple: usar una tarjeta temporal para validar denegado por saldo
        # con usuario nuevo y saldo directo por recarga controlada no disponible a la baja.
        # Alternativa simple: consumir 100 accesos; haremos 2 pasos en usuario nuevo con saldo 1.

        low_rfid = random_rfid()
        low_create = api("POST", "/api/users", token=token, body={"name": "Usuario Bajo", "rfid_card": low_rfid}, expected=201)
        low_id = low_create.get("data", {}).get("user_id")

        # Llevar a Q1 usando reinicio + cobros 99 (rápido en lote)
        for _ in range(99):
            publish_rfid(low_rfid)

        wait_for(lambda: abs(float((get_user_by_id((api("GET", "/api/users", token=token, params={"limit": 500}, expected=200).get("data") or []), low_id) or {}).get("balance", 0)) - 1.0) < 0.001, timeout=18)

        publish_rfid(low_rfid)  # saldo 1 -> 0 (grant)
        publish_rfid(low_rfid)  # saldo 0 -> denied

        def has_denied():
            denied = api("GET", "/api/events/type/access_denied", token=token, params={"limit": 60}, expected=200).get("data") or []
            for event in denied:
                data = event.get("data") or {}
                if data.get("rfid_card") == low_rfid and data.get("reason") == "saldo insuficiente":
                    return True
            return False

        denied_ok = wait_for(has_denied, timeout=12)
        add_result("Denegado por saldo insuficiente", denied_ok, "se detectó reason=saldo insuficiente")
    except Exception as e:
        add_result("Prueba saldo insuficiente", False, str(e))

    # 8) Comandos remotos API (publicación MQTT)
    try:
        api("POST", "/api/commands/fan/activate", token=token, body={}, expected=200)
        api("POST", "/api/commands/fan/deactivate", token=token, body={}, expected=200)
        api("POST", "/api/commands/emergency/activate", token=token, body={}, expected=200)
        api("POST", "/api/commands/emergency/deactivate", token=token, body={}, expected=200)
        api("POST", "/api/commands/door/entrance/open", token=token, body={}, expected=200)
        api("POST", "/api/commands/door/entrance/close", token=token, body={}, expected=200)
        api("POST", "/api/commands/door/exit/open", token=token, body={}, expected=200)
        api("POST", "/api/commands/door/exit/close", token=token, body={}, expected=200)
        add_result("Acciones remotas MQTT", True, "fan/emergency/doors OK")
    except Exception as e:
        add_result("Acciones remotas MQTT", False, str(e))

    # 9) Summary estadístico
    try:
        summary = api("GET", "/api/events/summary", token=token, expected=200).get("data") or {}
        ok = (
            "parking" in summary and
            "events" in summary and
            "users" in summary
        )
        add_result("Resumen estadístico", ok, json.dumps(summary))
    except Exception as e:
        add_result("Resumen estadístico", False, str(e))

    # Resultado global
    passed = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]
    print("\n== Resultado Global ==")
    print(f"Total: {len(results)} | PASS: {len(passed)} | FAIL: {len(failed)}")

    if failed:
        print("\nPruebas fallidas:")
        for item in failed:
            print(f" - {item.name}: {item.detail}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
