"""Rutas de gestión de espacios de parqueo"""
from flask import Blueprint, request
from app.services import ParkingService
from app.utils import token_required, create_response, create_error_response

bp = Blueprint('parking', __name__, url_prefix='/api/parking')

@bp.route('/initialize', methods=['POST'])
@token_required
def initialize_spaces(admin_id, email):
    """Inicializar los 5 espacios de parqueo"""
    success, message = ParkingService.initialize_parking_spaces()
    
    status_code = 200 if success else 400
    return create_response(
        message=message,
        status_code=status_code
    )


@bp.route('/spaces', methods=['GET'])
@token_required
def get_spaces(admin_id, email):
    """Obtener todos los espacios"""
    spaces = ParkingService.get_all_spaces()
    
    return create_response(
        data=spaces,
        message=f"Se encontraron {len(spaces)} espacios",
        status_code=200
    )


@bp.route('/spaces/<int:space_number>', methods=['GET'])
@token_required
def get_space(space_number, admin_id, email):
    """Obtener espacio por número"""
    if space_number < 1 or space_number > 5:
        return create_error_response("Número de espacio debe estar entre 1 y 5", 400)
    
    space = ParkingService.get_space_by_number(space_number)
    
    if not space:
        return create_error_response("Espacio no encontrado", 404)
    
    return create_response(
        data=space,
        message="Espacio encontrado",
        status_code=200
    )


@bp.route('/available', methods=['GET'])
@token_required
def get_available_count(admin_id, email):
    """Obtener cantidad de espacios disponibles"""
    available = ParkingService.get_available_spaces()
    
    return create_response(
        data={'available_spaces': available},
        message=f"Espacios disponibles: {available}",
        status_code=200
    )


@bp.route('/spaces/<int:space_number>/enable', methods=['PATCH'])
@token_required
def enable_space(space_number, admin_id, email):
    """Habilitar espacio"""
    if space_number < 1 or space_number > 5:
        return create_error_response("Número de espacio debe estar entre 1 y 5", 400)
    
    success, message = ParkingService.enable_space(space_number)
    
    if not success:
        return create_error_response(message, 400)
    
    return create_response(
        message=message,
        status_code=200
    )


@bp.route('/spaces/<int:space_number>/disable', methods=['PATCH'])
@token_required
def disable_space(space_number, admin_id, email):
    """Deshabilitar espacio"""
    if space_number < 1 or space_number > 5:
        return create_error_response("Número de espacio debe estar entre 1 y 5", 400)
    
    success, message = ParkingService.disable_space(space_number)
    
    if not success:
        return create_error_response(message, 400)
    
    return create_response(
        message=message,
        status_code=200
    )
