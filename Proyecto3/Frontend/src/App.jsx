import { Navigate, Route, Routes } from 'react-router-dom'
import ProteccionRuta from './componentes/ProteccionRuta'
import PaginaIngreso from './paginas/PaginaIngreso'
import PaginaPanel from './paginas/PaginaPanel'

function App() {
  return (
    <Routes>
      <Route path="/ingreso" element={<PaginaIngreso />} />
      <Route
        path="/panel"
        element={
          <ProteccionRuta>
            <PaginaPanel />
          </ProteccionRuta>
        }
      />
      <Route path="*" element={<Navigate to="/panel" replace />} />
    </Routes>
  )
}

export default App
