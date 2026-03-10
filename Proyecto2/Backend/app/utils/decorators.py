"""Decoradores para proteger rutas"""
from functools import wraps
from flask import request, jsonify
from app.services import JWTService

def token_required(f):
    """Decorador para requerir token JWT válido"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = JWTService.extract_token(request)
        
        if not token:
            return jsonify({'error': 'Token faltante'}), 401
        
        try:
            payload = JWTService.validate_token(token)
            kwargs['admin_id'] = payload['admin_id']
            kwargs['email'] = payload['email']
        except Exception as e:
            return jsonify({'error': str(e)}), 401
        
        return f(*args, **kwargs)
    
    return decorated
