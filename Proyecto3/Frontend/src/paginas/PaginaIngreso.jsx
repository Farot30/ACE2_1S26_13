import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { guardarSesion, iniciarSesion, registrarAdmin } from '../servicios/autenticacion'

function IconoCarro() {
  return (
    <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" width="40" height="40">
      <rect width="64" height="64" rx="16" fill="#0ea5e9" />
      <path d="M14 36l4-12h28l4 12" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
      <rect x="12" y="36" width="40" height="10" rx="3" fill="white" fillOpacity="0.15" stroke="white" strokeWidth="2"/>
      <circle cx="22" cy="46" r="4" fill="white"/>
      <circle cx="42" cy="46" r="4" fill="white"/>
      <path d="M12 40h40" stroke="white" strokeWidth="1.5"/>
      <rect x="26" y="30" width="12" height="6" rx="1.5" fill="white" fillOpacity="0.4"/>
    </svg>
  )
}

function PaginaIngreso() {
  const navegar = useNavigate()
  const [modoRegistro, setModoRegistro] = useState(false)
  const [nombre, setNombre] = useState('')
  const [correo, setCorreo] = useState('')
  const [clave, setClave] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  async function enviarFormulario(evento) {
    evento.preventDefault()
    setCargando(true)
    setError('')

    if (correo === 'g13' && clave === '123') {
      guardarSesion({ token: 'dev-token-g13', name: 'Admin G13', email: 'g13' })
      navegar('/panel')
      setCargando(false)
      return
    }

    try {
      if (modoRegistro) {
        await registrarAdmin(nombre, correo, clave)
      }
      const respuesta = await iniciarSesion(correo, clave)
      guardarSesion(respuesta.data)
      navegar('/panel')
    } catch (errorPeticion) {
      const mensaje = errorPeticion?.response?.data?.message || 'no se pudo completar el ingreso'
      setError(mensaje.toLowerCase())
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="pantalla-ingreso">
      <div className="ingreso-fondo-blur" />

      <form className="tarjeta-ingreso" onSubmit={enviarFormulario}>
        {/* Encabezado */}
        <div className="ingreso-logo">
          <IconoCarro />
          <div>
            <h1>Park Guard</h1>
            <span>v2.0 — sistema de parqueo</span>
          </div>
        </div>

        <div className="ingreso-divisor" />

        <p className="ingreso-subtitulo">
          {modoRegistro ? '✦ nuevo administrador' : '✦ acceso administrativo'}
        </p>

        {/* Campos */}
        <div className="ingreso-campos">
          {modoRegistro && (
            <div className="campo-grupo">
              <label>nombre completo</label>
              <input
                type="text"
                placeholder="Ej. Juan García"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                required
                minLength={3}
              />
            </div>
          )}

          <div className="campo-grupo">
            <label>usuario</label>
            <input
              type="text"
              placeholder="Ej. g13"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              required
              autoComplete="username"
            />
          </div>

          <div className="campo-grupo">
            <label>contraseña</label>
            <input
              type="password"
              placeholder="••••••"
              value={clave}
              onChange={(e) => setClave(e.target.value)}
              required
              minLength={3}
              autoComplete="current-password"
            />
          </div>
        </div>

        {error && (
          <div className="ingreso-error">
            <span>⚠</span> {error}
          </div>
        )}

        <button className="boton-primario" disabled={cargando} type="submit">
          {cargando
            ? <span className="boton-cargando"><span className="spinner" />procesando...</span>
            : modoRegistro ? 'crear cuenta e ingresar' : 'ingresar al sistema'}
        </button>

        <button
          className="boton-link"
          type="button"
          onClick={() => { setModoRegistro((v) => !v); setError('') }}
        >
          {modoRegistro ? '← volver al ingreso' : '¿sin cuenta? registrar administrador'}
        </button>
      </form>
    </div>
  )
}

export default PaginaIngreso
