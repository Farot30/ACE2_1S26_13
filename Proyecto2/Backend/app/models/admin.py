from datetime import datetime
from bson.objectid import ObjectId

class Admin:
    """Modelo de Administrador"""
    
    @staticmethod
    def create(email, name, password_hash, is_active=True):
        """Crear un nuevo administrador"""
        return {
            '_id': ObjectId(),
            'email': email,
            'name': name,
            'password_hash': password_hash,
            'is_active': is_active,
            'role': 'admin',
            'last_login': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    @staticmethod
    def to_dict(doc):
        """Convertir documento a diccionario sin credenciales"""
        if doc is None:
            return None
        doc['id'] = str(doc.get('_id', ''))
        doc.pop('_id', None)
        doc.pop('password_hash', None)
        return doc
