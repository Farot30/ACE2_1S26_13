# Exportar esquemas
from app.schemas.user_schema import UserCreateSchema, UserUpdateSchema
from app.schemas.parking_schema import ParkingSpaceSchema, AccessValidationSchema
from app.schemas.auth_schema import LoginSchema, RegisterSchema

__all__ = [
    'UserCreateSchema',
    'UserUpdateSchema',
    'ParkingSpaceSchema',
    'AccessValidationSchema',
    'LoginSchema',
    'RegisterSchema'
]
