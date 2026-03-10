"""Rutas de eventos y estadísticas"""
from flask import Blueprint, request
from app.services import EventService, ParkingService, UserService
from app.models import Event
from app.utils import token_required, create_response, create_error_response
from datetime import datetime, timedelta

bp = Blueprint('events', __name__, url_prefix='/api/events')

@bp.route('', methods=['GET'])
@token_required
def get_events(admin_id, email):
    """Obtener eventos con filtros opcionales"""
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 50, type=int)
    event_type = request.args.get('event_type', None, type=str)
    user_id = request.args.get('user_id', None, type=str)
    
    events = EventService.get_all_events(
        skip=skip,
        limit=limit,
        event_type=event_type,
        user_id=user_id
    )
    
    return create_response(
        data=events,
        message=f"Se encontraron {len(events)} eventos",
        status_code=200
    )


@bp.route('/user/<user_id>', methods=['GET'])
@token_required
def get_user_events(user_id, admin_id, email):
    """Obtener eventos de un usuario"""
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    events = EventService.get_events_by_user(user_id, skip=skip, limit=limit)
    
    return create_response(
        data=events,
        message=f"Se encontraron {len(events)} eventos para el usuario",
        status_code=200
    )


@bp.route('/type/<event_type>', methods=['GET'])
@token_required
def get_events_by_type(event_type, admin_id, email):
    """Obtener eventos por tipo"""
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    events = EventService.get_events_by_type(event_type, skip=skip, limit=limit)
    
    return create_response(
        data=events,
        message=f"Se encontraron {len(events)} eventos de tipo {event_type}",
        status_code=200
    )


@bp.route('/summary', methods=['GET'])
@token_required
def get_summary(admin_id, email):
    """Obtener resumen de estadísticas"""
    
    # Obtener datos
    available_spaces = ParkingService.get_available_spaces()
    total_spaces = 5
    occupied_spaces = total_spaces - available_spaces
    
    # Eventos de hoy
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.utcnow()
    
    access_granted = EventService.get_events_by_type(Event.ACCESS_GRANTED)
    access_denied = EventService.get_events_by_type(Event.ACCESS_DENIED)
    emergencies = EventService.get_events_by_type(Event.EMERGENCY_TRIGGERED)
    
    total_users = len(UserService.get_all_users(limit=1000))
    
    summary = {
        'parking': {
            'total_spaces': total_spaces,
            'occupied_spaces': occupied_spaces,
            'available_spaces': available_spaces,
            'occupancy_percentage': round((occupied_spaces / total_spaces) * 100, 2)
        },
        'events': {
            'access_granted_today': len(access_granted),
            'access_denied_today': len(access_denied),
            'emergencies_today': len(emergencies)
        },
        'users': {
            'total_registered': total_users
        }
    }
    
    return create_response(
        data=summary,
        message="Resumen de estadísticas",
        status_code=200
    )


@bp.route('/access/validate', methods=['POST'])
def validate_access():
    """
    Validar acceso RFID
    
    Este endpoint es llamado por el Consumer MQTT después de leer una tarjeta
    """
    data = request.get_json()
    
    if not data or 'rfid_card' not in data:
        return create_error_response("RFID faltante", 400)
    
    rfid_card = data['rfid_card'].upper()
    
    # Buscar usuario por RFID
    user = UserService.get_user_by_rfid(rfid_card)
    
    if not user:
        # Usuario no existe
        EventService.record_access_attempt(rfid_card, success=False)
        return create_response(
            data={
                'authorized': False,
                'user_id': None,
                'message': 'Tarjeta no registrada'
            },
            status_code=200
        )
    
    if not user.get('is_active', False):
        # Usuario desactivado
        EventService.record_access_attempt(rfid_card, success=False, user_id=user['id'])
        return create_response(
            data={
                'authorized': False,
                'user_id': user['id'],
                'message': 'Usuario desactivado'
            },
            status_code=200
        )
    
    # Verificar espacios disponibles
    available = ParkingService.get_available_spaces()
    
    if available == 0:
        EventService.record_access_attempt(rfid_card, success=False, user_id=user['id'])
        return create_response(
            data={
                'authorized': False,
                'user_id': user['id'],
                'message': 'Parqueo lleno'
            },
            status_code=200
        )
    
    # Acceso concedido
    UserService.update_access_stats(user['id'])
    EventService.record_access_attempt(rfid_card, success=True, user_id=user['id'])
    
    return create_response(
        data={
            'authorized': True,
            'user_id': user['id'],
            'user_name': user['name'],
            'message': 'Acceso concedido'
        },
        status_code=200
    )
