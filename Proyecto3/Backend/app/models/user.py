from datetime import datetime
from bson.objectid import ObjectId

class User:
    """
    Modelo de Usuario RFID
    
    Representa a una persona que tiene una tarjeta RFID para acceder al parqueo.
    NO tiene credenciales de login (es solo una tarjeta que se valida en la BD).
    """
    
    @staticmethod
    def create(rfid_card, name, is_active=True):
        """
        Crear un nuevo usuario RFID
        
        Args:
            rfid_card: Identificador de tarjeta (8 caracteres hex, ej: B91E19B4)
            name: Nombre de la persona
            is_active: Si está habilitado para acceder
        """
        return {
            '_id': ObjectId(),
            'rfid_card': rfid_card,
            'name': name,
            'is_active': is_active,
            'balance': 5.0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'last_access': None,
            'access_count': 0
        }
    
    @staticmethod
    def to_dict(doc):
        """Convertir documento a diccionario para enviar en respuesta"""
        if doc is None:
            return None
        if doc.get('balance') is None:
            doc['balance'] = 5.0
        doc['id'] = str(doc.get('_id', ''))
        doc.pop('_id', None)
        return doc
