# Exportar todos los modelos
from app.models.user import User
from app.models.parking_space import ParkingSpace
from app.models.event import Event
from app.models.suspicious_activity import SuspiciousActivity
from app.models.system_log import SystemLog
from app.models.admin import Admin

__all__ = [
    'User',
    'ParkingSpace',
    'Event',
    'SuspiciousActivity',
    'SystemLog',
    'Admin'
]
