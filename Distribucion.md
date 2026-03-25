# Park-Guard 2.0 - Continuación del Proyecto

**Estado Actual:** Backend + MongoDB + Mosquitto dockerizado y 100% testeado ✅
- ✅ 11/11 pruebas de testing integral pasadas
- ✅ API REST funcional con 25+ endpoints
- ✅ JWT AuthenticationImplementado
- ✅ MongoDB persistiendo datos
- ✅ WebSocket Socket.IO conectado
- ✅ Comandos MQTT listos

---

## 📋 Distribución de Roles y Responsabilidades

Desde este punto, cada integrante debe enfocarse en su área específica. El backend está completamente funcional; ahora se requiere integrar los demás componentes.

---

## 1. 🖥️ ROLE: BACKEND (Python/Flask)

**Estado:** ✅ COMPLETADO Y COMPLETAMENTE TESTEADO

### Validación Final - Suite de Testing Integral ✅
**Resultados: 11/11 Pruebas Pasadas**

- ✅ Health endpoint respondiendo con estado OK
- ✅ JWT authentication con login y token generation (24h)
- ✅ CRUD usuarios RFID funcionando (3 usuarios en BD)
- ✅ 5 espacios de parqueo inicializados y persistidos
- ✅ Base de datos de eventos accesible
- ✅ Endpoints protegidos retornan 401 sin token
- ✅ Comandos MQTT publicándose correctamente
- ✅ WebSocket Socket.IO conectando sin errores
- ✅ MongoDB persistiendo datos (3 usuarios, 5 espacios)
- ✅ Docker Compose con 3/3 contenedores activos
- ✅ Autenticación y autorización funcionando

**Testing Validado:**
- [x] Probar todos los endpoints REST ✅
- [x] Validar autenticación JWT ✅
- [x] Verificar endpoints protegidos ✅
- [x] Probar CRUD completo usuarios RFID ✅
- [x] Verificar MongoDB persistencia ✅
- [x] Probar WebSocket Socket.IO ✅
- [x] Verificar comandos MQTT ✅

### Endpoints que deben funcionar:
```
POST   /api/auth/register        → Crear admin
POST   /api/auth/login           → Login y obtener JWT
GET    /api/health               → Verificar backend vivo

POST   /api/users                → Crear usuario RFID
GET    /api/users                → Listar usuarios
GET    /api/users/<id>           → Obtener usuario
PUT    /api/users/<id>           → Actualizar usuario
DELETE /api/users/<id>           → Eliminar usuario

GET    /api/parking              → Estado de espacios
PUT    /api/parking/<space>      → Cambiar ocupación
GET    /api/parking/<space>      → Obtener espacio

POST   /api/events               → Registrar evento
GET    /api/events               → Listar eventos filtrados

GET    /api/commands/emergency   → Activar emergencia
GET    /api/commands/ventilator  → Activar ventilador
```

### WebSocket Events
- Validar que Socket.IO eventos se emiten correctamente:
  - `parking_update`
  - `emergency_alert`
  - `ventilator_update`
  - `door_update`
  - `system_status`

---

## 2. 🎨 ROLE: FRONTEND (React/Vue/Angular)

**Estado:** ❌ NO INICIADO

**Responsabilidades:**

### Dashboard 1: Visualización en Tiempo Real
- [ ] Crear componente principal con P5.js
- [ ] Dibujar 5 espacios de parqueo (ocupado/libre)
- [ ] Mostrar nivel de gas en tiempo real
- [ ] Mostrar estado de ventilador (ON/OFF)
- [ ] Mostrar estado de emergencia (ALERTA/NORMAL)
- [ ] Mostrar estado de talanqueras
- [ ] Lista en vivo de últimos 10 eventos
- [ ] Conectar a WebSocket para actualizaciones en tiempo real

```javascript
// Debe suscribirse a eventos:
socket.on('parking_update', (data) => { /* actualizar P5.js */ })
socket.on('emergency_alert', (data) => { /* mostrar alerta */ })
socket.on('ventilator_update', (data) => { /* cambiar estado */ })
socket.on('system_status', (data) => { /* actualizar todo */ })
```

### Dashboard 2: Gestión de Usuarios RFID
- [ ] Formulario para crear usuario (nombre + RFID)
- [ ] Tabla de usuarios con acciones: editar, activar/desactivar, eliminar
- [ ] Historial básico de actividad por usuario
- [ ] Detector de actividad sospechosa (intentos fallidos)
- [ ] Indicador visual de usuarios bloqueados

### Dashboard 3: Estadísticas y Reportes
- [ ] Gráfica de ingresos/salidas (Chart.js o similar)
- [ ] Gráfica de ocupación máxima por hora
- [ ] Contador de emergencias activadas
- [ ] Contador de activaciones de ventilador
- [ ] Botón para generar y descargar PDF con estadísticas

