"""
Manejo de eventos WebSocket para actualizaciones en tiempo real
Permite que el frontend (P5.js) reciba actualizaciones de:
- Ocupación de espacios
- Estado de talanqueras/puertas
- Estado del ventilador
- Emergencias
"""

from flask_socketio import emit, join_room, leave_room, disconnect
from app import get_db
from datetime import datetime

# Sala de parqueo para todos los clientes conectados
PARKING_ROOM = 'parking-updates'

def register_socketio_events(socketio):
    """Registrar todos los handlers de eventos WebSocket"""
    
    @socketio.on('connect')
    def handle_connect():
        """Cliente se conecta"""
        join_room(PARKING_ROOM)
        emit('connection_response', {
            'status': 'connected',
            'message': 'Conectado al servidor de actualizaciones',
            'timestamp': datetime.utcnow().isoformat()
        })
        print(f"✓ Cliente conectado a WebSocket")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Cliente se desconecta"""
        leave_room(PARKING_ROOM)
        print(f"✓ Cliente desconectado de WebSocket")
    
    @socketio.on('subscribe_parking')
    def handle_subscribe_parking(data):
        """Cliente se suscribe a actualizaciones de parqueo"""
        join_room(PARKING_ROOM)
        emit('subscribe_response', {
            'status': 'success',
            'message': 'Suscrito a actualizaciones de parqueo',
            'timestamp': datetime.utcnow().isoformat()
        })
        print(f"✓ Cliente suscrito a actualizaciones de parqueo")


def emit_parking_update(socketio, space_number, occupancy_status, emergency=False):
    """
    Emitir actualización de estado de un espacio de parqueo
    
    Args:
        socketio: Instancia de SocketIO
        space_number: Número del espacio (1-5)
        occupancy_status: True (ocupado) o False (disponible)
        emergency: Si hay emergencia en el espacio
    """
    data = {
        'event_type': 'parking_update',
        'space_number': space_number,
        'is_occupied': occupancy_status,
        'is_emergency': emergency,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    socketio.emit('parking_update', data, room=PARKING_ROOM)
    print(f"📤 Emitido: Espacio {space_number} - Ocupado: {occupancy_status}")


def emit_ventilator_update(socketio, ventilator_status, gas_level=None):
    """
    Emitir actualización de estado del ventilador
    
    Args:
        socketio: Instancia de SocketIO
        ventilator_status: True (encendido) o False (apagado)
        gas_level: Nivel de gas detectado (opcional)
    """
    data = {
        'event_type': 'ventilator_update',
        'is_active': ventilator_status,
        'gas_level': gas_level,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    socketio.emit('ventilator_update', data, room=PARKING_ROOM)
    print(f"📤 Emitido: Ventilador - Estado: {ventilator_status}")


def emit_door_update(socketio, door_number, is_open):
    """
    Emitir actualización de estado de una talanquera/puerta
    
    Args:
        socketio: Instancia de SocketIO
        door_number: Número de la puerta/talanquera
        is_open: True (abierta) o False (cerrada)
    """
    data = {
        'event_type': 'door_update',
        'door_number': door_number,
        'is_open': is_open,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    socketio.emit('door_update', data, room=PARKING_ROOM)
    print(f"📤 Emitido: Puerta {door_number} - Abierta: {is_open}")


def emit_emergency_alert(socketio, event_type, location, severity='high'):
    """
    Emitir alerta de emergencia
    
    Args:
        socketio: Instancia de SocketIO
        event_type: Tipo de emergencia (fire, intrusion, gas_leak, etc)
        location: Ubicación de la emergencia
        severity: Severidad (low, medium, high, critical)
    """
    data = {
        'event_type': 'emergency_alert',
        'alert_type': event_type,
        'location': location,
        'severity': severity,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    socketio.emit('emergency_alert', data, room=PARKING_ROOM)
    print(f"🚨 ALERTA EMITIDA: {event_type} en {location} - Severidad: {severity}")


def emit_system_status(socketio, status):
    """
    Emitir estado general del sistema
    
    Args:
        socketio: Instancia de SocketIO
        status: Dict con estados de componentes
    """
    data = {
        'event_type': 'system_status',
        'status': status,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    socketio.emit('system_status', data, room=PARKING_ROOM)
    print(f"📤 Emitido: Estado del sistema")
