"""Esquemas de validación para autenticación"""

class LoginSchema:
    """Esquema para login"""
    required_fields = ['email', 'password']
    
    @staticmethod
    def validate(data):
        """Validar datos de entrada"""
        if not isinstance(data, dict):
            return False, "Los datos deben ser un diccionario"
        
        for field in LoginSchema.required_fields:
            if field not in data or not data[field]:
                return False, f"Campo requerido: {field}"
        
        return True, "Validación exitosa"


class RegisterSchema:
    """Esquema para registro de administrador"""
    required_fields = ['email', 'name', 'password']
    
    @staticmethod
    def validate(data):
        """Validar datos de entrada"""
        if not isinstance(data, dict):
            return False, "Los datos deben ser un diccionario"
        
        for field in RegisterSchema.required_fields:
            if field not in data or not data[field]:
                return False, f"Campo requerido: {field}"
        
        if len(data.get('password', '')) < 3:
            return False, "Contraseña debe tener al menos 3 caracteres"
        
        return True, "Validación exitosa"
