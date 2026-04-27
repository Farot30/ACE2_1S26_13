import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

export function exportarReporte(nombreArchivo, metricas, filasEventos) {
  const documento = new jsPDF()
  documento.setFontSize(16)
  documento.text('reporte park guard 2.0', 14, 16)

  autoTable(documento, {
    startY: 24,
    head: [['metrica', 'valor']],
    body: metricas,
  })

  autoTable(documento, {
    startY: documento.lastAutoTable.finalY + 8,
    head: [['evento', 'fecha']],
    body: filasEventos,
  })

  documento.save(nombreArchivo)
}