### Panel de Control (todas las vistas)
- [ ] Login obligatorio con JWT
- [ ] Protección de rutas (solo con token válido)
- [ ] Botón para activar ventilador (publica a MQTT)
- [ ] Botón para activar emergencia (publica a MQTT)
- [ ] Botón para habilitar/deshabilitar espacios (publica a MQTT)
- [ ] Logout y gestión de sesión

### Requerimientos Técnicos
- Stack: React, Vue o Angular
- Autenticación: JWT (guardar en localStorage)
- Comunicación: axios/fetch para HTTP, Socket.IO para WebSocket
- Visualización: P5.js para gráfico de parqueo, Chart.js para estadísticas
- Estilos: CSS, Tailwind o Bootstrap (limpio y profesional)

### Estructura de carpetas recomendada
```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx
│   │   ├── Parking.jsx
│   │   ├── Users.jsx
│   │   ├── Statistics.jsx
│   │   └── ...
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Home.jsx
│   │   └── ...
│   ├── services/
│   │   ├── api.js (axios instance)
│   │   ├── socket.js (Socket.IO config)
│   │   └── auth.js
│   ├── hooks/
│   ├── App.jsx
│   └── index.js
├── Dockerfile
├── package.json
└── .dockerignore
```

---

## 3. 📡 ROLE: MQTT / COMUNICACIÓN

**Estado:** ❌ NO INICIADO (infraestructura lista en Docker)

**Responsabilidades:**

### Documentación Formal de Topics MQTT
Crear archivo `MQTT_TOPICS.md` con:

```
park-guard/parking/<space_number>/status
  → Publicador: Arduino/ESP32
  → Payload: {"occupied": true/false}
  
park-guard/parking/<space_number>/command
  → Publicador: Backend/Frontend
  → Payload: {"action": "enable/disable"}
  
park-guard/emergency/trigger
  → Publicador: Arduino/Backend
  → Payload: {"status": "on/off", "timestamp": "..."}
  
park-guard/ventilator/command
  → Publicador: Frontend/Backend
  → Payload: {"action": "on/off"}
  
park-guard/rfid/read
  → Publicador: Arduino/ESP32
  → Payload: {"card_id": "12345678", "timestamp": "..."}
  
park-guard/rfid/validate
  → Publicador: Backend
  → Payload: {"card_id": "12345678", "valid": true/false}
  
park-guard/gas/sensor
  → Publicador: Arduino/ESP32
  → Payload: {"level": 45.2, "unit": "ppm"}
  
park-guard/system/status
  → Publicador: Backend
  → Payload: {"spaces_occupied": 2, "gas_level": 45.2, "emergency": false, ...}
```

### Integración Arduino/ESP32
- [ ] Leer sensores de ocupación (pines digitales)
- [ ] Leer sensor RFID (protocolo UART o SPI)
- [ ] Leer sensor de gas (entrada analógica)
- [ ] Publicar a broker Mosquitto (IP: mosquitto, puerto: 1883)
- [ ] Mostrar en LCD: espacio, gas, estado talanquera
- [ ] Controlar relés para talanqueras

### Consumer en Python
- [ ] Suscribirse a tópicos MQTT
- [ ] Procesar mensajes de eventos (ocupación, RFID)
- [ ] Validar usuarios contra base de datos vía HTTP
- [ ] Registrar eventos en MongoDB
- [ ] Publicar actualizaciones a Backend vía HTTP

### Diagrama de Flujo MQTT
```
Arduino/ESP32 
    ↓ (publish ocupación, RFID, gas)
Mosquitto Broker
    ↓ (subscribe el consumer)
Consumer Python
    ↓ (HTTP POST a backend)
Backend API
    ↓ (registra en MongoDB, emite WebSocket)
MongoDB + Socket.IO
    ↓ (WebSocket a Frontend)
Frontend (React)
    ↓ (visualiza en tiempo real)
```

---

## 4. 🗄️ ROLE: BASE DE DATOS (MongoDB)

**Estado:** ✅ INICIALIZADA (pero vacía)

**Responsabilidades:**

### Validación de Colecciones
- [ ] Verificar que las 6 colecciones existan:
  ```
  db.users                     → Usuarios RFID
  db.parking_spaces            → Espacios de parqueo
  db.events                    → Eventos del sistema
  db.suspicious_activity       → Intentos fallidos
  db.system_logs               → Logs operativos
  db.statistics                → Datos agregados
  ```

### Índices
- [ ] Verificar índices en colecciones (por performance)
  ```
  users: unique index en rfid_card
  events: index en timestamp, user_id, event_type
  parking_spaces: unique index en space_number
  suspicious_activity: index en user_id, timestamp
  ```

### Datos de Prueba
- [ ] Insertar 5 usuarios RFID de ejemplo
  ```json
  {
    "rfid_card": "12345678",
    "name": "Usuario Prueba 1",
    "is_active": true,
    "created_at": "2026-03-10T...",
    "last_access": null
  }
  ```

