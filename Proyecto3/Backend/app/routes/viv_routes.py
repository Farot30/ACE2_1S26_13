"""Rutas VIV - Detección de vehículos por visión"""
from flask import Blueprint, request, jsonify, send_file
from app import get_db
from datetime import datetime, timedelta
from app.utils.decorators import token_required
from pathlib import Path

bp = Blueprint('viv', __name__, url_prefix='/api/viv')


@bp.route('/detecciones', methods=['GET'])
@token_required
def obtener_detecciones(usuario_id):
    """Obtener detecciones VIV recientes"""
    db = get_db()

    limite = request.args.get('limit', 50, type=int)
    dias = request.args.get('dias', 7, type=int)

    fecha_inicio = datetime.utcnow() - timedelta(days=dias)

    detecciones = list(db.registros_viv.find(
        {'timestamp': {'$gte': fecha_inicio}}
    ).sort('timestamp', -1).limit(limite))

    # Convertir ObjectId a string
    for det in detecciones:
        det['_id'] = str(det['_id'])
        if 'registro_id' in det:
            det['registro_id'] = str(det['registro_id'])

    return jsonify({
        'success': True,
        'data': detecciones,
        'total': len(detecciones)
    }), 200


@bp.route('/placa-imagen', methods=['GET'])
@token_required
def obtener_imagen_placa(usuario_id):
    """Retorna la última imagen de región de placa generada por VIV."""
    ruta_raiz = Path(__file__).resolve().parents[3]
    posibles_rutas = [
        ruta_raiz / 'VIV' / 'plate_region.jpg',
        ruta_raiz / 'VIV' / 'plate_region-jpg',
    ]
    ruta_imagen = next((ruta for ruta in posibles_rutas if ruta.exists()), None)

    if ruta_imagen is None:
        return jsonify({
            'success': False,
            'message': 'imagen de placa no disponible aun'
        }), 404

    return send_file(ruta_imagen, mimetype='image/jpeg')


@bp.route('/vehiculos-activos', methods=['GET'])
@token_required
def vehiculos_activos(usuario_id):
    """Obtener vehículos actualmente en el parqueo"""
    db = get_db()

    # Registros sin salida = vehículos activos
    activos = list(db.registros_entrada_salida.find(
        {'timestamp_salida': None}
    ).sort('timestamp_entrada', -1))

    # Convertir ObjectId a string
    for auto in activos:
        auto['_id'] = str(auto['_id'])

    return jsonify({
        'success': True,
        'data': activos,
        'total': len(activos)
    }), 200


@bp.route('/estadisticas', methods=['GET'])
@token_required
def estadisticas_viv(usuario_id):
    """Obtener estadísticas VIV"""
    db = get_db()

    dias = request.args.get('dias', 30, type=int)
    fecha_inicio = datetime.utcnow() - timedelta(days=dias)

    # Total de entradas
    total_entradas = db.registros_entrada_salida.count_documents(
        {'timestamp_entrada': {'$gte': fecha_inicio}}
    )

    # Total de salidas
    total_salidas = db.registros_entrada_salida.count_documents(
        {'timestamp_salida': {'$gte': fecha_inicio}, 'timestamp_salida': {'$ne': None}}
    )

    # Ingresos totales
    registros_completados = list(db.registros_entrada_salida.find(
        {'timestamp_salida': {'$gte': fecha_inicio}, 'timestamp_salida': {'$ne': None}}
    ))

    ingresos_totales = sum([r.get('tarifa_cobrada', 0) for r in registros_completados])

    # Por tipo de vehículo
    por_tipo = db.registros_entrada_salida.aggregate([
        {
            '$match': {
                'timestamp_entrada': {'$gte': fecha_inicio}
            }
        },
        {
            '$group': {
                '_id': '$vehicle_type',
                'cantidad': {'$sum': 1},
                'ingresos': {'$sum': {'$cond': [{'$ne': ['$tarifa_cobrada', None]}, '$tarifa_cobrada', 0]}}
            }
        }
    ])

    stats_por_tipo = {item['_id']: {'cantidad': item['cantidad'], 'ingresos': item['ingresos']} for item in por_tipo}

    return jsonify({
        'success': True,
        'data': {
            'dias': dias,
            'total_entradas': total_entradas,
            'total_salidas': total_salidas,
            'ingresos_totales': ingresos_totales,
            'por_tipo_vehiculo': stats_por_tipo,
            'vehiculos_activos': db.registros_entrada_salida.count_documents({'timestamp_salida': None})
        }
    }), 200


@bp.route('/historial/<plate>', methods=['GET'])
@token_required
def historial_vehiculo(usuario_id, plate):
    """Obtener historial de un vehículo por placa"""
    db = get_db()

    registros = list(db.registros_entrada_salida.find(
        {'plate_text': plate.upper()}
    ).sort('timestamp_entrada', -1))

    for reg in registros:
        reg['_id'] = str(reg['_id'])

    return jsonify({
        'success': True,
        'plate': plate.upper(),
        'data': registros,
        'total': len(registros)
    }), 200
