# MQTT Topics - Park-Guard 2.0

Este documento define los topics MQTT reales usados por el backend y el puente Raspberry Pi.

## Publicados por Raspberry Pi (puente desde Arduino)

park-guard/parking/<space_number>/status
  Publicador: Raspberry Pi (desde Arduino)
  Payload:
    {"type":"parking","space":1,"is_occupied":true,"timestamp":"..."}

park-guard/gas/sensor
  Publicador: Raspberry Pi (desde Arduino)
  Payload:
    {"type":"gas","ppm":150,"timestamp":"..."}

park-guard/rfid/read
  Publicador: Raspberry Pi (desde Arduino)
  Payload:
    {"type":"rfid","card_id":"ABC123","timestamp":"..."}

park-guard/emergency/trigger
  Publicador: Raspberry Pi (desde Arduino)
  Payload:
    {"type":"emergency","timestamp":"..."}

park-guard/ventilator/command
  Publicador: Raspberry Pi (desde Arduino)
  Payload:
    {"type":"ventilator","is_active":true,"gas_level":150,"timestamp":"..."}

## Publicados por Backend (comandos)

/park-guard/commands/fan
  Publicador: Backend
  Payload:
    {"command":"activate_fan","timestamp":"..."}
    {"command":"deactivate_fan","timestamp":"..."}

/park-guard/commands/emergency
  Publicador: Backend
  Payload:
    {"command":"activate_emergency","triggered_by":"admin","timestamp":"..."}
    {"command":"deactivate_emergency","resolved_by":"admin","timestamp":"..."}

/park-guard/commands/door/entrance
  Publicador: Backend
  Payload:
    {"command":"open_door","door":"entrance","triggered_by":"admin","timestamp":"..."}
    {"command":"close_door","door":"entrance","triggered_by":"admin","timestamp":"..."}

/park-guard/commands/door/exit
  Publicador: Backend
  Payload:
    {"command":"open_door","door":"exit","triggered_by":"admin","timestamp":"..."}
    {"command":"close_door","door":"exit","triggered_by":"admin","timestamp":"..."}

## Topics de estado (publicados por Arduino/Raspberry Pi)

park-guard/doors/entrance/status
  Publicador: Raspberry Pi (desde Arduino)
  Payload:
    {"type":"door_update","door":"entrance","is_open":true,"timestamp":"..."}

park-guard/doors/exit/status
  Publicador: Raspberry Pi (desde Arduino)
  Payload:
    {"type":"door_update","door":"exit","is_open":true,"timestamp":"..."}

/park-guard/commands/access
  Publicador: Backend (opcional)
  Payload:
    {"cmd":"access","granted":true}
    {"cmd":"access","granted":false}

## Nota de arquitectura

- No se usa ESP32. El flujo real es Arduino -> Raspberry Pi (serial USB) -> MQTT.
- La Raspberry Pi es solo puente y no ejecuta contenedores.
