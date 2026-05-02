import axios from 'axios'
import { esSesionPrueba } from './autenticacion'

function obtenerUrlApiPorDefecto() {
  if (typeof window === 'undefined') {
    return 'http://localhost:5000'
  }
  const { protocol, hostname } = window.location
  
  // Si se ejecuta localmente o en red local, el backend suele estar en el mismo servidor
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.') || hostname.startsWith('172.') || hostname.startsWith('10.')) {
    return `${protocol}//${hostname}:5000`
  }
  
  // Si se ejecuta en un bucket S3 u otro dominio de producción, DEBE configurarse VITE_API_URL en el archivo .env
  console.warn('⚠️ Ejecutando en entorno de producción/nube sin VITE_API_URL. El backend no estará en el mismo dominio (ej. S3). Configura el archivo .env antes de hacer "npm run build".')
  
  // Fallback que asume que el backend NO está en el mismo host si el frontend es S3
  // Retornamos la IP de red como fallback temporal, pero fallará si se accede desde fuera de la red local sin VITE_API_URL configurado a la IP pública de EC2.
  return `http://192.168.0.6:5000`
}

const clienteApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL || obtenerUrlApiPorDefecto(),
  timeout: 15000,
})

clienteApi.interceptors.request.use((configuracion) => {
  const token = localStorage.getItem('token')
  if (token) {
    configuracion.headers.Authorization = `Bearer ${token}`
  }
  return configuracion
})

clienteApi.interceptors.response.use(
  (respuesta) => respuesta,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Evitar cerrar sesión automáticamente en modo de prueba.
      if (!esSesionPrueba()) {
        localStorage.removeItem('token')
        localStorage.removeItem('admin_nombre')
        localStorage.removeItem('admin_email')
        if (window.location.pathname !== '/ingreso') {
          window.location.href = '/ingreso'
        }
      }
    }
    return Promise.reject(error)
  }
)

export async function solicitarApi(metodo, ruta, datos = undefined, parametros = undefined) {
  const respuesta = await clienteApi({
    method: metodo,
    url: ruta,
    data: datos,
    params: parametros,
  })
  return respuesta.data
}

export default clienteApi
