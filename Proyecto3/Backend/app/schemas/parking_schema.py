"""Esquemas de validación para espacios de parqueo"""

class ParkingSpaceSchema:
    """Esquema para espacios de parqueo"""
    
    @staticmethod
    def validate(data):
        """Validar datos de entrada"""
        if not isinstance(data, dict):
            return False, "Los datos deben ser un diccionario"
        
        if 'space_number' in data:
            space_num = data.get('space_number')
            if not isinstance(space_num, int) or space_num < 1 or space_num > 5:
                return False, "Número de espacio debe estar entre 1 y 5"
        
        if 'is_enabled' in data:
            if not isinstance(data.get('is_enabled'), bool):
                return False, "is_enabled debe ser booleano"
        
        return True, "Validación exitosa"


class AccessValidationSchema:
    """Esquema para validación de acceso RFID"""
    required_fields = ['rfid_card']
    
    @staticmethod
    def validate(data):
        """Validar datos de entrada"""
        if not isinstance(data, dict):
            return False, "Los datos deben ser un diccionario"
        
        for field in AccessValidationSchema.required_fields:
            if field not in data or not data[field]:
                return False, f"Campo requerido: {field}"
        
        # Validar RFID
        rfid = data.get('rfid_card', '').upper()
        if len(rfid) != 8 or not all(c in '0123456789ABCDEF' for c in rfid):
            return False, "RFID inválido"
        
        return True, "Validación exitosa"
