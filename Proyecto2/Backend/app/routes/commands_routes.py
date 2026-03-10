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


@bp.route('/barrier/<int:space_number>', methods=['POST'])
@token_required
def control_barrier(space_number, admin_id, email):
    """Controlar barrera de estacionamiento"""
    
    if space_number < 1 or space_number > 5:
        return create_error_response("Número de espacio debe estar entre 1 y 5", 400)
    
    data = request.get_json() or {}
    action = data.get('action', 'open')  # open o close
    
    if action not in ['open', 'close']:
        return create_error_response("Acción debe ser 'open' o 'close'", 400)
    
    try:
        mqtt = get_mqtt_service()
        
        payload = {
            'command': f'{action}_barrier',
            'space_number': space_number,
            'triggered_by': email,
            'timestamp': str(__import__('datetime').datetime.utcnow())
        }
        
        mqtt.publish(f'/park-guard/commands/barrier/{space_number}', payload, qos=1)
        
        message = f"Barrera {space_number} {'abierta' if action == 'open' else 'cerrada'}"
        return create_response(
            message=f"Comando enviado: {message}",
            status_code=200
        )
    except Exception as e:
        return create_error_response(f"Error: {str(e)}", 500)
