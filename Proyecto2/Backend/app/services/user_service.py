"""Servicio para gestión de usuarios RFID"""
from bson.objectid import ObjectId
from app import get_db
from app.models import User
from datetime import datetime

class UserService:
    """
    Servicio para lógica de usuarios RFID
    
    Los usuarios son personas que tienen una tarjeta RFID.
    Pueden ser activados/desactivados pero NO tienen credenciales.
    """
    
    @staticmethod
    def create_user(rfid_card, name):
        """
        Crear un nuevo usuario RFID
        
        Args:
            rfid_card: Tarjeta RFID (8 caracteres hex, ej: B91E19B4)
            name: Nombre de la persona
            
        Returns:
            (success: bool, message: str)
        """
        db = get_db()
        
        rfid_upper = rfid_card.upper()
        
        # Verificar si RFID ya existe
        existing_user = db.users.find_one({'rfid_card': rfid_upper})
        if existing_user:
            return False, "Esta tarjeta RFID ya está registrada"
        
        user = User.create(rfid_card=rfid_upper, name=name)
        
        result = db.users.insert_one(user)
        return True, str(result.inserted_id)
    
    @staticmethod
    def get_user_by_id(user_id):
        """Obtener usuario por ID"""
        db = get_db()
        try:
            user = db.users.find_one({'_id': ObjectId(user_id)})
            return User.to_dict(user) if user else None
        except:
            return None
    
    @staticmethod
    def get_user_by_rfid(rfid_card):
        """
        Obtener usuario por tarjeta RFID
        
        Este es el método más importante:
        se usa para validar acceso cuando Arduino envía la tarjeta
        """
        db = get_db()
        user = db.users.find_one({'rfid_card': rfid_card.upper()})
        return User.to_dict(user) if user else None
    
    @staticmethod
    def get_all_users(skip=0, limit=50):
        """Obtener lista de usuarios"""
        db = get_db()
        users = list(db.users.find({}).skip(skip).limit(limit))
        return [User.to_dict(user) for user in users]
    
    @staticmethod
    def update_user(user_id, update_data):
        """
        Actualizar usuario
        
        Solo permite actualizar: name, is_active
        """
        db = get_db()
        
        # Permitir solo campos seguros
        allowed_fields = {'name', 'is_active'}
        update_dict = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not update_dict:
            return False, "No hay campos válidos para actualizar"
        
        update_dict['updated_at'] = datetime.utcnow()
        
        try:
            result = db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_dict}
            )
            
            if result.matched_count == 0:
                return False, "Usuario no encontrado"
            
            return True, "Usuario actualizado"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def activate_user(user_id):
        """Activar un usuario (permitir acceso)"""
        db = get_db()
        try:
            result = db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'is_active': True, 'updated_at': datetime.utcnow()}}
            )
            
            if result.matched_count == 0:
                return False, "Usuario no encontrado"
            
            return True, "Usuario activado"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def deactivate_user(user_id):
        """Desactivar un usuario (bloquear acceso)"""
        db = get_db()
        try:
            result = db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'is_active': False, 'updated_at': datetime.utcnow()}}
            )
            
            if result.matched_count == 0:
                return False, "Usuario no encontrado"
            
            return True, "Usuario desactivado"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def delete_user(user_id):
        """Eliminar usuario"""
        db = get_db()
        try:
            result = db.users.delete_one({'_id': ObjectId(user_id)})
            if result.deleted_count == 0:
                return False, "Usuario no encontrado"
            return True, "Usuario eliminado"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def update_access_stats(user_id):
        """
        Actualizar estadísticas de acceso
        
        Se llama cada vez que un usuario accede exitosamente
        """
        db = get_db()
        
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$inc': {'access_count': 1},
                '$set': {'last_access': datetime.utcnow()}
            }
        )
    
    @staticmethod
    def update_balance(user_id, amount):
        """
        Cargar saldo a un usuario
        
        Args:
            user_id: ID del usuario
            amount: Cantidad a agregar (ej: 100.0)
            
        Returns:
            (success: bool, message: str)
        """
        db = get_db()
        
        try:
            # Verificar que amount es positivo
            if not isinstance(amount, (int, float)) or amount <= 0:
                return False, "La cantidad debe ser un número positivo"
            
            result = db.users.update_one(
                {'_id': ObjectId(user_id)},
                {
                    '$inc': {'balance': float(amount)},
                    '$set': {'updated_at': datetime.utcnow()}
                }
            )
            
            if result.matched_count == 0:
                return False, "Usuario no encontrado"
            
            return True, f"Saldo cargado: +Q{amount}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def reset_balance(user_id, target_balance=5.0):
        """Reiniciar saldo del usuario a un valor fijo (default Q5)."""
        db = get_db()

        try:
            result = db.users.update_one(
                {'_id': ObjectId(user_id)},
                {
                    '$set': {
                        'balance': float(target_balance),
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            if result.matched_count == 0:
                return False, "Usuario no encontrado"

            return True, f"Saldo reiniciado a Q{float(target_balance):.2f}"
        except Exception as e:
            return False, str(e)
