from datetime import datetime
from bson.objectid import ObjectId

class SuspiciousActivity:
    """Modelo de Actividad Sospechosa"""
    
    # Tipos de actividades sospechosas
    MULTIPLE_FAILED_ATTEMPTS = "multiple_failed_attempts"
    UNUSUAL_TIME_PATTERN = "unusual_time_pattern"
    MULTIPLE_SPACES_RAPID = "multiple_spaces_rapid"
    
    @staticmethod
    def create(user_id, activity_type, details=None, severity="low"):
        """
        Crear un registro de actividad sospechosa
        
        Args:
            user_id: ID del usuario
            activity_type: Tipo de actividad sospechosa
            details: Detalles adicionales
            severity: Severidad (low, medium, high, critical)
        """
        return {
            '_id': ObjectId(),
            'user_id': user_id,
            'activity_type': activity_type,
            'severity': severity,
            'details': details or {},
            'timestamp': datetime.utcnow(),
            'resolved': False,
            'resolved_by': None,
            'resolution_time': None,
            'notes': ""
        }
    
    @staticmethod
    def to_dict(doc):
        """Convertir documento a diccionario"""
        if doc is None:
            return None
        doc['id'] = str(doc.get('_id', ''))
        doc.pop('_id', None)
        return doc
