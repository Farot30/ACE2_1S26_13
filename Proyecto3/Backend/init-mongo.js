// Inicialización de MongoDB para Park-Guard
// El usuario root (park_user) se crea automáticamente con MONGO_INITDB_ROOT_USERNAME/PASSWORD
// Este script solo crea las colecciones necesarias

// Cambiar a la BD park_guard (ya está autenticado como root)
db = db.getSiblingDB('park_guard');

// Crear colecciones
try {
  db.createCollection('users');
  db.users.createIndex({ 'rfid_card': 1 }, { unique: true });
  db.users.createIndex({ 'created_at': 1 });
  print('✓ Colección users creada');
} catch (err) {
  print('⚠ ' + err);
}

try {
  db.createCollection('parking_spaces');
  db.parking_spaces.createIndex({ 'space_number': 1 }, { unique: true });
  print('✓ Colección parking_spaces creada');
} catch (err) {
  print('⚠ ' + err);
}

try {
  db.createCollection('events');
  db.events.createIndex({ 'timestamp': 1 });
  db.events.createIndex({ 'user_id': 1 });
  db.events.createIndex({ 'event_type': 1 });
  print('✓ Colección events creada');
} catch (err) {
  print('⚠ ' + err);
}

try {
  db.createCollection('suspicious_activity');
  db.suspicious_activity.createIndex({ 'user_id': 1 });
  db.suspicious_activity.createIndex({ 'timestamp': 1 });
  print('✓ Colección suspicious_activity creada');
} catch (err) {
  print('⚠ ' + err);
}

try {
  db.createCollection('system_logs');
  db.system_logs.createIndex({ 'timestamp': 1 });
  db.system_logs.createIndex({ 'level': 1 });
  print('✓ Colección system_logs creada');
} catch (err) {
  print('⚠ ' + err);
}

try {
  db.createCollection('statistics');
  db.statistics.createIndex({ 'date': 1 });
  print('✓ Colección statistics creada');
} catch (err) {
  print('⚠ ' + err);
}

try {
  db.createCollection('admins');
  db.admins.createIndex({ 'email': 1 }, { unique: true });
  print('✓ Colección admins creada');
} catch (err) {
  print('⚠ ' + err);
}

// Colección para registros VIV específicos
try {
  db.createCollection('registros_viv');
  db.registros_viv.createIndex({ 'plate_text': 1 });
  db.registros_viv.createIndex({ 'timestamp': 1 });
  print('✓ Colección registros_viv creada');
} catch (err) {
  print('⚠ ' + err);
}

// Colección de vehículos (placa vinculada a usuario)
try {
  db.createCollection('vehiculos');
  db.vehiculos.createIndex({ 'plate_text': 1 }, { unique: true });
  db.vehiculos.createIndex({ 'usuario_id': 1 });
  db.vehiculos.createIndex({ 'rfid_card': 1 });
  print('✓ Colección vehiculos creada');
} catch (err) {
  print('⚠ ' + err);
}

// Colección de registros entrada/salida
try {
  db.createCollection('registros_entrada_salida');
  db.registros_entrada_salida.createIndex({ 'plate_text': 1 });
  db.registros_entrada_salida.createIndex({ 'timestamp_entrada': 1 });
  db.registros_entrada_salida.createIndex({ 'usuario_id': 1 });
  print('✓ Colección registros_entrada_salida creada');
} catch (err) {
  print('⚠ ' + err);
}

// Colección de operadores/usuarios
try {
  db.createCollection('operadores');
  db.operadores.createIndex({ 'email': 1 }, { unique: true });
  db.operadores.createIndex({ 'activo': 1 });
  print('✓ Colección operadores creada');
} catch (err) {
  print('⚠ ' + err);
}

print('✓ Base de datos Park-Guard inicializada correctamente');
