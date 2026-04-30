const pestanas = [
  { id: 'tiempo_real', etiqueta: 'tiempo real' },
  { id: 'viv', etiqueta: 'VIV (visión)' },
  { id: 'usuarios', etiqueta: 'usuarios rfid' },
  { id: 'estadisticas', etiqueta: 'estadisticas y reporte' },
]

function BarraPestanas({ activa, alCambiar }) {
  return (
    <div className="barra-pestanas">
      {pestanas.map((pestana) => (
        <button
          key={pestana.id}
          className={`boton-pestana ${activa === pestana.id ? 'activa' : ''}`}
          onClick={() => alCambiar(pestana.id)}
        >
          {pestana.etiqueta}
        </button>
      ))}
    </div>
  )
}

export default BarraPestanas
