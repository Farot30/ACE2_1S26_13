import { solicitarApi } from './api'

const TOKEN_PRUEBA = 'dev-token-g13'

export async function iniciarSesion(correo, clave) {
  const respuesta = await solicitarApi('post', '/api/auth/login', {
    email: correo,
    password: clave,
  })
  return respuesta
}

export async function registrarAdmin(nombre, correo, clave) {
  return solicitarApi('post', '/api/auth/register', {
    name: nombre,
    email: correo,
    password: clave,
  })
}

export async function validarToken(token) {
  return solicitarApi('post', '/api/auth/validate-token', { token })
}

export function guardarSesion(datos) {
  localStorage.setItem('token', datos.token)
  localStorage.setItem('admin_nombre', datos.name || '')
  localStorage.setItem('admin_email', datos.email || '')
}

export function cerrarSesion() {
  localStorage.removeItem('token')
  localStorage.removeItem('admin_nombre')
  localStorage.removeItem('admin_email')
}

export function obtenerToken() {
  return localStorage.getItem('token')
}

export function esSesionPrueba() {
  return obtenerToken() === TOKEN_PRUEBA
}
