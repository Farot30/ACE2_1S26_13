export function formatearFecha(fechaTexto) {
  if (!fechaTexto) return 'sin fecha'
  const fecha = new Date(fechaTexto)
  if (Number.isNaN(fecha.getTime())) return 'sin fecha'
  return fecha.toLocaleString('es-GT', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}
