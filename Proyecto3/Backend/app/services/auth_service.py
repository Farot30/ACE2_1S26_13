"""Servicio para autenticación de administradores"""
from bson.objectid import ObjectId
from app import get_db
from app.models import Admin
from werkzeug.security import generate_password_hash, check_password_hash

class AuthService:
    """Servicio para autenticación"""
    
    @staticmethod
    def register_admin(email, name, password):
        """Registrar un nuevo administrador"""
        db = get_db()
        
        # Verificar si email ya existe
        existing = db.admins.find_one({'email': email.lower()})
        if existing:
            return False, "Email ya está registrado"
        
        password_hash = generate_password_hash(password)
        
        admin = Admin.create(
            email=email.lower(),
            name=name,
            password_hash=password_hash
        )
        
        result = db.admins.insert_one(admin)
        return True, str(result.inserted_id)
    
    @staticmethod
    def verify_credentials(email, password):
        """Verificar credenciales de administrador"""
        db = get_db()
        
        admin = db.admins.find_one({'email': email.lower()})
        
        if not admin:
            return False, None, "Email o contraseña inválidos"
        
        if not admin.get('is_active', False):
            return False, None, "Administrador desactivado"
        
        if not check_password_hash(admin['password_hash'], password):
            return False, None, "Email o contraseña inválidos"
        
        from datetime import datetime
        db.admins.update_one(
            {'_id': admin['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        return True, admin, "Autenticación exitosa"
    
    @staticmethod
    def get_admin_by_id(admin_id):
        """Obtener administrador por ID"""
        db = get_db()
        
        try:
            admin = db.admins.find_one({'_id': ObjectId(admin_id)})
            return Admin.to_dict(admin) if admin else None
        except:
            return None
    
    @staticmethod
    def get_admin_by_email(email):
        """Obtener administrador por email"""
        db = get_db()
        
        admin = db.admins.find_one({'email': email.lower()})
        return Admin.to_dict(admin) if admin else None
