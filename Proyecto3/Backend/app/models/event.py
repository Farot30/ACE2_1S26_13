from datetime import datetime
from bson.objectid import ObjectId

class Event:
    """Modelo de Evento del Sistema"""
    
    # Tipos de eventos
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    SPACE_OCCUPIED = "space_occupied"
    SPACE_EMPTY = "space_empty"
    EMERGENCY_TRIGGERED = "emergency_triggered"
    EMERGENCY_RESOLVED = "emergency_resolved"
    FAN_ACTIVATED = "fan_activated"
    FAN_DEACTIVATED = "fan_deactivated"
    BARRIER_OPENED = "barrier_opened"
    BARRIER_CLOSED = "barrier_closed"
    SPACE_ENABLED = "space_enabled"
    SPACE_DISABLED = "space_disabled"
    MANUAL_EXIT = "manual_exit"
    
    @staticmethod
    def create(event_type, user_id=None, space_id=None, data=None, description=""):
        """
        Crear un nuevo evento
        
        Args:
            event_type: Tipo de evento
            user_id: ID del usuario (si aplica)
            space_id: ID del espacio (si aplica)
            data: Datos adicionales del evento
            description: Descripción del evento
        """
        return {
            '_id': ObjectId(),
            'event_type': event_type,
            'user_id': user_id,
            'space_id': space_id,
            'description': description,
            'data': data or {},
            'timestamp': datetime.utcnow(),
            'resolved': False
        }
    
    @staticmethod
    def to_dict(doc):
        """Convertir documento a diccionario"""
        if doc is None:
            return None
        doc['id'] = str(doc.get('_id', ''))
        doc.pop('_id', None)
        return doc
