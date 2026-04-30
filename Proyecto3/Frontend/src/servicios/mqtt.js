import mqtt from 'mqtt'

let clienteMqttSingleton = null

function obtenerUrlMqttPorDefecto() {
  if (typeof window === 'undefined') {
    return 'ws://localhost:9001'
  }
  const protocolo = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocolo}//${window.location.hostname}:9001`
}

function normalizarTopico(topico = '') {
  return topico.startsWith('/') ? topico.slice(1) : topico
}

function convertirTopicoAEvento(topicoOriginal, payload) {
  const topico = normalizarTopico(topicoOriginal)

  // Ocupación de parqueos
  if (/^park-guard\/parking\/\d+\/status$/.test(topico)) {
    return {
      evento: 'parking_update',
      dato: {
        space_number: Number(payload.space),
        is_occupied: Boolean(payload.is_occupied),
        timestamp: payload.timestamp,
      },
    }
  }

  // Sensor de gas
  if (topico === 'park-guard/gas/sensor') {
    return {
      evento: 'gas_update',
      dato: {
        ppm: payload.ppm,
        timestamp: payload.timestamp,
      },
    }
  }

  // Lectura RFID (en vivo)
  if (topico === 'park-guard/rfid/read') {
    return {
      evento: 'rfid_read',
      dato: {
        card_id: payload.card_id,
        timestamp: payload.timestamp,
      },
    }
  }

  // Activación manual/auto de ventilador (desde Arduino)
  if (topico === 'park-guard/ventilator/command') {
    return {
      evento: 'ventilator_update',
      dato: {
        is_active: Boolean(payload.is_active),
        gas_level: payload.gas_level,
        timestamp: payload.timestamp,
      },
    }
  }

  // Disparo de emergencia (desde Arduino)
  if (topico === 'park-guard/emergency/trigger') {
    return {
      evento: 'emergency_alert',
      dato: {
        alert_type: payload.type || 'system',
        timestamp: payload.timestamp,
        is_active: true,
      },
    }
  }

  // Estado de puertas (desde Arduino)
  if (topico === 'park-guard/doors/entrance/status' || topico === 'park-guard/doors/exit/status') {
    const door = payload.door || (topico.includes('entrance') ? 'entrance' : 'exit')
    return {
      evento: 'door_update',
      dato: {
        door: door,
        is_open: Boolean(payload.is_open),
        timestamp: payload.timestamp,
      },
    }
  }

  // Comandos de ventilador (desde Backend/Admin)
  if (topico === 'park-guard/commands/fan') {
    return {
      evento: 'ventilator_update',
      dato: {
        is_active: payload.command === 'activate_fan',
        timestamp: payload.timestamp,
      },
    }
  }

  // Comandos de emergencia (desde Backend/Admin)
  if (topico === 'park-guard/commands/emergency') {
    const activada = payload.command === 'activate_emergency'
    return {
      evento: activada ? 'emergency_alert' : 'system_status',
      dato: activada
        ? {
            alert_type: 'manual',
            timestamp: payload.timestamp,
            is_active: true,
          }
        : {
            status: { emergency: false },
            timestamp: payload.timestamp,
          },
    }
  }

  // Comandos de puertas (desde Backend/Admin)
  if (topico === 'park-guard/commands/door/entrance' || topico === 'park-guard/commands/door/exit') {
    const door = payload.door || (topico.includes('entrance') ? 'entrance' : 'exit')
    return {
      evento: 'door_update',
      dato: {
        door: door,
        is_open: payload.command === 'open_door',
        timestamp: payload.timestamp,
      },
    }
  }

  // Comandos de espacios de parqueo (desde Backend/Admin)
  if (topico === 'park-guard/commands/parking/space') {
    return {
      evento: 'parking_status_update',
      dato: {
        space_number: Number(payload.space),
        is_enabled: payload.command === 'enable_space',
        timestamp: payload.timestamp,
      },
    }
  }

  // Detección VIV (Visión)
  if (topico === 'park-guard/viv/vehicle/type' || topico === 'park-guard/viv/vehiculos') {
    return {
      evento: 'viv_detection',
      dato: {
        vehicle_type: payload.vehicle_type,
        plate_text: payload.plate_text,
        fee_quetzales: payload.fee_quetzales,
        timestamp: payload.timestamp,
        source: payload.source || 'viv'
      },
    }
  }

  return null
}

function crearClienteMqtt() {
  const manejadores = new Map()
  let conectado = false

  const cliente = mqtt.connect(import.meta.env.VITE_MQTT_URL || obtenerUrlMqttPorDefecto(), {
    reconnectPeriod: 1000,
    connectTimeout: 10_000,
    clean: true,
  })

  function emitirInterno(evento, dato) {
    const lista = manejadores.get(evento)
    if (!lista) return
    lista.forEach((callback) => callback(dato))
  }

  cliente.on('connect', () => {
    conectado = true
    emitirInterno('connect')
  })

  cliente.on('close', () => {
    conectado = false
  })

  cliente.on('message', (topico, mensaje) => {
    try {
      const payload = JSON.parse(mensaje.toString())
      const conversion = convertirTopicoAEvento(topico, payload)
      if (conversion) {
        emitirInterno(conversion.evento, conversion.dato)
      }
    } catch {
      // ignorar mensajes inválidos
    }
  })

  cliente.on('error', (error) => {
    emitirInterno('error', error)
  })

  return {
    on(evento, callback) {
      if (!manejadores.has(evento)) {
        manejadores.set(evento, new Set())
      }
      manejadores.get(evento).add(callback)

      if (evento === 'connect' && conectado) {
        callback()
      }
    },
    off(evento, callback) {
      const lista = manejadores.get(evento)
      if (!lista) return
      lista.delete(callback)
      if (lista.size === 0) manejadores.delete(evento)
    },
    emit(evento, payload = {}) {
      if (evento === 'subscribe_parking') {
        const topicos = [
          'park-guard/parking/+/status',
          'park-guard/gas/sensor',
          'park-guard/rfid/read',
          'park-guard/emergency/trigger',
          'park-guard/ventilator/command',
          'park-guard/doors/+/status',
          'park-guard/commands/fan',
          'park-guard/commands/emergency',
          'park-guard/commands/door/+',
          'park-guard/viv/+',
          '/park-guard/commands/fan',
          '/park-guard/commands/emergency',
          '/park-guard/commands/door/+',
        ]
        topicos.forEach((topico) => {
          cliente.subscribe(topico, { qos: 1 })
        })
        return
      }

      if (evento === 'publish_command') {
        const topico = payload?.topic
        if (!topico) return
        const cuerpo = payload?.payload || {}
        cliente.publish(topico, JSON.stringify(cuerpo), { qos: 1 })
      }
    },
    disconnect() {
      cliente.end(true)
      manejadores.clear()
    },
  }
}

export function conectarMqtt() {
  if (!clienteMqttSingleton) {
    clienteMqttSingleton = crearClienteMqtt()
  }
  return clienteMqttSingleton
}

export function desconectarMqtt() {
  if (clienteMqttSingleton) {
    clienteMqttSingleton.disconnect()
    clienteMqttSingleton = null
  }
}