"""Servicio para gestión de eventos"""
from bson.objectid import ObjectId
from app import get_db
from app.models import Event, SuspiciousActivity
from datetime import datetime, timedelta

class EventService:
    """Servicio para lógica de eventos"""
    
    @staticmethod
    def create_event(event_type, user_id=None, space_id=None, data=None, description=""):
        """Crear un nuevo evento"""
        db = get_db()
        
        user_obj_id = ObjectId(user_id) if user_id else None
        
        event = Event.create(
            event_type=event_type,
            user_id=user_obj_id,
            space_id=space_id,
            data=data,
            description=description
        )
        
        result = db.events.insert_one(event)
        return True, str(result.inserted_id)
    
    @staticmethod
    def get_all_events(skip=0, limit=50, event_type=None, user_id=None):
        """Obtener eventos con filtros opcionales"""
        db = get_db()
        
        query = {}
        if event_type:
            query['event_type'] = event_type
        if user_id:
            try:
                query['user_id'] = ObjectId(user_id)
            except:
                pass
        
        events = list(db.events.find(query).sort('timestamp', -1).skip(skip).limit(limit))
        return [Event.to_dict(event) for event in events]
    
    @staticmethod
    def get_events_by_user(user_id, skip=0, limit=50):
        """Obtener eventos de un usuario"""
        db = get_db()
        
        try:
            events = list(db.events.find(
                {'user_id': ObjectId(user_id)}
            ).sort('timestamp', -1).skip(skip).limit(limit))
            
            return [Event.to_dict(event) for event in events]
        except Exception as e:
            return []
    
    @staticmethod
    def get_events_by_type(event_type, skip=0, limit=50):
        """Obtener eventos por tipo"""
        db = get_db()
        
        events = list(db.events.find(
            {'event_type': event_type}
        ).sort('timestamp', -1).skip(skip).limit(limit))
        
        return [Event.to_dict(event) for event in events]
    
    @staticmethod
    def get_events_by_date_range(start_date, end_date):
        """Obtener eventos en un rango de fechas"""
        db = get_db()
        
        events = list(db.events.find({
            'timestamp': {
                '$gte': start_date,
                '$lte': end_date
            }
        }).sort('timestamp', -1))
        
        return [Event.to_dict(event) for event in events]
    
    @staticmethod
    def record_access_attempt(rfid_card, success=True, user_id=None, space_number=None):
        """
        Registrar intento de acceso
        
        Args:
            rfid_card: Tarjeta RFID
            success: Si fue exitoso
            user_id: ID del usuario (si se encontró)
            space_number: Número del espacio
        """
        db = get_db()
        
        if success:
            event_type = Event.ACCESS_GRANTED
            description = f"Acceso concedido con tarjeta {rfid_card[:4]}..."
        else:
            event_type = Event.ACCESS_DENIED
            description = f"Acceso denegado con tarjeta {rfid_card[:4]}..."
        
        user_obj_id = ObjectId(user_id) if user_id else None
        
        event = Event.create(
            event_type=event_type,
            user_id=user_obj_id,
            space_id=space_number,
            data={'rfid_card': rfid_card},
            description=description
        )
        
        db.events.insert_one(event)
        
        # Si no fue exitoso, detectar actividad sospechosa
        if not success:
            EventService._check_suspicious_activity(rfid_card)
    
    @staticmethod
    def _check_suspicious_activity(rfid_card):
        """Detectar actividad sospechosa por intentos fallidos"""
        db = get_db()
        
        # Buscar intentos fallidos en los últimos 5 minutos
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        
        failed_attempts = db.events.count_documents({
            'event_type': Event.ACCESS_DENIED,
            'data.rfid_card': rfid_card,
            'timestamp': {'$gte': five_min_ago}
        })
        
        # Si hay 3 o más intentos fallidos, registrar como sospechoso
        if failed_attempts >= 3:
            suspicious = SuspiciousActivity.create(
                user_id=rfid_card,  # Usar RFID como referencia
                activity_type=SuspiciousActivity.MULTIPLE_FAILED_ATTEMPTS,
                details={
                    'failed_attempts': failed_attempts,
                    'rfid_card': rfid_card,
                    'time_window': '5 minutes'
                },
                severity='high' if failed_attempts >= 5 else 'medium'
            )
            
            db.suspicious_activity.insert_one(suspicious)
            
            return True, "Actividad sospechosa registrada"
        
        return False, "Actividad normal"
