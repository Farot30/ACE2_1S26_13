"""Rutas públicas para métricas (sin JWT)"""
from flask import Blueprint
from pymongo import MongoClient
import os
from datetime import datetime

bp = Blueprint('metrics', __name__, url_prefix='/api/metrics')

def get_db_connection():
    """Obtener conexión a MongoDB"""
    mongo_host = os.getenv('MONGO_HOST', 'localhost')
    mongo_port = int(os.getenv('MONGO_PORT', 27017))
    mongo_user = os.getenv('MONGO_USER', 'park_user')
    mongo_password = os.getenv('MONGO_PASSWORD', 'park_password')
    mongo_db = os.getenv('MONGO_DB', 'park_guard')
    
    client = MongoClient(f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}")
    return client[ mongo_db]


@bp.route('', methods=['GET'])
def get_metrics():
    """Obtener métricas simples para Grafana"""
    try:
        db = get_db_connection()
        
        total_spaces = 5
        
        occupied = db.parking_spaces.count_documents({'is_occupied': True})
        available = total_spaces - occupied
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        access_granted = db.events.count_documents({
            'event_type': 'ACCESS_GRANTED',
            'timestamp': {'$gte': today_start}
        })
        
        access_denied = db.events.count_documents({
            'event_type': 'ACCESS_DENIED',
            'timestamp': {'$gte': today_start}
        })
        
        emergencies = db.events.count_documents({
            'event_type': 'EMERGENCY_TRIGGERED',
            'timestamp': {'$gte': today_start}
        })
        
        recent_events = list(db.events.find().sort('timestamp', -1).limit(10))
        
        for event in recent_events:
            event['_id'] = str(event['_id'])
            if 'timestamp' in event:
                event['timestamp'] = event['timestamp'].isoformat()
        
        return {
            'success': True,
            'data': {
                'parking': {
                    'total_spaces': total_spaces,
                    'occupied_spaces': occupied,
                    'available_spaces': available,
                    'occupancy_percentage': round((occupied / total_spaces) * 100, 2) if total_spaces > 0 else 0
                },
                'events': {
                    'access_granted': access_granted,
                    'access_denied': access_denied,
                    'emergencies': emergencies
                },
                'recent_events': recent_events
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500