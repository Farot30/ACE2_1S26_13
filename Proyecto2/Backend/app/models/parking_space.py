from datetime import datetime
from bson.objectid import ObjectId

class ParkingSpace:
    """
    Modelo de Espacio de Parqueo
    
    Representa uno de los 5 espacios físicos de la maqueta.
    El estado (ocupado/libre) se sincroniza con Arduino via MQTT.
    """
    
    @staticmethod
    def create(space_number, is_occupied=False, is_enabled=True):
        """
        Crear espacio de parqueo
        
        Args:
            space_number: Número del espacio (1-5)
            is_occupied: Estado inicial (falso = libre)
            is_enabled: Si está disponible (falso = mantenimiento)
        """
        return {
            '_id': ObjectId(),
            'space_number': space_number,
            'is_occupied': is_occupied,
            'is_enabled': is_enabled,
            'last_updated': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
    
    @staticmethod
    def to_dict(doc):
        """Convertir documento a diccionario"""
        if doc is None:
            return None
        doc['id'] = str(doc.get('_id', ''))
        doc.pop('_id', None)
        return doc
