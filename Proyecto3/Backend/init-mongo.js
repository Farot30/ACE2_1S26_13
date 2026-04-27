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

print('✓ Base de datos Park-Guard inicializada correctamente');
