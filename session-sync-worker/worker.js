// Cloudflare Worker: Session Sync para cockpit Valakhan (DM + Players)
// Pattern: SPEC del session-sync con role=dm/players, tokens separados,
// sin cuentas, polling 800ms, TTL 8h.
//
// Endpoints:
//   POST   /api/session/create
//   GET    /api/session/:sessionId?role=...&t=...
//   PATCH  /api/session/:sessionId/move?role=players&t=...
//   POST   /api/session/:sessionId/markers?role=dm&t=...
//   DELETE /api/session/:sessionId/markers/:markerId?role=dm&t=...
//   PATCH  /api/session/:sessionId/section?role=dm&t=...
//   POST   /api/session/:sessionId/reset?role=dm&t=...

const TTL_MS = 8 * 60 * 60 * 1000; // 8 horas
const VERSION = 'v1';

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PATCH, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
};

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS, ...extra },
  });
}

function nowIso() { return new Date().toISOString(); }
function rand(prefix) {
  const arr = new Uint8Array(8);
  crypto.getRandomValues(arr);
  const hex = Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join('');
  return `${prefix}_${hex}`;
}
function shortId() {
  const arr = new Uint8Array(4);
  crypto.getRandomValues(arr);
  return Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join('');
}
function keyFor(x, y) { return `${x},${y}`; }

// ============================================================================
// Durable Object: SessionDO
// ============================================================================
export class SessionDO {
  constructor(state, env) {
    this.state = state;
    this.storage = state.storage;
  }

  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // CORS preflight
    if (method === 'OPTIONS') return new Response(null, { headers: CORS });

    // INIT (create) — internal call from main worker after generating sessionId
    if (path === '/__init' && method === 'POST') {
      return this.init(await request.json());
    }

    // All other endpoints require auth
    const role = url.searchParams.get('role') || '';
    const token = url.searchParams.get('t') || '';
    const auth = await this.assertAuth(role, token);
    if (!auth.ok) return json({ error: auth.error }, auth.status || 401);

    // Route by path suffix
    if (path === '/' || path === '') {
      if (method === 'GET') return this.handleGet(role);
    }
    if (path === '/move' && method === 'PATCH') {
      return this.handleMove(role, await request.json());
    }
    if (path === '/markers' && method === 'POST') {
      return this.handleAddMarker(role, await request.json());
    }
    const mDelete = path.match(/^\/markers\/([^/]+)$/);
    if (mDelete && method === 'DELETE') {
      return this.handleDeleteMarker(role, mDelete[1]);
    }
    if (path === '/section' && method === 'PATCH') {
      return this.handleSection(role, await request.json());
    }
    if (path === '/reset' && method === 'POST') {
      return this.handleReset(role, await request.json());
    }

