function TarjetaMetrica({ titulo, valor, estado = 'normal' }) {
  return (
    <div className={`tarjeta-metrica ${estado}`}>
      <p className="tarjeta-titulo">{titulo}</p>
      <p className="tarjeta-valor">{valor}</p>
    </div>
  )
}

export default TarjetaMetrica
