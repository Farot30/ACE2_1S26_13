import { useEffect, useRef } from 'react'
import p5 from 'p5'

function LienzoParqueo({ espacios, nivelGas, estadoEmergencia }) {
  const referenciaContenedor = useRef(null)

  useEffect(() => {
    let instancia = null

    const boceto = (dibujo) => {
      dibujo.setup = () => {
        dibujo.createCanvas(680, 290)
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

        dibujo.fill(15, 23, 42)
        dibujo.textSize(14)
        dibujo.text(`gas ppm: ${nivelGas ?? 'sin dato'}`, 24, 255)
        dibujo.text(`emergencia: ${estadoEmergencia ? 'activa' : 'normal'}`, 260, 255)
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
  }, [espacios, nivelGas, estadoEmergencia])

  return <div className="contenedor-lienzo" ref={referenciaContenedor} />
}

export default LienzoParqueo
