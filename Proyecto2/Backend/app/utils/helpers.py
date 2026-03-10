"""Utilidades generales"""
from datetime import datetime
from bson.objectid import ObjectId

def serialize_mongodb_doc(doc):
    """Convertir documento MongoDB a JSON serializable"""
    if doc is None:
        return None
    
    if isinstance(doc, list):
        return [serialize_mongodb_doc(item) for item in doc]
    
    if isinstance(doc, dict):
        serialized = {}
        for key, value in doc.items():
            if key == '_id':
                serialized['id'] = str(value) if value else None
            elif isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = serialize_mongodb_doc(value)
            elif isinstance(value, list):
                serialized[key] = [serialize_mongodb_doc(item) for item in value]
            else:
                serialized[key] = value
        return serialized
    
    if isinstance(doc, ObjectId):
        return str(doc)
    
    if isinstance(doc, datetime):
        return doc.isoformat()
    
    return doc

def create_response(data=None, message="", status_code=200):
    """Crear respuesta estándar"""
    response = {
        'status': 'success' if 200 <= status_code < 300 else 'error',
        'message': message,
        'data': serialize_mongodb_doc(data) if data else None
    }
    return response, status_code

def create_error_response(message, status_code=400):
    """Crear respuesta de error"""
    return create_response(message=message, status_code=status_code)