    return json({ error: 'Not found' }, 404);
  }

  async init(body) {
    const exists = await this.storage.get('data');
    if (exists) return json({ error: 'Session already initialized' }, 409);

    const { sessionId, moduleId, sectionId, startX, startY, partyFtPerTurn, cellFt } = body;
    if (!sessionId || !moduleId || !sectionId) {
      return json({ error: 'sessionId, moduleId, sectionId required' }, 400);
    }
    const sx = Number.isFinite(startX) ? startX : 1;
    const sy = Number.isFinite(startY) ? startY : 1;
    const k = keyFor(sx, sy);
    const dmToken = rand('dm');
    const playersToken = rand('pl');
    const expiresAt = new Date(Date.now() + TTL_MS).toISOString();

    const data = {
      sessionId,
      moduleId,
      sectionId,
      party: { x: sx, y: sy },
      seen: [k],
      visible: [k],
      steps: 0,
      turns: 0,
      minutes: 0,
      partyFtPerTurn: Number.isFinite(partyFtPerTurn) ? partyFtPerTurn : 240,
      cellFt: Number.isFinite(cellFt) ? cellFt : 10,
      markers: [],
      version: 1,
      updatedAt: nowIso(),
      expiresAt,
    };

    await this.storage.put('data', data);
    await this.storage.put('dmToken', dmToken);
    await this.storage.put('playersToken', playersToken);
    // schedule cleanup at expiration
    await this.storage.setAlarm(Date.now() + TTL_MS);

    return json({
      sessionId,
      dmToken,
      playersToken,
      expiresAt,
    });
  }

  async alarm() {
    // Session expired — clean up storage
    await this.storage.deleteAll();
  }

  async assertAuth(role, token) {
    if (role !== 'dm' && role !== 'players') {
      return { ok: false, error: 'Invalid role', status: 400 };
    }
    const data = await this.storage.get('data');
    if (!data) return { ok: false, error: 'Session not found', status: 404 };
    if (new Date(data.expiresAt).getTime() < Date.now()) {
      await this.storage.deleteAll();
      return { ok: false, error: 'Session expired', status: 410 };
    }
    const expected = role === 'dm'
      ? await this.storage.get('dmToken')
      : await this.storage.get('playersToken');
    if (token !== expected) return { ok: false, error: 'Invalid token', status: 401 };
    return { ok: true, data };
  }

  sanitize(data, role) {
    if (role === 'dm') return data;
    const { markers, ...rest } = data;
    return rest; // players nunca reciben markers
  }

  async getData() {
    return await this.storage.get('data');
  }

  async putData(data) {
    const next = {
      ...data,
      version: data.version + 1,
      updatedAt: nowIso(),
    };
    await this.storage.put('data', next);
    return next;
  }

  async handleGet(role) {
    const data = await this.getData();
    return json(this.sanitize(data, role));
  }

  async handleMove(role, body) {
    if (role !== 'players') return json({ error: 'Only players can move' }, 403);
    const dx = Number(body?.dx ?? 0);
    const dy = Number(body?.dy ?? 0);
    if (!Number.isInteger(dx) || !Number.isInteger(dy) || (Math.abs(dx) + Math.abs(dy)) !== 1) {
      return json({ error: 'Invalid move vector' }, 400);
    }
    const data = await this.getData();
    const nx = data.party.x + dx;
    const ny = data.party.y + dy;
    if (nx < 0 || ny < 0) return json({ error: 'Out of bounds' }, 409);

    const steps = data.steps + 1;
    const turns = (steps * data.cellFt) / data.partyFtPerTurn;
    const minutes = turns * 10;
    const seenSet = new Set(data.seen);
    seenSet.add(keyFor(nx, ny));

    // Optional: client-supplied visible (LoS computed client-side)
    let visible = [keyFor(nx, ny)];
    if (Array.isArray(body?.visible)) {
      visible = body.visible.filter(v => typeof v === 'string').slice(0, 200);
    }
    // Optional: client-supplied seen (LoS adds visible cells to history)
    if (Array.isArray(body?.seen)) {
      for (const k of body.seen) {
        if (typeof k === 'string') seenSet.add(k);
      }
    }

    const next = await this.putData({
      ...data,
      party: { x: nx, y: ny },
      steps,
      turns,
      minutes,
      seen: Array.from(seenSet),
      visible,
    });
    return json({ ok: true, state: this.sanitize(next, role) });
  }

  async handleAddMarker(role, body) {
    if (role !== 'dm') return json({ error: 'Only DM can add markers' }, 403);
    const x = Number(body?.x);
    const y = Number(body?.y);
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      return json({ error: 'Invalid coords' }, 400);
    }
    const marker = {
      id: 'm_' + shortId(),
      x,
      y,
      label: String(body?.label ?? 'Marker').slice(0, 60),
      color: body?.color ? String(body.color).slice(0, 20) : 'red',
    };
    const data = await this.getData();
    const next = await this.putData({
      ...data,
      markers: [...data.markers, marker],
    });
    return json({ ok: true, marker, state: next });
  }

  async handleDeleteMarker(role, markerId) {
    if (role !== 'dm') return json({ error: 'Only DM can delete markers' }, 403);
    const data = await this.getData();
    const next = await this.putData({
      ...data,
      markers: data.markers.filter(m => m.id !== markerId),
    });
    return json({ ok: true, state: next });
  }

  async handleSection(role, body) {
    if (role !== 'dm') return json({ error: 'Only DM can change section' }, 403);
    const sectionId = String(body?.sectionId ?? '');
    if (!sectionId) return json({ error: 'sectionId required' }, 400);
    const sx = Number.isFinite(body?.startX) ? body.startX : 1;
    const sy = Number.isFinite(body?.startY) ? body.startY : 1;
    const clearMarkers = Boolean(body?.clearMarkers ?? true); // default true al cambiar sección
    const k = keyFor(sx, sy);
    const data = await this.getData();
    const next = await this.putData({
      ...data,
      sectionId,
      party: { x: sx, y: sy },
      seen: [k],
      visible: [k],
      steps: 0,
      turns: 0,
      minutes: 0,
      markers: clearMarkers ? [] : data.markers,
    });
    return json({ ok: true, state: next });
  }

  async handleReset(role, body) {
    if (role !== 'dm') return json({ error: 'Only DM can reset session' }, 403);
    const data = await this.getData();
    const sx = Number.isFinite(body?.startX) ? body.startX : data.party.x;
    const sy = Number.isFinite(body?.startY) ? body.startY : data.party.y;
    const clearMarkers = Boolean(body?.clearMarkers ?? false);
    const k = keyFor(sx, sy);
    const next = await this.putData({
      ...data,
      party: { x: sx, y: sy },
      seen: [k],
      visible: [k],
      steps: 0,
      turns: 0,
      minutes: 0,
      markers: clearMarkers ? [] : data.markers,
    });
    return json({ ok: true, state: next });
  }
}

