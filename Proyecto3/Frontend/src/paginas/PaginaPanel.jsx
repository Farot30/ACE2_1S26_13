import { useEffect, useMemo, useState } from 'react'
import { Bar, Doughnut } from 'react-chartjs-2'
import {
  Chart as Grafica,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'
import BarraPestanas from '../componentes/BarraPestanas'
import TarjetaMetrica from '../componentes/TarjetaMetrica'
import LienzoParqueo from '../componentes/LienzoParqueo'
import { solicitarApi } from '../servicios/api'
import { cerrarSesion, esSesionPrueba } from '../servicios/autenticacion'
import { conectarMqtt, desconectarMqtt } from '../servicios/mqtt'
import { formatearFecha } from '../utilidades/fechas'
import { exportarReporte } from '../utilidades/reporte'
import clienteApi from '../servicios/api'

Grafica.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend)

function PaginaPanel() {
  const [pestanaActiva, setPestanaActiva] = useState('tiempo_real')
  const [espacios, setEspacios] = useState([])
  const [usuarios, setUsuarios] = useState([])
  const [eventos, setEventos] = useState([])
  const [resumen, setResumen] = useState(null)
  const [nivelGas, setNivelGas] = useState(null)
  const [estadoVentilador, setEstadoVentilador] = useState(false)
  const [estadoEmergencia, setEstadoEmergencia] = useState(false)
  const [estadoTalanqueraEntrada, setEstadoTalanqueraEntrada] = useState(false)
  const [estadoTalanqueraSalida, setEstadoTalanqueraSalida] = useState(false)
  const [cargando, setCargando] = useState(true)
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')
  const [usuarioSeleccionado, setUsuarioSeleccionado] = useState('')
  const [historialUsuario, setHistorialUsuario] = useState([])
  const [nombreNuevo, setNombreNuevo] = useState('')
  const [tarjetaNueva, setTarjetaNueva] = useState('')
  const [usuarioParaSaldo, setUsuarioParaSaldo] = useState(null)
  const [montoSaldo, setMontoSaldo] = useState('')
  const [deteccionesViv, setDeteccionesViv] = useState([])
  const [imagenPlacaUrl, setImagenPlacaUrl] = useState('')

  const nombreAdmin = localStorage.getItem('admin_nombre') || 'admin'

  function normalizarEspacios(lista = []) {
    const mapa = new Map()
    lista.forEach((item) => {
      const numero = Number(item.space_number)
      if (!Number.isInteger(numero) || numero < 1 || numero > 5) return
      const previo = mapa.get(numero)
      if (!previo) {
        mapa.set(numero, { ...item, space_number: numero })
        return
      }
      const previoTs = new Date(previo.last_updated || 0).getTime()
      const actualTs = new Date(item.last_updated || 0).getTime()
      if (actualTs >= previoTs) {
        mapa.set(numero, { ...item, space_number: numero })
      }
    })
    return Array.from(mapa.values()).sort((a, b) => a.space_number - b.space_number)
  }

  useEffect(() => {
    cargarDatosIniciales()
  }, [])

  useEffect(() => {
    if (pestanaActiva !== 'viv' || esSesionPrueba()) return

    const cargarViv = async () => {
      try {
        const respuesta = await solicitarApi('get', '/api/viv/detecciones', undefined, { limit: 30, dias: 7 })
        setDeteccionesViv(respuesta.data || [])
      } catch {
        setDeteccionesViv([])
      }

      const token = localStorage.getItem('token')
      if (!token) return
      const base = clienteApi.defaults.baseURL || ''
      const ts = Date.now()
      setImagenPlacaUrl(`${base}/api/viv/placa-imagen?ts=${ts}`)
    }

    cargarViv()
    const intervalo = setInterval(cargarViv, 6000)
    return () => clearInterval(intervalo)
  }, [pestanaActiva])

  useEffect(() => {
    const clienteMqtt = conectarMqtt()

    clienteMqtt.on('connect', () => {
      clienteMqtt.emit('subscribe_parking', { canal: 'parking-updates' })
    })

    const handleParkingUpdate = (dato) => {
      setEspacios((anterior) => {
        const numero = Number(dato.space_number)
        const actualizados = anterior.map((espacio) =>
          espacio.space_number === numero
            ? { ...espacio, is_occupied: dato.is_occupied, last_updated: dato.timestamp }
            : espacio,
        )
        if (!actualizados.some((espacio) => espacio.space_number === numero)) {
          actualizados.push({
            id: `live-${numero}`,
            space_number: numero,
            is_occupied: Boolean(dato.is_occupied),
            is_enabled: true,
            last_updated: dato.timestamp,
          })
        }
        return normalizarEspacios(actualizados)
      })
      insertarEventoEnVivo({
        event_type: 'parking_update',
        description: `espacio ${dato.space_number} actualizado`,
        timestamp: dato.timestamp,
      })
    }

    const handleGasUpdate = (dato) => {
      if (dato.ppm !== null && dato.ppm !== undefined) {
        setNivelGas(dato.ppm)
      }
      insertarEventoEnVivo({
        event_type: 'gas_update',
        description: `nivel de gas actualizado a ${dato.ppm} ppm`,
        timestamp: dato.timestamp,
      })
    }

    const handleVentilatorUpdate = (dato) => {
      setEstadoVentilador(Boolean(dato.is_active))
      if (dato.gas_level !== null && dato.gas_level !== undefined) {
        setNivelGas(dato.gas_level)
      }
      insertarEventoEnVivo({
        event_type: 'fan_update',
        description: `ventilador ${dato.is_active ? 'encendido' : 'apagado'}`,
        timestamp: dato.timestamp,
      })
    }

    const handleDoorUpdate = (dato) => {
      if (dato.door === 'entrance') {
        setEstadoTalanqueraEntrada(Boolean(dato.is_open))
      } else if (dato.door === 'exit') {
        setEstadoTalanqueraSalida(Boolean(dato.is_open))
      }
      insertarEventoEnVivo({
        event_type: 'door_update',
        description: `talanquera ${dato.door === 'entrance' ? 'entrada' : 'salida'} ${dato.is_open ? 'abierta' : 'cerrada'}`,
        timestamp: dato.timestamp,
      })
    }

    const handleEmergencyAlert = (dato) => {
      const activa = typeof dato.is_active === 'boolean' ? dato.is_active : true
      setEstadoEmergencia(activa)
      insertarEventoEnVivo({
        event_type: activa ? 'emergency_alert' : 'emergency_cleared',
        description: activa
          ? `alerta ${dato.alert_type || 'emergencia'} en ${dato.location || 'zona general'}`
          : 'alerta de emergencia desactivada',
        timestamp: dato.timestamp,
      })

      if (activa) {
        setResumen((prev) => {
          if (!prev) return prev
          return {
            ...prev,
            events: {
              ...prev.events,
              emergencies_today: (prev.events?.emergencies_today || 0) + 1
            }
          }
        })
      }
    }

    const handleAccessUpdate = (dato) => {
      const tipo = dato.granted ? 'access_granted' : 'access_denied'
      insertarEventoEnVivo({
        event_type: tipo,
        description: `${dato.granted ? 'acceso concedido' : 'acceso denegado'} a ${dato.user_name || 'desconocido'}`,
        timestamp: dato.timestamp,
        data: { rfid_card: dato.card_id }
      })

      setResumen((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          events: {
            ...prev.events,
            access_granted_today: dato.granted 
              ? (prev.events?.access_granted_today || 0) + 1 
              : (prev.events?.access_granted_today || 0),
            access_denied_today: !dato.granted 
              ? (prev.events?.access_denied_today || 0) + 1 
              : (prev.events?.access_denied_today || 0)
          }
        }
      })
    }

    const handleVivDetection = (dato) => {
      insertarEventoEnVivo({
        event_type: 'viv_detection',
        description: `vehículo detectado: ${dato.vehicle_type} (${dato.plate_text})`,
        timestamp: dato.timestamp,
        source: 'viv'
      })
      setResumen((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          events: {
            ...prev.events,
            access_granted_today: (prev.events?.access_granted_today || 0) + 1
          }
        }
      })
    }

    const handleSystemStatus = (dato) => {
      const estado = dato.status || {}
      if (typeof estado.gas_level === 'number') setNivelGas(estado.gas_level)
      if (typeof estado.emergency === 'boolean') setEstadoEmergencia(estado.emergency)
      if (typeof estado.fan_active === 'boolean') setEstadoVentilador(estado.fan_active)
      insertarEventoEnVivo({
        event_type: 'system_status',
        description: 'estado general actualizado',
        timestamp: dato.timestamp,
      })
    }

    const handleRfidRead = (dato) => {
      if (dato.card_id) {
        setTarjetaNueva(dato.card_id.toUpperCase())
        setMensaje(`tarjeta detectada: ${dato.card_id}`)
        setTimeout(() => setMensaje(''), 3000)
      }
    }

    clienteMqtt.on('parking_update', handleParkingUpdate)
    clienteMqtt.on('gas_update', handleGasUpdate)
    clienteMqtt.on('ventilator_update', handleVentilatorUpdate)
    clienteMqtt.on('door_update', handleDoorUpdate)
    clienteMqtt.on('emergency_alert', handleEmergencyAlert)
    clienteMqtt.on('system_status', handleSystemStatus)
    clienteMqtt.on('access_update', handleAccessUpdate)
    clienteMqtt.on('viv_detection', handleVivDetection)
    clienteMqtt.on('rfid_read', handleRfidRead)

    return () => {
      clienteMqtt.off('parking_update', handleParkingUpdate)
      clienteMqtt.off('gas_update', handleGasUpdate)
      clienteMqtt.off('ventilator_update', handleVentilatorUpdate)
      clienteMqtt.off('door_update', handleDoorUpdate)
      clienteMqtt.off('emergency_alert', handleEmergencyAlert)
      clienteMqtt.off('system_status', handleSystemStatus)
      clienteMqtt.off('access_update', handleAccessUpdate)
      clienteMqtt.off('viv_detection', handleVivDetection)
      clienteMqtt.off('rfid_read', handleRfidRead)
      desconectarMqtt()
    }
  }, [])

  async function cargarDatosIniciales() {
    setCargando(true)
    setError('')
    try {
      if (esSesionPrueba()) {
        const espaciosPrueba = [1, 2, 3, 4, 5].map((numero) => ({
          id: `dev-${numero}`,
          space_number: numero,
          is_occupied: false,
          is_enabled: true,
        }))
        setEspacios(espaciosPrueba)
        setUsuarios([])
        setEventos([])
        setResumen(null)
        setMensaje('modo prueba activo')
        return
      }

      const [respuestaEspacios, respuestaUsuarios, respuestaEventos, respuestaResumen] = await Promise.all([
        solicitarApi('get', '/api/parking/spaces'),
        solicitarApi('get', '/api/users', undefined, { limit: 200 }),
        solicitarApi('get', '/api/events', undefined, { limit: 120 }),
        solicitarApi('get', '/api/events/summary'),
      ])

      setEspacios(normalizarEspacios(respuestaEspacios.data || []))
      setUsuarios(respuestaUsuarios.data || [])
      setEventos(respuestaEventos.data || [])
      setResumen(respuestaResumen.data || null)
      setMensaje('datos actualizados')
    } catch (errorPeticion) {
      const codigo = errorPeticion?.response?.status
      if (codigo === 401 && !esSesionPrueba()) {
        cerrarSesion()
        window.location.href = '/ingreso'
        return
      }
      setError((errorPeticion?.response?.data?.message || 'error cargando informacion').toLowerCase())
    } finally {
      setCargando(false)
      setTimeout(() => setMensaje(''), 2000)
    }
  }

  function insertarEventoEnVivo(eventoNuevo) {
    setEventos((anterior) => [eventoNuevo, ...anterior].slice(0, 120))
  }

  async function crearUsuario(evento) {
    evento.preventDefault()
    setError('')
    try {
      // Limpiar y formatear los datos antes de enviar
      const nombreLimpio = nombreNuevo.trim()
      const rfidLimpio = tarjetaNueva.trim().replace(/\s/g, '').toUpperCase()
      
      if (rfidLimpio.length !== 8) {
        setError('la tarjeta rfid debe tener exactamente 8 caracteres')
        return
      }

      await solicitarApi('post', '/api/users', {
        name: nombreLimpio,
        rfid_card: rfidLimpio,
      })
      setNombreNuevo('')
      setTarjetaNueva('')
      setMensaje('usuario creado exitosamente')
      await cargarDatosIniciales()
    } catch (errorPeticion) {
      const msj = errorPeticion?.response?.data?.message || 'no se pudo crear usuario'
      setError(msj.toLowerCase())
    }
  }

  async function cambiarEstadoUsuario(idUsuario, activo) {
    setError('')
    try {
      const ruta = activo ? `/api/users/${idUsuario}/deactivate` : `/api/users/${idUsuario}/activate`
      await solicitarApi('patch', ruta)
      await cargarDatosIniciales()
    } catch (errorPeticion) {
      setError((errorPeticion?.response?.data?.message || 'no se pudo actualizar usuario').toLowerCase())
    }
  }

  async function eliminarUsuario(idUsuario) {
    setError('')
    try {
      await solicitarApi('delete', `/api/users/${idUsuario}`)
      if (usuarioSeleccionado === idUsuario) {
        setUsuarioSeleccionado('')
        setHistorialUsuario([])
      }
      await cargarDatosIniciales()
    } catch (errorPeticion) {
      setError((errorPeticion?.response?.data?.message || 'no se pudo eliminar usuario').toLowerCase())
    }
  }

  async function editarNombreUsuario(idUsuario, nombreActual) {
    const nombreEditado = window.prompt('nuevo nombre del usuario', nombreActual)
    if (!nombreEditado || nombreEditado.trim().length < 3) return

    setError('')
    try {
      await solicitarApi('put', `/api/users/${idUsuario}`, {
        name: nombreEditado.trim(),
      })
      await cargarDatosIniciales()
    } catch (errorPeticion) {
      setError((errorPeticion?.response?.data?.message || 'no se pudo editar usuario').toLowerCase())
    }
  }

  async function cargarHistorialUsuario(idUsuario) {
    setUsuarioSeleccionado(idUsuario)
    try {
      const respuesta = await solicitarApi('get', `/api/events/user/${idUsuario}`, undefined, { limit: 20 })
      setHistorialUsuario(respuesta.data || [])
    } catch {
      setHistorialUsuario([])
    }
  }

  async function cargarSaldoUsuario(idUsuario, monto) {
    if (!monto || monto <= 0) {
      setError('ingresa un monto válido')
      return
    }

    setError('')
    try {
      await solicitarApi('patch', `/api/users/${idUsuario}/balance`, {
        amount: parseFloat(monto),
      })
      setMensaje(`saldo cargado: +Q${monto}`)
      setUsuarioParaSaldo(null)
      setMontoSaldo('')
      await cargarDatosIniciales()
      setTimeout(() => setMensaje(''), 3000)
    } catch (errorPeticion) {
      setError((errorPeticion?.response?.data?.message || 'no se pudo cargar saldo').toLowerCase())
    }
  }

  async function reiniciarSaldoUsuario(idUsuario) {
    setError('')
    try {
      await solicitarApi('patch', `/api/users/${idUsuario}/balance/reset`)
      setMensaje('saldo reiniciado a Q5.00')
      setUsuarioParaSaldo(null)
      setMontoSaldo('')
      await cargarDatosIniciales()
      setTimeout(() => setMensaje(''), 3000)
    } catch (errorPeticion) {
      setError((errorPeticion?.response?.data?.message || 'no se pudo reiniciar saldo').toLowerCase())
    }
  }

  async function cambiarEstadoEspacio(numeroEspacio, habilitado) {
    setError('')
    try {
      const clienteMqtt = conectarMqtt()
      clienteMqtt.emit('publish_command', {
        topic: 'park-guard/commands/parking/space',
        payload: {
          command: habilitado ? 'disable_space' : 'enable_space',
          space: numeroEspacio,
          timestamp: crearTimestamp()
        }
      })

      const ruta = habilitado
        ? `/api/parking/spaces/${numeroEspacio}/disable`
        : `/api/parking/spaces/${numeroEspacio}/enable`
      await solicitarApi('patch', ruta)
      await cargarDatosIniciales()
    } catch (errorPeticion) {
      setError((errorPeticion?.response?.data?.message || 'no se pudo cambiar espacio').toLowerCase())
    }
  }

  function crearTimestamp() {
    return new Date().toISOString()
  }

  async function accionarVentilador(activar) {
    setError('')
    try {
      const clienteMqtt = conectarMqtt()
      clienteMqtt.emit('publish_command', {
        topic: 'park-guard/commands/fan',
        payload: {
          command: activar ? 'activate_fan' : 'deactivate_fan',
          timestamp: crearTimestamp()
        }
      })

      await solicitarApi('post', activar ? '/api/commands/fan/activate' : '/api/commands/fan/deactivate')
      setEstadoVentilador(activar)
      setMensaje(activar ? 'ventilador encendido' : 'ventilador apagado')
      setTimeout(() => setMensaje(''), 2000)
    } catch (errorPeticion) {
      setError((errorPeticion?.response?.data?.message || 'no se pudo cambiar ventilador').toLowerCase())
    }
  }

  async function accionarTalanquera(tipo, abrir) {
    setError('')
    try {
      const clienteMqtt = conectarMqtt()
      clienteMqtt.emit('publish_command', {
        topic: `park-guard/commands/door/${tipo}`,
        payload: {
          command: abrir ? 'open_door' : 'close_door',
          door: tipo,
          timestamp: crearTimestamp()
        }
      })

      const ruta = tipo === 'entrance'
        ? (abrir ? '/api/commands/door/entrance/open' : '/api/commands/door/entrance/close')
        : (abrir ? '/api/commands/door/exit/open' : '/api/commands/door/exit/close')

      await solicitarApi('post', ruta)

      if (tipo === 'entrance') {
        setEstadoTalanqueraEntrada(abrir)
      } else {
        setEstadoTalanqueraSalida(abrir)
      }

      setMensaje(`talanquera ${tipo === 'entrance' ? 'entrada' : 'salida'} ${abrir ? 'abierta' : 'cerrada'}`)
      setTimeout(() => setMensaje(''), 2000)
    } catch (errorPeticion) {
      setError((errorPeticion?.response?.data?.message || 'no se pudo accionar talanquera').toLowerCase())
    }
  }

  async function accionarEmergencia(activar) {
    setError('')
    try {
      const clienteMqtt = conectarMqtt()
      clienteMqtt.emit('publish_command', {
        topic: 'park-guard/commands/emergency',
        payload: {
          command: activar ? 'activate_emergency' : 'deactivate_emergency',
          timestamp: crearTimestamp()
        }
      })

      await solicitarApi('post', activar ? '/api/commands/emergency/activate' : '/api/commands/emergency/deactivate')
      setEstadoEmergencia(activar)
      setMensaje(activar ? 'emergencia activada' : 'emergencia desactivada')
      setTimeout(() => setMensaje(''), 2000)
    } catch (errorPeticion) {
      setError((errorPeticion?.response?.data?.message || 'no se pudo cambiar emergencia').toLowerCase())
    }
  }

  function salir() {
    cerrarSesion()
    window.location.href = '/ingreso'
  }

  const conteoEspacios = useMemo(() => {
    const total = espacios.length
    const ocupados = espacios.filter((item) => item.is_occupied).length
    const disponibles = espacios.filter((item) => !item.is_occupied && item.is_enabled).length
    const mantenimiento = espacios.filter((item) => !item.is_enabled).length
    return { total, ocupados, disponibles, mantenimiento }
  }, [espacios])

  const actividadSospechosa = useMemo(() => {
    const limite = Date.now() - 5 * 60 * 1000
    const contadorPorTarjeta = {}

    eventos
      .filter((evento) => evento.event_type === 'access_denied')
      .forEach((evento) => {
        // Asegurar que el timestamp se interprete como UTC (agregando 'Z' si no lo tiene)
        const tsString = evento.timestamp.endsWith('Z') ? evento.timestamp : `${evento.timestamp}Z`
        const tiempo = new Date(tsString).getTime()
        const tarjeta = evento?.data?.rfid_card || 'sin tarjeta'
        if (tiempo >= limite) {
          contadorPorTarjeta[tarjeta] = (contadorPorTarjeta[tarjeta] || 0) + 1
        }
      })

    return Object.entries(contadorPorTarjeta)
      .filter(([, cantidad]) => cantidad >= 3)
      .map(([tarjeta, cantidad]) => ({ tarjeta, cantidad }))
      .sort((a, b) => b.cantidad - a.cantidad)
  }, [eventos])

  const datosGraficas = useMemo(() => {
    // Usar totales del resumen para los contadores principales si están disponibles
    const ingresos = resumen?.events?.access_granted_today ?? eventos.filter((item) => item.event_type === 'access_granted').length
    const denegados = resumen?.events?.access_denied_today ?? eventos.filter((item) => item.event_type === 'access_denied').length
    const salidas = eventos.filter((item) => item.event_type === 'manual_exit' || item.event_type === 'space_empty').length
    const emergencias = resumen?.events?.emergencies_today ?? eventos.filter(
      (item) => item.event_type === 'emergency_triggered' || item.event_type === 'emergency_alert',
    ).length
    const ventilador = eventos.filter(
      (item) => item.event_type === 'fan_activated' || item.event_type === 'fan_update',
    ).length

    const usoEspacio = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
    eventos.forEach((item) => {
      const numEspacio = item.space_id || item.space_number
      if (item.event_type === 'space_occupied' && numEspacio) {
        usoEspacio[numEspacio] = (usoEspacio[numEspacio] || 0) + 1
      }
    })

    const espacioMasUsado = Object.entries(usoEspacio).sort((a, b) => b[1] - a[1])[0]

    return {
      ingresos,
      denegados,
      salidas,
      emergencias,
      ventilador,
      usoEspacio,
      espacioMasUsado,
    }
  }, [eventos, resumen])

  const graficaAccesos = {
    labels: ['ingresos', 'denegados', 'salidas'],
    datasets: [
      {
        label: 'eventos',
        data: [datosGraficas.ingresos, datosGraficas.denegados, datosGraficas.salidas],
        backgroundColor: ['#22c55e', '#ef4444', '#3b82f6'],
      },
    ],
  }

  const graficaOperaciones = {
    labels: ['emergencias', 'ventilador'],
    datasets: [
      {
        label: 'cantidad',
        data: [datosGraficas.emergencias, datosGraficas.ventilador],
        backgroundColor: ['#f59e0b', '#8b5cf6'],
      },
    ],
  }

  function generarReportePdf() {
    const metricas = [
      ['espacios ocupados', String(conteoEspacios.ocupados)],
      ['espacios disponibles', String(conteoEspacios.disponibles)],
      ['espacios en mantenimiento', String(conteoEspacios.mantenimiento)],
      ['ingresos', String(datosGraficas.ingresos)],
      ['denegados', String(datosGraficas.denegados)],
      ['salidas', String(datosGraficas.salidas)],
      ['emergencias', String(datosGraficas.emergencias)],
      ['activaciones de ventilador', String(datosGraficas.ventilador)],
      [
        'espacio mas usado',
        datosGraficas.espacioMasUsado
          ? `espacio ${datosGraficas.espacioMasUsado[0]} con ${datosGraficas.espacioMasUsado[1]} usos`
          : 'sin datos',
      ],
      ['fecha', new Date().toLocaleString('es-GT')],
    ]

    const filasEventos = eventos
      .slice(0, 20)
      .map((item) => [item.description || item.event_type, formatearFecha(item.timestamp)])

    exportarReporte('reporte-park-guard.pdf', metricas, filasEventos)
  }

  function renderTiempoReal() {
    return (
      <div className="contenido-panel">
        <div className="rejilla-metricas">
          <TarjetaMetrica titulo="disponibles" valor={conteoEspacios.disponibles} estado="ok" />
          <TarjetaMetrica titulo="ocupados" valor={conteoEspacios.ocupados} estado="alerta" />
          <TarjetaMetrica titulo="mantenimiento" valor={conteoEspacios.mantenimiento} estado="normal" />
          <TarjetaMetrica titulo="gas ppm" valor={nivelGas ?? 'sin dato'} estado="normal" />
          <TarjetaMetrica titulo="ventilador" valor={estadoVentilador ? 'encendido' : 'apagado'} estado="normal" />
          <TarjetaMetrica titulo="emergencia" valor={estadoEmergencia ? 'activa' : 'normal'} estado={estadoEmergencia ? 'alerta' : 'ok'} />
        </div>

        <div className="bloque">
          <h3>visualizacion p5.js</h3>
          <LienzoParqueo
            espacios={espacios}
            nivelGas={nivelGas}
            estadoEmergencia={estadoEmergencia}
            estadoVentilador={estadoVentilador}
          />
        </div>

        <div className="bloque">
          <h3>acciones remotas</h3>
          <div className="panel-acciones-remotas">
            <div className="tarjeta-accion-remota">
              <div className="encabezado-accion-remota">
                <div className="titulo-accion-remota">🌀 ventilador</div>
                <span className={`insignia-estado ${estadoVentilador ? 'activo' : 'inactivo'}`}>
                  {estadoVentilador ? 'encendido' : 'apagado'}
                </span>
              </div>
              <div className="fila-botones">
                <button
                  disabled={estadoVentilador}
                  onClick={() => accionarVentilador(true)}
                >
                  encender
                </button>
                <button
                  disabled={!estadoVentilador}
                  onClick={() => accionarVentilador(false)}
                >
                  apagar
                </button>
              </div>
            </div>

            <div className="tarjeta-accion-remota">
              <div className="encabezado-accion-remota">
                <div className="titulo-accion-remota">🚨 emergencia</div>
                <span className={`insignia-estado ${estadoEmergencia ? 'alerta' : 'ok'}`}>
                  {estadoEmergencia ? 'activa' : 'normal'}
                </span>
              </div>
              <div className="fila-botones">
                <button disabled={estadoEmergencia} onClick={() => accionarEmergencia(true)}>
                  activar
                </button>
                <button disabled={!estadoEmergencia} onClick={() => accionarEmergencia(false)}>
                  desactivar
                </button>
              </div>
            </div>

            <div className="tarjeta-accion-remota">
              <div className="encabezado-accion-remota">
                <div className="titulo-accion-remota">  talanquera entrada</div>
                <span className={`insignia-estado ${estadoTalanqueraEntrada ? 'activo' : 'normal'}`}>
                  {estadoTalanqueraEntrada ? 'abierta' : 'cerrada'}
                </span>
              </div>
              <div className="fila-botones">
                <button
                  disabled={estadoTalanqueraEntrada}
                  onClick={() => accionarTalanquera('entrance', true)}
                >
                  abrir
                </button>
                <button
                  disabled={!estadoTalanqueraEntrada}
                  onClick={() => accionarTalanquera('entrance', false)}
                >
                  cerrar
                </button>
              </div>
            </div>

            <div className="tarjeta-accion-remota">
              <div className="encabezado-accion-remota">
                <div className="titulo-accion-remota">🚪 talanquera salida</div>
                <span className={`insignia-estado ${estadoTalanqueraSalida ? 'activo' : 'normal'}`}>
                  {estadoTalanqueraSalida ? 'abierta' : 'cerrada'}
                </span>
              </div>
              <div className="fila-botones">
                <button
                  disabled={estadoTalanqueraSalida}
                  onClick={() => accionarTalanquera('exit', true)}
                >
                  abrir
                </button>
                <button
                  disabled={!estadoTalanqueraSalida}
                  onClick={() => accionarTalanquera('exit', false)}
                >
                  cerrar
                </button>
              </div>
            </div>
          </div>

          <div className="lista-espacios-control">
            {espacios.map((espacio) => {
              return (
                <div key={espacio.id || espacio.space_number} className="item-espacio-control">
                  <div className="info-espacio-control">
                    <strong>espacio {espacio.space_number}</strong>
                    <span className={`insignia-estado ${espacio.is_occupied ? 'alerta' : 'activo'}`}>
                      {espacio.is_occupied ? 'ocupado' : 'libre'}
                    </span>
                    <span className={`insignia-estado ${espacio.is_enabled ? 'activo' : 'inactivo'}`}>
                      {espacio.is_enabled ? 'habilitado' : 'mantenimiento'}
                    </span>
                  </div>

                  <div className="acciones-espacio-control">
                    <button
                      className="boton-control-espacio"
                      onClick={() => cambiarEstadoEspacio(espacio.space_number, espacio.is_enabled)}
                    >
                      {espacio.is_enabled ? 'deshabilitar espacio' : 'habilitar espacio'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="bloque">
          <h3>eventos recientes</h3>
          <div className="tabla-simple">
            {eventos.slice(0, 12).map((evento, indice) => (
              <div key={`${evento.timestamp}-${indice}`} className="fila-tabla">
                <span>{evento.description || evento.event_type}</span>
                <span>{formatearFecha(evento.timestamp)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  function renderUsuarios() {
    return (
      <div className="contenido-panel usuarios">
        <div className="bloque">
          <h3>crear usuario rfid</h3>
          <form className="formulario-dos-columnas" onSubmit={crearUsuario}>
            <label>
              nombre
              <input
                value={nombreNuevo}
                onChange={(evento) => setNombreNuevo(evento.target.value)}
                minLength={3}
                required
              />
            </label>
            <label>
              tarjeta rfid
              <input
                value={tarjetaNueva}
                onChange={(evento) => setTarjetaNueva(evento.target.value.toUpperCase())}
                minLength={8}
                required
              />
            </label>
            <button type="submit">guardar usuario</button>
          </form>
        </div>

        <div className="bloque">
          <h3>usuarios registrados</h3>
          <div className="tabla-simple">
            {usuarios.map((usuario) => (
              <div className="fila-tabla fila-usuario" key={usuario.id}>
                <span>{usuario.name}</span>
                <span>{usuario.rfid_card}</span>
                <span className={usuario.balance < 20 ? 'texto-alerta' : ''}>{usuario.balance ? `Q ${usuario.balance.toFixed(2)}` : 'Q 0.00'}</span>
                <span>{usuario.is_active ? 'activo' : 'inactivo'}</span>
                <span>accesos: {usuario.access_count || 0}</span>
                <div className="fila-botones fila-botones-compacta">
                  <button onClick={() => editarNombreUsuario(usuario.id, usuario.name)}>editar</button>
                  <button onClick={() => cambiarEstadoUsuario(usuario.id, usuario.is_active)}>
                    {usuario.is_active ? 'desactivar' : 'activar'}
                  </button>
                  <button onClick={() => setUsuarioParaSaldo(usuario.id)}>💰 saldo</button>
                  <button onClick={() => cargarHistorialUsuario(usuario.id)}>historial</button>
                  <button onClick={() => eliminarUsuario(usuario.id)}>eliminar</button>
                </div>
                {usuarioParaSaldo === usuario.id && (
                  <div className="formulario-carga-saldo">
                    <input
                      type="number"
                      placeholder="cantidad (Q)"
                      value={montoSaldo}
                      onChange={(e) => setMontoSaldo(e.target.value)}
                      min="1"
                      step="0.50"
                    />
                    <button onClick={() => cargarSaldoUsuario(usuario.id, montoSaldo)}>cargar</button>
                    <button className="boton-reiniciar-saldo" onClick={() => reiniciarSaldoUsuario(usuario.id)}>
                      reiniciar Q5
                    </button>
                    <button onClick={() => setUsuarioParaSaldo(null)}>cancelar</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="bloque dos-columnas">
          <div>
            <h3>historial del usuario</h3>
            {!usuarioSeleccionado && <p>selecciona un usuario para ver su historial</p>}
            {usuarioSeleccionado && (
              <div className="tabla-simple">
                {historialUsuario.length === 0 && <p>sin eventos para este usuario</p>}
                {historialUsuario.map((evento, indice) => (
                  <div key={`${evento.timestamp}-${indice}`} className="fila-tabla">
                    <span>{evento.description || evento.event_type}</span>
                    <span>{formatearFecha(evento.timestamp)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h3>actividad sospechosa</h3>
            {actividadSospechosa.length === 0 && <p>sin alertas en los ultimos 5 minutos</p>}
            {actividadSospechosa.map((item) => (
              <div key={item.tarjeta} className="alerta-sospechosa">
                tarjeta {item.tarjeta} con {item.cantidad} intentos denegados
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  function renderEstadisticas() {
    const resumenParqueo = resumen?.parking || {}
    const resumenEventos = resumen?.events || {}
    
    // Calcular ocupación en tiempo real basándose en el estado de los espacios
    const ocupacionReal = conteoEspacios.total > 0 
      ? Number(((conteoEspacios.ocupados / conteoEspacios.total) * 100).toFixed(1)) 
      : 0

    return (
      <div className="contenido-panel">
        <div className="rejilla-metricas">
          <TarjetaMetrica titulo="ocupacion %" valor={ocupacionReal} estado="normal" />
          <TarjetaMetrica titulo="ingresos hoy" valor={resumenEventos.access_granted_today ?? datosGraficas.ingresos} estado="ok" />
          <TarjetaMetrica titulo="denegados hoy" valor={resumenEventos.access_denied_today ?? datosGraficas.denegados} estado="alerta" />
          <TarjetaMetrica titulo="emergencias hoy" valor={resumenEventos.emergencies_today ?? datosGraficas.emergencias} estado="alerta" />
          <TarjetaMetrica
            titulo="espacio mas usado"
            valor={
              datosGraficas.espacioMasUsado
                ? `espacio ${datosGraficas.espacioMasUsado[0]} (${datosGraficas.espacioMasUsado[1]})`
                : 'sin datos'
            }
            estado="normal"
          />
          <TarjetaMetrica titulo="activaciones ventilador" valor={datosGraficas.ventilador} estado="normal" />
        </div>

        <div className="bloque dos-columnas">
          <div>
            <h3>grafica de ingresos y salidas</h3>
            <Bar data={graficaAccesos} />
          </div>
          <div>
            <h3>grafica de emergencias y ventilador</h3>
            <Doughnut data={graficaOperaciones} />
          </div>
        </div>

        <div className="bloque">
          <h3>reporte en pdf</h3>
          <button onClick={generarReportePdf}>descargar reporte pdf</button>
        </div>
      </div>
    )
  }

  function renderViv() {
    const eventosVivTiempoReal = eventos.filter((e) => e.event_type === 'viv_detection')
    const normalizarTipo = (tipo) => {
      if (tipo === 'car') return 'carro'
      if (tipo === 'motorcycle') return 'moto'
      return tipo || 'desconocido'
    }

    return (
      <div className="contenido-panel">
        <div className="bloque">
          <h3>imagen reciente de placa</h3>
          {imagenPlacaUrl ? (
            <img
              className="imagen-placa-viv"
              src={imagenPlacaUrl}
              alt="última placa detectada"
              onError={() => setImagenPlacaUrl('')}
            />
          ) : (
            <p style={{ opacity: 0.7 }}>sin imagen disponible aún, espera una detección VIV.</p>
          )}
        </div>

        <div className="bloque">
          <h3>historial de visión por computadora (viv)</h3>
          <p style={{ marginBottom: '1rem', color: '#94a3b8' }}>
            Logs de detecciones con tipo de vehículo (carro/moto), placa y hora.
          </p>

          <div className="tabla-simple">
            {deteccionesViv.length === 0 && eventosVivTiempoReal.length === 0 && (
              <p style={{ padding: '1rem', opacity: 0.7 }}>esperando nuevas detecciones...</p>
            )}

            {(deteccionesViv.length > 0 || eventosVivTiempoReal.length > 0) && (
              <div className="fila-tabla" style={{ borderBottom: '1px solid #334155', fontWeight: 'bold' }}>
                <span>vehículo / placa</span>
                <span>hora de detección</span>
              </div>
            )}

            {deteccionesViv.map((evento, indice) => (
              <div key={`${evento.timestamp}-${indice}`} className="fila-tabla">
                <span style={{ color: '#38bdf8', fontWeight: '600' }}>
                  {normalizarTipo(evento.vehicle_type)} - placa {evento.plate_text || 'sin lectura'}
                </span>
                <span>{formatearFecha(evento.timestamp)}</span>
              </div>
            ))}

            {deteccionesViv.length === 0 && eventosVivTiempoReal.map((evento, indice) => (
              <div key={`${evento.timestamp}-${indice}`} className="fila-tabla">
                <span style={{ color: '#38bdf8', fontWeight: '600' }}>{evento.description || evento.event_type}</span>
                <span>{formatearFecha(evento.timestamp)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (cargando) {
    return <div className="pantalla-cargando">cargando panel...</div>
  }

  return (
    <div className="pantalla-panel">
      <header className="encabezado-panel">
        <div>
          <h1>panel park guard 2.0</h1>
          <p>administrador: {nombreAdmin}</p>
        </div>
        <div className="fila-botones">
          <button onClick={cargarDatosIniciales}>actualizar</button>
          <button onClick={salir}>salir</button>
        </div>
      </header>

      <BarraPestanas activa={pestanaActiva} alCambiar={setPestanaActiva} />

      {mensaje && <p className="texto-ok">{mensaje}</p>}
      {error && <p className="texto-error">{error}</p>}

      {pestanaActiva === 'tiempo_real' && renderTiempoReal()}
      {pestanaActiva === 'viv' && renderViv()}
      {pestanaActiva === 'usuarios' && renderUsuarios()}
      {pestanaActiva === 'estadisticas' && renderEstadisticas()}
    </div>
  )
}

export default PaginaPanel
