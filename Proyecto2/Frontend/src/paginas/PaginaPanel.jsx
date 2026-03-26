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

  const nombreAdmin = localStorage.getItem('admin_nombre') || 'admin'

  useEffect(() => {
    cargarDatosIniciales()
  }, [])

  useEffect(() => {
    const clienteMqtt = conectarMqtt()

    clienteMqtt.on('connect', () => {
      clienteMqtt.emit('subscribe_parking', { canal: 'parking-updates' })
    })

    const handleParkingUpdate = (dato) => {
      setEspacios((anterior) =>
        anterior.map((espacio) =>
          espacio.space_number === dato.space_number
            ? { ...espacio, is_occupied: dato.is_occupied }
            : espacio,
        ),
      )
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
      setEstadoEmergencia(true)
      insertarEventoEnVivo({
        event_type: 'emergency_alert',
        description: `alerta ${dato.alert_type || 'emergencia'} en ${dato.location || 'zona general'}`,
        timestamp: dato.timestamp,
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

    clienteMqtt.on('parking_update', handleParkingUpdate)
    clienteMqtt.on('gas_update', handleGasUpdate)
    clienteMqtt.on('ventilator_update', handleVentilatorUpdate)
    clienteMqtt.on('door_update', handleDoorUpdate)
    clienteMqtt.on('emergency_alert', handleEmergencyAlert)
    clienteMqtt.on('system_status', handleSystemStatus)

    return () => {
      clienteMqtt.off('parking_update', handleParkingUpdate)
      clienteMqtt.off('gas_update', handleGasUpdate)
      clienteMqtt.off('ventilator_update', handleVentilatorUpdate)
      clienteMqtt.off('door_update', handleDoorUpdate)
      clienteMqtt.off('emergency_alert', handleEmergencyAlert)
      clienteMqtt.off('system_status', handleSystemStatus)
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

      setEspacios(respuestaEspacios.data || [])
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
      await solicitarApi('post', '/api/users', {
        name: nombreNuevo,
        rfid_card: tarjetaNueva,
      })
      setNombreNuevo('')
      setTarjetaNueva('')
      await cargarDatosIniciales()
    } catch (errorPeticion) {
      setError((errorPeticion?.response?.data?.message || 'no se pudo crear usuario').toLowerCase())
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
      const ruta = habilitado
        ? `/api/parking/spaces/${numeroEspacio}/disable`
        : `/api/parking/spaces/${numeroEspacio}/enable`
      await solicitarApi('patch', ruta)
      await cargarDatosIniciales()
    } catch (errorPeticion) {
      setError((errorPeticion?.response?.data?.message || 'no se pudo cambiar espacio').toLowerCase())
    }
  }

  async function ejecutarComandoRemoto(ruta, mensajeError, mensajeExito = '') {
    setError('')
    try {
      await solicitarApi('post', ruta)
      if (mensajeExito) {
        setMensaje(mensajeExito)
        setTimeout(() => setMensaje(''), 2000)
      }
    } catch {
      setError(mensajeError)
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
        const tiempo = new Date(evento.timestamp).getTime()
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
    const ingresos = eventos.filter((item) => item.event_type === 'access_granted').length
    const denegados = eventos.filter((item) => item.event_type === 'access_denied').length
    const salidas = eventos.filter((item) => item.event_type === 'manual_exit' || item.event_type === 'space_empty').length
    const emergencias = eventos.filter(
      (item) => item.event_type === 'emergency_triggered' || item.event_type === 'emergency_alert',
    ).length
    const ventilador = eventos.filter(
      (item) => item.event_type === 'fan_activated' || item.event_type === 'fan_update',
    ).length

    const usoEspacio = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
    eventos.forEach((item) => {
      if (item.event_type === 'space_occupied' && item.space_id) {
        usoEspacio[item.space_id] = (usoEspacio[item.space_id] || 0) + 1
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
  }, [eventos])

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
          <LienzoParqueo espacios={espacios} nivelGas={nivelGas} estadoEmergencia={estadoEmergencia} />
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
                  onClick={() => ejecutarComandoRemoto('/api/commands/fan/activate', 'no se pudo encender ventilador', 'ventilador activado')}
                >
                  encender
                </button>
                <button
                  disabled={!estadoVentilador}
                  onClick={() => ejecutarComandoRemoto('/api/commands/fan/deactivate', 'no se pudo apagar ventilador', 'ventilador desactivado')}
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
                <button
                  disabled={estadoEmergencia}
                  onClick={() => ejecutarComandoRemoto('/api/commands/emergency/activate', 'no se pudo activar emergencia', 'emergencia activada')}
                >
                  activar
                </button>
                <button
                  disabled={!estadoEmergencia}
                  onClick={() => ejecutarComandoRemoto('/api/commands/emergency/deactivate', 'no se pudo desactivar emergencia', 'emergencia desactivada')}
                >
                  desactivar
                </button>
              </div>
            </div>

            <div className="tarjeta-accion-remota">
              <div className="encabezado-accion-remota">
                <div className="titulo-accion-remota">🚧 talanquera entrada</div>
                <span className={`insignia-estado ${estadoTalanqueraEntrada ? 'activo' : 'normal'}`}>
                  {estadoTalanqueraEntrada ? 'abierta' : 'cerrada'}
                </span>
              </div>
              <div className="fila-botones">
                <button
                  disabled={estadoTalanqueraEntrada}
                  onClick={() =>
                    solicitarApi('post', '/api/commands/door/entrance/open').catch(() =>
                      setError('no se pudo abrir talanquera'),
                    )
                  }
                >
                  abrir
                </button>
                <button
                  disabled={!estadoTalanqueraEntrada}
                  onClick={() =>
                    solicitarApi('post', '/api/commands/door/entrance/close').catch(() =>
                      setError('no se pudo cerrar talanquera'),
                    )
                  }
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
                  onClick={() =>
                    solicitarApi('post', '/api/commands/door/exit/open').catch(() =>
                      setError('no se pudo abrir talanquera'),
                    )
                  }
                >
                  abrir
                </button>
                <button
                  disabled={!estadoTalanqueraSalida}
                  onClick={() =>
                    solicitarApi('post', '/api/commands/door/exit/close').catch(() =>
                      setError('no se pudo cerrar talanquera'),
                    )
                  }
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

    return (
      <div className="contenido-panel">
        <div className="rejilla-metricas">
          <TarjetaMetrica titulo="ocupacion %" valor={resumenParqueo.occupancy_percentage ?? 0} estado="normal" />
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
      {pestanaActiva === 'usuarios' && renderUsuarios()}
      {pestanaActiva === 'estadisticas' && renderEstadisticas()}
    </div>
  )
}

export default PaginaPanel
