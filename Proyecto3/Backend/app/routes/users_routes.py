"""Rutas de gestión de usuarios RFID"""
from flask import Blueprint, request
from app.services import UserService
from app.schemas import UserCreateSchema, UserUpdateSchema
from app.utils import token_required, create_response, create_error_response

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('', methods=['GET'])
@token_required
def get_users(admin_id, email):
    """
    Obtener lista de usuarios RFID registrados
    
    Parámetros:
    - skip: Número de registros a saltar (default: 0)
    - limit: Máximo de registros a retornar (default: 50)
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    users = UserService.get_all_users(skip=skip, limit=limit)
    
    return create_response(
        data=users,
        message=f"Se encontraron {len(users)} usuarios",
        status_code=200
    )


@bp.route('/<user_id>', methods=['GET'])
@token_required
def get_user(user_id, admin_id, email):
    """Obtener detalles de un usuario específico por ID"""
    user = UserService.get_user_by_id(user_id)
    
    if not user:
        return create_error_response("Usuario no encontrado", 404)
    
    return create_response(
        data=user,
        message="Usuario encontrado",
        status_code=200
    )


@bp.route('', methods=['POST'])
@token_required
def create_user(admin_id, email):
    """Crear nuevo usuario RFID"""
    data = request.get_json()
    
    if not data:
        return create_error_response("Body vacío", 400)
    
    # Validar esquema
    valid, message = UserCreateSchema.validate(data)
    if not valid:
        return create_error_response(message, 400)
    
    # Crear usuario
    success, result = UserService.create_user(
        rfid_card=data['rfid_card'],
        name=data['name']
    )
    
    if not success:
        return create_error_response(result, 400)
    
    return create_response(
        data=result,
        message="Usuario RFID creado exitosamente",
        status_code=201
    )


@bp.route('/<user_id>', methods=['PUT'])
@token_required
def update_user(user_id, admin_id, email):
    """
    Actualizar usuario (solo name y is_active)
    
    Body:
    {
        "name": "Juan Carlos López",
        "is_active": true
    }
    """
    data = request.get_json()
    
    if not data:
        return create_error_response("Datos faltantes", 400)
    
    # Validar esquema
    valid, message = UserUpdateSchema.validate(data)
    if not valid:
        return create_error_response(message, 400)
    
    # Actualizar usuario
    success, message = UserService.update_user(user_id, data)
    
    if not success:
        status_code = 404 if "no encontrado" in message else 400
        return create_error_response(message, status_code)
    
    return create_response(
        message=message,
        status_code=200
    )


@bp.route('/<user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id, admin_id, email):
    """Eliminar un usuario RFID"""
    success, message = UserService.delete_user(user_id)
    
    if not success:
        return create_error_response(message, 404)
    
    return create_response(
        message=message,
        status_code=200
    )


@bp.route('/<user_id>/activate', methods=['PATCH'])
@token_required
def activate_user(user_id, admin_id, email):
    """Activar usuario (permitir acceso con su tarjeta RFID)"""
    success, message = UserService.activate_user(user_id)
    
    if not success:
        return create_error_response(message, 400)
    
    return create_response(
        message=message,
        status_code=200
    )


@bp.route('/<user_id>/deactivate', methods=['PATCH'])
@token_required
def deactivate_user(user_id, admin_id, email):
    """Desactivar usuario (bloquear acceso con su tarjeta RFID)"""
    success, message = UserService.deactivate_user(user_id)
    
    if not success:
        return create_error_response(message, 400)
    
    return create_response(
        message=message,
        status_code=200
    )


@bp.route('/<user_id>/balance', methods=['PATCH'])
@token_required
def update_user_balance(user_id, admin_id, email):
    """
    Cargar saldo a un usuario
    
    Body:
    {
        "amount": 100.00
    }
    """
    data = request.get_json()
    
    if not data or 'amount' not in data:
        return create_error_response("Campo 'amount' requerido", 400)
    
    try:
        amount = float(data['amount'])
    except (ValueError, TypeError):
        return create_error_response("'amount' debe ser un número", 400)
    
    success, message = UserService.update_balance(user_id, amount)
    
    if not success:
        status_code = 404 if "no encontrado" in message else 400
        return create_error_response(message, status_code)
    
    return create_response(
        message=message,
        status_code=200
    )


@bp.route('/<user_id>/balance/reset', methods=['PATCH'])
@token_required
def reset_user_balance(user_id, admin_id, email):
    """Reiniciar saldo del usuario a Q5.00"""
    success, message = UserService.reset_balance(user_id, 5.0)

    if not success:
        status_code = 404 if "no encontrado" in message else 400
        return create_error_response(message, status_code)

    return create_response(
        message=message,
        status_code=200
    )
