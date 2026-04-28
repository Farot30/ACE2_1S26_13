**VIV MQTT Payload (contrato)**

- **Tópico:** `park-guard/viv/vehicle/type`
- **QoS:** 1
- **Formato:** JSON

Campos obligatorios (VIV envía):

- `event_type`: "viv_vehicle_detected"
- `source`: "viv"
- `vehicle_type`: "car" | "motorcycle"
- `plate_text`: texto leído por OCR (string)
- `timestamp`: ISO 8601 con zona (string)

Notas para el consumidor (backend):

- VIV entrega evidencia y sugerencias; la lógica de negocio (autorización, cobro, apertura de portón) debe decidirse en el backend.
- No asumir que `plate_text` está 100% correcto; validar / normalizar antes de usarlo en acciones críticas.
- Si necesitan más metadatos (confianzas, tarifas, etc.) pueden solicitarlos; actualmente VIV entrega solo los campos mínimos para simplificar la integración.