#!/usr/bin/env python3
"""Script simple para exponer métricas a Grafana"""
from pymongo import MongoClient
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

MONGO_HOST = os.getenv('MONGO_HOST', 'mongodb')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USER = os.getenv('MONGO_USER', 'park_user')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'park_password')
MONGO_DB = os.getenv('MONGO_DB', 'park_guard')

def get_metrics():
    client = MongoClient(f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin")
    db = client[MONGO_DB]
    
    total_spaces = 5
    occupied = db.parking_spaces.count_documents({'is_occupied': True})
    available = total_spaces - occupied
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    access_granted = db.events.count_documents({
        'event_type': 'ACCESS_GRANTED',
        'timestamp': {'$gte': today_start}
    })
    
    access_denied = db.events.count_documents({
        'event_type': 'ACCESS_DENIED',
        'timestamp': {'$gte': today_start}
    })
    
    emergencies = db.events.count_documents({
        'event_type': 'EMERGENCY_TRIGGERED',
        'timestamp': {'$gte': today_start}
    })
    
    recent = list(db.events.find().sort('timestamp', -1).limit(10))
    for e in recent:
        e['_id'] = str(e['_id'])
        if 'timestamp' in e:
            e['timestamp'] = e['timestamp'].isoformat()
    
    return {
        'parking': {
            'total_spaces': total_spaces,
            'occupied_spaces': occupied,
            'available_spaces': available,
            'occupancy_percentage': round((occupied / total_spaces) * 100, 2)
        },
        'events': {
            'access_granted': access_granted,
            'access_denied': access_denied,
            'emergencies': emergencies
        },
        'recent_events': recent
    }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics' or self.path == '/api/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = get_metrics()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    print("Iniciando servidor de métricas en puerto 8080...")
    server = HTTPServer(('0.0.0.0', 8080), Handler)
    server.serve_forever()