- [ ] Insertar 5 espacios de parqueo
  ```json
  {
    "space_number": 1,
    "is_occupied": false,
    "is_enabled": true,
    "entry_time": null
  }
  ```

### Monitoreo
- [ ] Escribir script para validar integridad de datos
- [ ] Crear backup regularmente
- [ ] Documentar esquema de cada colección

### Reporte de Base de Datos
Crear archivo `DATABASE_SCHEMA.md` con:
- Estructura completa de cada colección
- Tipos de datos
- Índices definidos
- Relaciones entre colecciones

---

## 5. 🔧 ROLE: MAQUETA (Hardware/Electrónica)

**Estado:** ⚠️ CONEXIÓN PENDIENTE

**Responsabilidades:**

### Componentes Físicos (verificar)
- [ ] 5 espacios de parqueo con estructura clara
- [ ] 1 sensor de ocupación por espacio (IR, ultrasónico o MCU)
- [ ] 1 lector RFID (RC522 u otro) en entrada
- [ ] 1 sensor de gas (MQ-135 o similar)
- [ ] 2 talanqueras automáticas (entrada/salida)
- [ ] 1 buzzer
- [ ] 1 ventilador (controlado por relé)
- [ ] Pantalla LCD (I2C o serial)
- [ ] LEDs indicadores por espacio (libre/ocupado)

### Circuitos Electrónicos
- [ ] Diagrama esquemático actualizado (Fritzing)
  - Conexiones de sensores a microcontrolador
  - Conexiones de relés para actuadores
  - Alimentación (GND y Vcc común)
  
- [ ] Verificar polaridades de:
  - Sensor RFID
  - Motor de talanquera
  - Ventilador
  - Buzzer
  - LEDs

### Microcontrolador (Arduino/ESP32)
- [ ] Instalar librerías necesarias:
  ```
  PubSubClient          (MQTT)
  MFRC522               (RFID)
  LiquidCrystal_I2C     (LCD)
  DHT                   (sensor gas)
  ```

- [ ] Programación del firmware
  ```cpp
  // Conexión a WiFi (si ESP32)
  
  // Conexión a Mosquitto
  client.setServer("mosquitto", 1883);
  
  // Leer sensores en loop
  // Publicar si hay cambios
  // Suscribirse a comandos
  ```

- [ ] Test de cada sensor individualmente

### Integración con Sistema
- [ ] Arduino conectado a red Docker
- [ ] Publicar estados a topics MQTT correctamente
- [ ] Recibir y ejecutar comandos (ventilador, talanquera)
- [ ] Mostrar estado en LCD en tiempo real
- [ ] LEDs sincronizados con estado en base de datos

### Documentación Hardware
Crear archivo `HARDWARE_SETUP.md` con:
- Lista de componentes
- Diagrama esquemático
- Pins utilizados
- Calibración de sensores
- Instrucciones de armado
- Troubleshooting común

---

## 📅 Timeline Estimado (desde ahora)

| Semana | Hito | Responsable |
|--------|------|-------------|
| Semana 1 | Frontend dashboard + MQTT topics doc | Frontend, MQTT, DB |
| Semana 2 | Consumer Python + Arduino firmware | MQTT, Maqueta |
| Semana 3 | Integración completa + testing | Todos |
| Semana 3 (final) | Presentación + Commits a GitHub | Todos |

---

## 🔗 Integración Esperada

```
[Hardware] → [Mosquitto] → [Consumer] ↓
                              ↓
                         [Backend API] ← [JWT Auth]
                              ↓
                         [MongoDB] ← [Queries]
                              ↓
                         [WebSocket]
                              ↓
                         [Frontend React]
```

---

## ✅ Checklist Pre-Entrega

- [x] Backend respondiendo todos los endpoints
- [ ] Frontend con 3 dashboards funcionales
- [ ] MQTT topics documentados y funcionando
- [ ] Consumer procesando eventos correctamente
- [x] MongoDB con datos de prueba ✅ (3 usuarios, 5 espacios)
- [ ] Hardware publicando datos a MQTT
- [x] Docker Compose levanta todo en 1 comando ✅
- [ ] Imágenes publicadas en Docker Hub
- [ ] Repositorio con mínimo 2 commits por persona
- [ ] Documentación técnica completa
- [ ] Manual de usuario claro

---

## 📞 Referencias Rápidas

**Backend corriendo en:**
- API REST: `http://localhost:5000/api/*`
- WebSocket: `ws://localhost:5000/socket.io`
- Documentación en: `Instrucciones.md`

**Mosquitto corriendo en:**
- Host: `mosquitto` (desde Docker)
- Puerto: `1883`

**MongoDB corriendo en:**
- Host: `mongodb` (desde Docker)
- URI: `mongodb://park_user:park_password@mongodb:27017/park_guard?authSource=admin`

**Frontend debe correr en puerto:** `3000` (cualquier framework)

**Consumer Python debe conectarse a:** Backend (`http://backend:5000`) y Mosquitto (`mosquitto:1883`)

