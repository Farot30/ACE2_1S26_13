"""Rutas de comandos remotos (comunicación MQTT)"""
from flask import Blueprint, request
from app.services import MQTTService
from app.utils import token_required, create_response, create_error_response
import json

bp = Blueprint('commands', __name__, url_prefix='/api/commands')

mqtt_service = None

def get_mqtt_service():
    """Obtener instancia del servicio MQTT"""
    global mqtt_service
    if mqtt_service is None:
        mqtt_service = MQTTService()
    return mqtt_service


@bp.route('/fan/activate', methods=['POST'])
@token_required
def activate_fan(admin_id, email):
    """Activar ventilador remotamente"""
    try:
        mqtt = get_mqtt_service()
        
        payload = {
            'command': 'activate_fan',
            'timestamp': str(__import__('datetime').datetime.utcnow())
        }
        
        mqtt.publish('/park-guard/commands/fan', payload, qos=1)
        
        return create_response(
            message="Comando enviado: ventilador activado",
            status_code=200
        )
    except Exception as e:
        return create_error_response(f"Error: {str(e)}", 500)


@bp.route('/fan/deactivate', methods=['POST'])
@token_required
def deactivate_fan(admin_id, email):
    """Desactivar ventilador remotamente"""
    try:
        mqtt = get_mqtt_service()
        
        payload = {
            'command': 'deactivate_fan',
            'timestamp': str(__import__('datetime').datetime.utcnow())
        }
        
        mqtt.publish('/park-guard/commands/fan', payload, qos=1)
        
        return create_response(
            message="Comando enviado: ventilador desactivado",
            status_code=200
        )
    except Exception as e:
        return create_error_response(f"Error: {str(e)}", 500)


@bp.route('/emergency/activate', methods=['POST'])
@token_required
def activate_emergency(admin_id, email):
    """Activar modo emergencia remotamente"""
    try:
        mqtt = get_mqtt_service()
        
        payload = {
            'command': 'activate_emergency',
            'triggered_by': email,
            'timestamp': str(__import__('datetime').datetime.utcnow())
        }
        
        mqtt.publish('/park-guard/commands/emergency', payload, qos=1)
        
        return create_response(
            message="Comando enviado: emergencia activada",
            status_code=200
        )
    except Exception as e:
        return create_error_response(f"Error: {str(e)}", 500)


@bp.route('/emergency/deactivate', methods=['POST'])
@token_required
def deactivate_emergency(admin_id, email):
    """Desactivar modo emergencia remotamente"""
    try:
        mqtt = get_mqtt_service()
        
        payload = {
            'command': 'deactivate_emergency',
            'resolved_by': email,
            'timestamp': str(__import__('datetime').datetime.utcnow())
        }
        
        mqtt.publish('/park-guard/commands/emergency', payload, qos=1)
        
        return create_response(
            message="Comando enviado: emergencia desactivada",
            status_code=200
        )
    except Exception as e:
        return create_error_response(f"Error: {str(e)}", 500)


@bp.route('/door/entrance/open', methods=['POST'])
@token_required
def open_entrance(admin_id, email):
    """Abrir talanquera de entrada"""
    try:
        mqtt = get_mqtt_service()
        
        payload = {
            'command': 'open_door',
            'door': 'entrance',
            'triggered_by': email,
            'timestamp': str(__import__('datetime').datetime.utcnow())
        }
        
        mqtt.publish('/park-guard/commands/door/entrance', payload, qos=1)
        
        return create_response(
            message="Comando enviado: talanquera entrada abierta",
            status_code=200
        )
    except Exception as e:
        return create_error_response(f"Error: {str(e)}", 500)


@bp.route('/door/entrance/close', methods=['POST'])
@token_required
def close_entrance(admin_id, email):
    """Cerrar talanquera de entrada"""
    try:
        mqtt = get_mqtt_service()
        
        payload = {
            'command': 'close_door',
            'door': 'entrance',
            'triggered_by': email,
            'timestamp': str(__import__('datetime').datetime.utcnow())
        }
        
        mqtt.publish('/park-guard/commands/door/entrance', payload, qos=1)
        
        return create_response(
            message="Comando enviado: talanquera entrada cerrada",
            status_code=200
        )
    except Exception as e:
        return create_error_response(f"Error: {str(e)}", 500)


@bp.route('/door/exit/open', methods=['POST'])
@token_required
def open_exit(admin_id, email):
    """Abrir talanquera de salida"""
    try:
        mqtt = get_mqtt_service()
        
        payload = {
            'command': 'open_door',
            'door': 'exit',
            'triggered_by': email,
            'timestamp': str(__import__('datetime').datetime.utcnow())
        }
        
        mqtt.publish('/park-guard/commands/door/exit', payload, qos=1)
        
        return create_response(
            message="Comando enviado: talanquera salida abierta",
            status_code=200
        )
    except Exception as e:
        return create_error_response(f"Error: {str(e)}", 500)


@bp.route('/door/exit/close', methods=['POST'])
@token_required
def close_exit(admin_id, email):
    """Cerrar talanquera de salida"""
    try:
        mqtt = get_mqtt_service()
        
        payload = {
            'command': 'close_door',
            'door': 'exit',
            'triggered_by': email,
            'timestamp': str(__import__('datetime').datetime.utcnow())
        }
        
        mqtt.publish('/park-guard/commands/door/exit', payload, qos=1)
        
        return create_response(
            message="Comando enviado: talanquera salida cerrada",
            status_code=200
        )
    except Exception as e:
        return create_error_response(f"Error: {str(e)}", 500)
