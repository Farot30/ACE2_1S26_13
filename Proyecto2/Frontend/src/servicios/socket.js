import { io } from 'socket.io-client'

let socket = null

function obtenerUrlSocketPorDefecto() {
  if (typeof window === 'undefined') {
    return 'http://localhost:5000'
  }
  const { protocol, hostname } = window.location
  return `${protocol}//${hostname}:5000`
}

export function conectarSocket() {
  if (!socket) {
    socket = io(import.meta.env.VITE_SOCKET_URL || obtenerUrlSocketPorDefecto(), {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 20,
      reconnectionDelay: 800,
    })
  }
  return socket
}

export function desconectarSocket() {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}
