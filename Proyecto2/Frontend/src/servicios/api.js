import axios from 'axios'

function obtenerUrlApiPorDefecto() {
  if (typeof window === 'undefined') {
    return 'http://localhost:5000'
  }
  const { protocol, hostname } = window.location
  return `${protocol}//${hostname}:5000`
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
