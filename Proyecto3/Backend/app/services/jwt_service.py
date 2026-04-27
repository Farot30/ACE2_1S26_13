"""Servicio de JWT para autenticación"""
import jwt
from datetime import datetime, timedelta
from flask import current_app

class JWTService:
    """Servicio para manejo de JWT"""
    
    @staticmethod
    def create_token(admin_id, email, expires_in=None):
        """
        Crear un token JWT
        
        Args:
            admin_id: ID del administrador
            email: Email del administrador
            expires_in: Tiempo de expiración en horas (usa config si no se especifica)
        
        Returns:
            Token JWT codificado
        """
        if expires_in is None:
            expires_in = current_app.config.get('JWT_EXPIRATION_HOURS', 24)
        
        payload = {
            'admin_id': str(admin_id),
            'email': email,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_in)
        }
        
        try:
            token = jwt.encode(
                payload,
                current_app.config['SECRET_KEY'],
                algorithm=current_app.config['JWT_ALGORITHM']
            )
            return token
        except Exception as e:
            raise Exception(f"Error creando token: {str(e)}")
    
    @staticmethod
    def validate_token(token):
        """
        Validar un token JWT
        
        Args:
            token: Token a validar
        
        Returns:
            Diccionario con datos del token si es válido, None si no
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token expirado")
        except jwt.InvalidTokenError:
            raise Exception("Token inválido")
        except Exception as e:
            raise Exception(f"Error validando token: {str(e)}")
    
    @staticmethod
    def extract_token(request):
        """
        Extraer token del header Authorization
        
        Args:
            request: Objeto de la solicitud Flask
        
        Returns:
            Token si existe, None en caso contrario
        """
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:]  # Remover "Bearer "
        return token
