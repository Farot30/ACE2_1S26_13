"""Rutas de autenticación"""
from flask import Blueprint, request, jsonify
from app.services import AuthService, JWTService
from app.schemas import LoginSchema, RegisterSchema
from app.utils import create_response, create_error_response

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register():
    """Registrar nuevo administrador"""
    data = request.get_json()
    
    if not data:
        return create_error_response("Datos faltantes", 400)
    
    # Validar esquema
    valid, message = RegisterSchema.validate(data)
    if not valid:
        return create_error_response(message, 400)
    
    # Registrar administrador
    success, result = AuthService.register_admin(
        email=data['email'],
        name=data['name'],
        password=data['password']
    )
    
    if not success:
        return create_error_response(result, 400)
    
    return create_response(
        data={'admin_id': result},
        message="Administrador registrado exitosamente",
        status_code=201
    )


@bp.route('/login', methods=['POST'])
def login():
    """Autenticar administrador y generar JWT"""
    data = request.get_json()
    
    if not data:
        return create_error_response("Datos faltantes", 400)
    
    # Validar esquema
    valid, message = LoginSchema.validate(data)
    if not valid:
        return create_error_response(message, 400)
    
    # Verificar credenciales
    success, admin, message = AuthService.verify_credentials(
        email=data['email'],
        password=data['password']
    )
    
    if not success:
        return create_error_response(message, 401)
    
    # Generar token
    try:
        token = JWTService.create_token(str(admin['_id']), admin['email'])
        
        return create_response(
            data={
                'token': token,
                'admin_id': str(admin['_id']),
                'email': admin['email'],
                'name': admin['name']
            },
            message="Autenticación exitosa",
            status_code=200
        )
    except Exception as e:
        return create_error_response(str(e), 500)


@bp.route('/validate-token', methods=['POST'])
def validate_token():
    """Validar token JWT"""
    data = request.get_json()
    
    if not data or 'token' not in data:
        return create_error_response("Token faltante", 400)
    
    try:
        payload = JWTService.validate_token(data['token'])
        return create_response(
            data=payload,
            message="Token válido",
            status_code=200
        )
    except Exception as e:
        return create_error_response(str(e), 401)
