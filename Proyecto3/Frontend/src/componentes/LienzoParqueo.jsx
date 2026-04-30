import { useEffect, useRef } from 'react'
import p5 from 'p5'

function LienzoParqueo({ espacios, nivelGas, estadoEmergencia, estadoVentilador }) {
  const referenciaContenedor = useRef(null)

  useEffect(() => {
    let instancia = null

    const boceto = (dibujo) => {
      dibujo.setup = () => {
        dibujo.createCanvas(680, 320)
      }

      dibujo.draw = () => {
        dibujo.background(248, 250, 252)

        dibujo.noStroke()
        dibujo.fill(15, 23, 42)
        dibujo.textSize(18)
        dibujo.text('estado de parqueos', 24, 30)

        espacios.forEach((espacio, indice) => {
          const ejeX = 24 + indice * 128
          const ejeY = 56
          const ancho = 110
          const alto = 170

          if (!espacio.is_enabled) {
            dibujo.fill(148, 163, 184)
          } else if (espacio.is_occupied) {
            dibujo.fill(239, 68, 68)
          } else {
            dibujo.fill(34, 197, 94)
          }

          dibujo.rect(ejeX, ejeY, ancho, alto, 14)
          dibujo.fill(255)
          dibujo.textSize(14)
          dibujo.text(`espacio ${espacio.space_number}`, ejeX + 12, ejeY + 28)
          dibujo.text(espacio.is_enabled ? (espacio.is_occupied ? 'ocupado' : 'libre') : 'mantenimiento', ejeX + 12, ejeY + 54)
        })

        // Nivel de Gas (Barra visual)
        dibujo.fill(15, 23, 42)
        dibujo.textSize(14)
        dibujo.text(`gas: ${nivelGas ?? '...'} ppm`, 24, 260)
        
        dibujo.fill(226, 232, 240)
        dibujo.rect(24, 270, 200, 10, 5)
        const anchoGas = dibujo.constrain(dibujo.map(nivelGas || 0, 0, 1000, 0, 200), 0, 200)
        dibujo.fill(nivelGas > 300 ? '#ef4444' : '#22c55e')
        dibujo.rect(24, 270, anchoGas, 10, 5)

        // Emergencia y Ventilador
        dibujo.fill(estadoEmergencia ? '#ef4444' : '#22c55e')
        dibujo.text(`emergencia: ${estadoEmergencia ? 'ACTIVA' : 'NORMAL'}`, 260, 260)
        
        dibujo.fill(15, 23, 42)
        dibujo.text(`ventilador: ${estadoVentilador ? 'ENCENDIDO' : 'APAGADO'}`, 260, 280)
      }
    }

    if (referenciaContenedor.current) {
      referenciaContenedor.current.innerHTML = ''
      instancia = new p5(boceto, referenciaContenedor.current)
    }

    return () => {
      if (instancia) instancia.remove()
      if (referenciaContenedor.current) {
        referenciaContenedor.current.innerHTML = ''
      }
    }
  }, [espacios, nivelGas, estadoEmergencia, estadoVentilador])

  return <div className="contenedor-lienzo" ref={referenciaContenedor} />
}

export default LienzoParqueo