// ============================================================================
// Main Worker (entry)
// ============================================================================
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS preflight
    if (request.method === 'OPTIONS') return new Response(null, { headers: CORS });

    // Health check
    if (path === '/' || path === '/health') {
      return json({ ok: true, version: VERSION, ts: nowIso() });
    }

    // POST /api/session/create — bootstrap
    if (path === '/api/session/create' && request.method === 'POST') {
      let body = {};
      try { body = await request.json(); } catch {}
      const moduleId = String(body?.moduleId ?? '').slice(0, 60);
      const sectionId = String(body?.sectionId ?? '').slice(0, 60);
      if (!moduleId || !sectionId) {
        return json({ error: 'moduleId and sectionId are required' }, 400);
      }
      // sessionId con prefix legible: bm-XXXXX (bm = barrowmaze, X = hex random)
      const prefix = moduleId.slice(0, 4).replace(/[^a-z0-9]/gi, '');
      const sessionId = `${prefix || 'sess'}-${shortId()}`;
      const id = env.SESSIONS.idFromName(sessionId);
      const stub = env.SESSIONS.get(id);
      const initRes = await stub.fetch('https://do/__init', {
        method: 'POST',
        body: JSON.stringify({
          sessionId,
          moduleId,
          sectionId,
          startX: body?.startX,
          startY: body?.startY,
          partyFtPerTurn: body?.partyFtPerTurn,
          cellFt: body?.cellFt,
        }),
      });
      if (!initRes.ok) return new Response(initRes.body, { status: initRes.status, headers: { ...CORS, 'Content-Type': 'application/json' } });
      const initData = await initRes.json();

      return json({
        sessionId,
        dmToken: initData.dmToken,
        playersToken: initData.playersToken,
        expiresAt: initData.expiresAt,
        // URLs absolutas requieren saber el origin del cockpit;
        // el cliente puede construir las URLs con su propio location.
        dmPath: `/cockpit?sessionId=${encodeURIComponent(sessionId)}&role=dm&t=${encodeURIComponent(initData.dmToken)}`,
        playersPath: `/cockpit?sessionId=${encodeURIComponent(sessionId)}&role=players&t=${encodeURIComponent(initData.playersToken)}`,
      });
    }

    // Routes /api/session/:sessionId/*
    const m = path.match(/^\/api\/session\/([^/]+)(\/.*)?$/);
    if (m) {
      const sessionId = m[1];
      const rest = m[2] || '/';
      const id = env.SESSIONS.idFromName(sessionId);
      const stub = env.SESSIONS.get(id);
      // Forward to DO with rest as path; preserve query string
      const doUrl = new URL('https://do' + rest);
      for (const [k, v] of url.searchParams) doUrl.searchParams.set(k, v);
      const doReq = new Request(doUrl.toString(), {
        method: request.method,
        headers: request.headers,
        body: ['GET', 'HEAD'].includes(request.method) ? undefined : await request.clone().text(),
      });
      const res = await stub.fetch(doReq);
      // Wrap response to ensure CORS headers
      const newHeaders = new Headers(res.headers);
      for (const [k, v] of Object.entries(CORS)) newHeaders.set(k, v);
      return new Response(res.body, { status: res.status, headers: newHeaders });
    }

    return json({ error: 'Not found' }, 404);
  },
};
