const { MongoClient } = require('mongodb');

const mongoHost = process.env.MONGO_HOST || 'mongodb';
const mongoPort = process.env.MONGO_PORT || 27017;
const mongoUser = process.env.MONGO_USER || 'park_user';
const mongoPassword = process.env.MONGO_PASSWORD || 'park_password';
const mongoDb = process.env.MONGO_DB || 'park_guard';

const uri = `mongodb://${mongoUser}:${mongoPassword}@${mongoHost}:${mongoPort}/?authSource=admin`;

function buildDailyBuckets(days) {
  const buckets = [];
  const now = new Date();
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  start.setDate(start.getDate() - (days - 1));

  for (let i = 0; i < days; i += 1) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    const yyyyMmDd = d.toISOString().slice(0, 10);
    buckets.push({ key: yyyyMmDd, iso: `${yyyyMmDd}T00:00:00.000Z` });
  }

  return { buckets, start };
}

function parseEventTimestamp(value) {
  if (!value) return null;
  if (value instanceof Date) return value;
  if (typeof value !== 'string') return null;

  // Normalize microseconds (e.g. .123456) to milliseconds (.123) for JS Date parsing.
  let normalized = value.replace(/\.(\d{3})\d+$/, '.$1');
  // If timezone is missing, assume UTC to avoid local/UTC day drift.
  if (!/[zZ]|[+-]\d{2}:\d{2}$/.test(normalized)) {
    normalized = `${normalized}Z`;
  }
  const ts = new Date(normalized);
  return Number.isNaN(ts.getTime()) ? null : ts;
}

async function getMetrics() {
  const client = new MongoClient(uri);
  try {
    await client.connect();
    const db = client.db(mongoDb);
    
    const totalSpaces = 5;
    const occupiedDistinctSpaces = await db.collection('parking_spaces').distinct('space_number', {
      is_occupied: true,
      space_number: { $gte: 1, $lte: totalSpaces }
    });
    const occupied = Math.min(totalSpaces, occupiedDistinctSpaces.length);
    const available = Math.max(0, totalSpaces - occupied);
    
    const todayStart = new Date();
    todayStart.setHours(0, 0, 0, 0);
    
    const trackedTypes = [
      'ACCESS_GRANTED',
      'access_granted',
      'ACCESS_DENIED',
      'access_denied',
      'EMERGENCY_TRIGGERED',
      'emergency_alert'
    ];
    
    const recentEvents = await db.collection('events')
      .find()
      .sort({ timestamp: -1 })
      .limit(10)
      .toArray();

    const lastGasReading = await db.collection('statistics')
      .find({ type: 'gas_reading' })
      .sort({ timestamp: -1 })
      .limit(1)
      .toArray();
    const gasPpm = lastGasReading.length > 0 ? Number(lastGasReading[0].ppm || 0) : 0;
    
    const processedEvents = recentEvents.map(e => {
      const rawType = e.event_type || 'UNKNOWN';
      const eventTypeEsMap = {
        ACCESS_GRANTED: 'Acceso autorizado',
        access_granted: 'Acceso autorizado',
        ACCESS_DENIED: 'Acceso denegado',
        access_denied: 'Acceso denegado',
        EMERGENCY_TRIGGERED: 'Emergencia',
        emergency_alert: 'Emergencia'
      };

      const obj = {
        _id: e._id ? e._id.toString() : 'unknown',
        event_type: rawType,
        event_type_es: eventTypeEsMap[rawType] || 'Evento',
        user_id: e.user_id || null,
        space_number: e.space_number || null,
        details: e.details || {}
      };
      if (e.timestamp) {
        const parsedTs = parseEventTimestamp(e.timestamp);
        obj.timestamp = parsedTs ? parsedTs.toISOString() : String(e.timestamp);
      }
      return obj;
    });

    const { buckets, start } = buildDailyBuckets(30);
    const historicalEvents = await db.collection('events')
      .find({ event_type: { $in: trackedTypes } })
      .toArray();

    const grantedMap = new Map(buckets.map((b) => [b.key, 0]));
    const deniedMap = new Map(buckets.map((b) => [b.key, 0]));
    const emergencyMap = new Map(buckets.map((b) => [b.key, 0]));
    let accessGranted = 0;
    let accessDenied = 0;
    let emergencies = 0;
    let gatesOpenedToday = 0;
    let gatesClosedToday = 0;
    let fanOnToday = 0;
    let fanOffToday = 0;

    historicalEvents.forEach((event) => {
      const ts = parseEventTimestamp(event.timestamp);
      if (!ts) return;
      if (ts < start) return;

      const dayKey = ts.toISOString().slice(0, 10);
      const type = event.event_type;
      const isToday = ts >= todayStart;

      if (type === 'ACCESS_GRANTED' || type === 'access_granted') {
        grantedMap.set(dayKey, (grantedMap.get(dayKey) || 0) + 1);
        if (isToday) accessGranted += 1;
      } else if (type === 'ACCESS_DENIED' || type === 'access_denied') {
        deniedMap.set(dayKey, (deniedMap.get(dayKey) || 0) + 1);
        if (isToday) accessDenied += 1;
      } else if (type === 'EMERGENCY_TRIGGERED' || type === 'emergency_alert') {
        emergencyMap.set(dayKey, (emergencyMap.get(dayKey) || 0) + 1);
        if (isToday) emergencies += 1;
      }
    });

    const doorEvents = await db.collection('events')
      .find({ event_type: 'door_update' })
      .toArray();

    doorEvents.forEach((event) => {
      const ts = parseEventTimestamp(event.timestamp);
      if (!ts) return;
      if (ts < todayStart) return;

      if (event.is_open === true) gatesOpenedToday += 1;
      if (event.is_open === false) gatesClosedToday += 1;
    });

    const fanStats = await db.collection('statistics')
      .find({ type: 'ventilator_status' })
      .toArray();

    fanStats.forEach((item) => {
      const ts = parseEventTimestamp(item.timestamp);
      if (!ts) return;
      if (ts < todayStart) return;
      if (item.is_active === true) fanOnToday += 1;
      if (item.is_active === false) fanOffToday += 1;
    });

    const history = {
      access_granted_daily: buckets.map((b) => ({ date: b.iso, count: grantedMap.get(b.key) || 0 })),
      access_denied_daily: buckets.map((b) => ({ date: b.iso, count: deniedMap.get(b.key) || 0 })),
      emergencies_daily: buckets.map((b) => ({ date: b.iso, count: emergencyMap.get(b.key) || 0 }))
    };
    
    return {
      parking: {
        total_spaces: totalSpaces,
        occupied_spaces: occupied,
        available_spaces: available,
        occupancy_percentage: Math.round((occupied / totalSpaces) * 100 * 100) / 100
      },
      gas: {
        ppm: gasPpm
      },
      events: {
        access_granted: accessGranted,
        access_denied: accessDenied,
        emergencies: emergencies
      },
      gates: {
        opened_today: gatesOpenedToday,
        closed_today: gatesClosedToday
      },
      ventilator: {
        on_today: fanOnToday,
        off_today: fanOffToday
      },
      recent_events: processedEvents,
      history
    };
  } finally {
    await client.close();
  }
}

const http = require('http');
const server = http.createServer(async (req, res) => {
  if (req.url === '/metrics' || req.url === '/api/metrics') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }
    
    try {
      const metrics = await getMetrics();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(metrics));
    } catch (e) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: e.message }));
    }
  } else {
    res.writeHead(404);
    res.end();
  }
});

server.listen(8080, '0.0.0.0', () => {
  console.log('Metrics server running on port 8080');
});
