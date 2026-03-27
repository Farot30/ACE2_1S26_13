"""Servicio para gestión de espacios de parqueo"""
from bson.objectid import ObjectId
from app import get_db
from app.models import ParkingSpace, Event
from datetime import datetime
from app.services.mqtt_service import MQTTService

class ParkingService:
    """Servicio para lógica de espacios de parqueo"""
    
    @staticmethod
    def initialize_parking_spaces():
        """Inicializar los 5 espacios de parqueo"""
        db = get_db()
        
        # Verificar si ya existen
        count = db.parking_spaces.count_documents({})
        if count > 0:
            return True, "Espacios ya inicializados"
        
        try:
            spaces = []
            for i in range(1, 6):
                space = ParkingSpace.create(space_number=i)
                spaces.append(space)
            
            db.parking_spaces.insert_many(spaces)
            return True, "Espacios de parqueo inicializados"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_all_spaces():
        """Obtener todos los espacios"""
        db = get_db()
        spaces = list(db.parking_spaces.find({}).sort('space_number', 1))
        return [ParkingSpace.to_dict(space) for space in spaces]
    
    @staticmethod
    def get_space_by_number(space_number):
        """Obtener espacio por número"""
        db = get_db()
        space = db.parking_spaces.find_one({'space_number': space_number})
        return ParkingSpace.to_dict(space) if space else None
    
    @staticmethod
    def get_available_spaces():
        """Obtener cantidad de espacios disponibles"""
        db = get_db()
        available = db.parking_spaces.count_documents({
            'is_occupied': False,
            'is_enabled': True
        })
        return available
    
    @staticmethod
    def occupy_space(space_number, user_id):
        """Marcar espacio como ocupado"""
        db = get_db()
        
        try:
            result = db.parking_spaces.update_one(
                {'space_number': space_number},
                {
                    '$set': {
                        'is_occupied': True,
                        'current_user_id': ObjectId(user_id),
                        'entry_time': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.matched_count == 0:
                return False, "Espacio no encontrado"
            
            # Registrar evento
            event = Event.create(
                event_type=Event.SPACE_OCCUPIED,
                space_id=space_number,
                user_id=ObjectId(user_id),
                description=f"Espacio {space_number} ocupado"
            )
            db.events.insert_one(event)
            
            return True, "Espacio ocupado"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def vacate_space(space_number):
        """Marcar espacio como desocupado"""
        db = get_db()
        
        try:
            space = db.parking_spaces.find_one({'space_number': space_number})
            
            result = db.parking_spaces.update_one(
                {'space_number': space_number},
                {
                    '$set': {
                        'is_occupied': False,
                        'current_user_id': None,
                        'exit_time': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.matched_count == 0:
                return False, "Espacio no encontrado"
            
            # Registrar evento
            event = Event.create(
                event_type=Event.SPACE_EMPTY,
                space_id=space_number,
                description=f"Espacio {space_number} desocupado"
            )
            db.events.insert_one(event)
            
            return True, "Espacio desocupado"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def enable_space(space_number):
        """Habilitar un espacio"""
        db = get_db()
        
        try:
            result = db.parking_spaces.update_one(
                {'space_number': space_number},
                {'$set': {'is_enabled': True}}
            )
            
            if result.matched_count == 0:
                return False, "Espacio no encontrado"
            
            # Registrar evento
            event = Event.create(
                event_type=Event.SPACE_ENABLED,
                space_id=space_number,
                description=f"Espacio {space_number} habilitado"
            )
            db.events.insert_one(event)

            try:
                mqtt = MQTTService()
                mqtt.publish(
                    f"/park-guard/commands/barrier/{space_number}",
                    {
                        'command': 'open_barrier',
                        'space': space_number,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    qos=1
                )
            except Exception:
                pass
            
            return True, "Espacio habilitado"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def disable_space(space_number):
        """Deshabilitar un espacio"""
        db = get_db()
        
        try:
            result = db.parking_spaces.update_one(
                {'space_number': space_number},
                {'$set': {'is_enabled': False}}
            )
            
            if result.matched_count == 0:
                return False, "Espacio no encontrado"
            
            # Registrar evento
            event = Event.create(
                event_type=Event.SPACE_DISABLED,
                space_id=space_number,
                description=f"Espacio {space_number} deshabilitado"
            )
            db.events.insert_one(event)

            try:
                mqtt = MQTTService()
                mqtt.publish(
                    f"/park-guard/commands/barrier/{space_number}",
                    {
                        'command': 'close_barrier',
                        'space': space_number,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    qos=1
                )
            except Exception:
                pass
            
            return True, "Espacio deshabilitado"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def update_space_occupancy_with_websocket(space_number, is_occupied, user_id=None):
        """
        Actualizar ocupación de espacio y emitir evento WebSocket
        
        Args:
            space_number: Número del espacio (1-5)
            is_occupied: Nuevo estado de ocupación
            user_id: ID del usuario (si es ocupado)
        
        Returns:
            Tupla (success, message)
        """
        try:
            # Actualizar ocupación
            if is_occupied:
                success, message = ParkingService.occupy_space(space_number, user_id)
            else:
                success, message = ParkingService.vacate_space(space_number)
            
            if success:
                # Emitir evento WebSocket
                try:
                    from app import get_socketio
                    from app.websocket import emit_parking_update
                    
                    socketio = get_socketio()
                    emit_parking_update(socketio, space_number, is_occupied)
                except RuntimeError:
                    # SocketIO no inicializado aún (por ejemplo, en init)
                    pass
                except ImportError:
                    # Evitar error si los módulos no están listos
                    pass
            
            return success, message
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def broadcast_parking_status():
        """
        Emitir estado actual de todos los espacios
        Útil para sincronizar con nuevos clientes WebSocket
        """
        try:
            from app import get_socketio
            from app.websocket import emit_parking_update
            
            socketio = get_socketio()
            spaces = ParkingService.get_all_spaces()
            
            for space in spaces:
                emit_parking_update(
                    socketio,
                    space['space_number'],
                    space['is_occupied']
                )
            
            return True, "Estado de parqueo transmitido"
        except Exception as e:
            return False, str(e)
