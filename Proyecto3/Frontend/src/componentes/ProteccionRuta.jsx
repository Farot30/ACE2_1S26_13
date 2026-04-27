import { Navigate } from 'react-router-dom'
import { obtenerToken } from '../servicios/autenticacion'

function ProteccionRuta({ children }) {
  const token = obtenerToken()

  if (!token) {
    return <Navigate to="/ingreso" replace />
  }

  return children
}

export default ProteccionRuta
