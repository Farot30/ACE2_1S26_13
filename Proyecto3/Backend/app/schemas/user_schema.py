"""Esquemas de validación para usuarios RFID"""

class UserCreateSchema:
    """Esquema para crear usuario RFID"""
    required_fields = ['rfid_card', 'name']
    
    @staticmethod
    def validate(data):
        """Validar datos de entrada"""
        if not isinstance(data, dict):
            return False, "Los datos deben ser un diccionario"
        
        for field in UserCreateSchema.required_fields:
            if field not in data or not data[field]:
                return False, f"Campo requerido: {field}"
        
        # Validar RFID (debe ser hexadecimal, ej: B91E19B4)
        rfid = data.get('rfid_card', '').upper()
        if len(rfid) != 8 or not all(c in '0123456789ABCDEF' for c in rfid):
            return False, "RFID inválido. Debe ser 8 caracteres hexadecimales (ej: B91E19B4)"
        
        # Validar que name no esté vacío
        if len(data.get('name', '').strip()) < 2:
            return False, "El nombre debe tener al menos 2 caracteres"
        
        return True, "Validación exitosa"


class UserUpdateSchema:
    """Esquema para actualizar usuario (solo name y is_active)"""
    
    @staticmethod
    def validate(data):
        """Validar datos de entrada"""
        if not isinstance(data, dict):
            return False, "Los datos deben ser un diccionario"
        
        # Validar campos permitidos
        allowed_fields = {'name', 'is_active'}
        provided_fields = set(data.keys())
        
        invalid_fields = provided_fields - allowed_fields
        if invalid_fields:
            return False, f"Campos no permitidos: {', '.join(invalid_fields)}"
        
        # Validar name si está presente
        if 'name' in data:
            if not isinstance(data['name'], str) or len(data['name'].strip()) < 2:
                return False, "El nombre debe tener al menos 2 caracteres"
        
        # Validar is_active si está presente
        if 'is_active' in data:
            if not isinstance(data['is_active'], bool):
                return False, "is_active debe ser true o false"
        
        return True, "Validación exitosa"
