from datetime import datetime
from bson.objectid import ObjectId

class SystemLog:
    """Modelo de Log del Sistema"""
    
    # Niveles de log
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    @staticmethod
    def create(level, message, source=None, data=None):
        """
        Crear un log del sistema
        
        Args:
            level: Nivel del log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Mensaje del log
            source: Fuente del log (ej: "mqtt", "api", "database")
            data: Datos adicionales
        """
        return {
            '_id': ObjectId(),
            'level': level,
            'message': message,
            'source': source,
            'data': data or {},
            'timestamp': datetime.utcnow()
        }
    
    @staticmethod
    def to_dict(doc):
        """Convertir documento a diccionario"""
        if doc is None:
            return None
        doc['id'] = str(doc.get('_id', ''))
        doc.pop('_id', None)
        return doc
