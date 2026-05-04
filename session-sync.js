// Session Sync layer para cockpit Valakhan.
// Activa cuando la URL tiene ?sessionId=...&role=...&t=...
// Sincroniza state via Worker en mc-prism-session.marcoscabobianco.workers.dev.

(function(){
  const SYNC_VERSION = 'v6k10p14'; // bump cada deploy de session-sync.js para verificar live
  const API_BASE_HOST = 'https://mc-prism-session.marcoscabobianco.workers.dev';
  // V6k10.7: track wallmap-loaded localmente porque el cockpit usa `let`
  // (no `var`), así que window._realWallmap NUNCA es accesible. Bug en boot prev.
  let _wallmapReady = false;
  let _wallmapInfo = null; // {cols, rows, sala_74A_cell}
  // V6k10.8: GRID_DIRECTIONS tampoco está en window (es const local del cockpit).
  // Defino mi propia tabla — debe matchear EXACTAMENTE la del cockpit.
  const DIRS = {
    up:    { dx: 0,  dy: -1 },
    down:  { dx: 0,  dy: 1  },
    left:  { dx: -1, dy: 0  },
    right: { dx: 1,  dy: 0  },
  };
  const url = new URL(location.href);
  const sessionId = url.searchParams.get('sessionId');
  const role = url.searchParams.get('role');
  const token = url.searchParams.get('t');

  // Expose helper for non-session UI (create-session button)
  window._sessionApi = {
    create(body) {
      return fetch(`${API_BASE_HOST}/api/session/create`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body || {}),
      }).then(r => r.json());
    },
    apiBase: API_BASE_HOST,
  };

  if (!sessionId || !role || !token) return; // standalone mode
  if (role !== 'dm' && role !== 'players') return;

  console.log(`[Session] Activo: ${sessionId} | role=${role}`);

  const API_BASE = `${API_BASE_HOST}/api/session/${encodeURIComponent(sessionId)}`;
  let _state = null;
  let _localVersion = 0;
  let _badgeEl = null;
  let _markersEl = null;

  // ---- body classes for role-based hiding ----
  document.body.classList.add('session-mode');
  document.body.classList.add('session-' + role);

  // ---- inject CSS for role-based hiding ----
  const css = `
    body.session-mode .session-badge {
      position: fixed; top: calc(8px + var(--safe-top)); right: 8px;
      z-index: 9000; padding: 6px 10px; border-radius: 14px;
      font-size: 11px; font-weight: bold;
      background: rgba(0,0,0,0.85); border: 1px solid var(--accent);
      color: var(--accent); display: flex; gap: 6px; align-items: center;
      max-width: 180px; pointer-events: auto;
    }
    body.session-dm .session-badge { border-color: #5dade2; color: #5dade2; }
    body.session-players .session-badge { border-color: #7eef87; color: #7eef87; }
    body.session-players .session-hide-players,
    body.session-players #_dg-room-modal,
    body.session-players #toggle-markers-btn {
      display: none !important;
    }
    /* Hide the inline DM toggle button (no specific id, target by onclick) */
    body.session-players button[onclick*="gridToggleDM"] {
      display: none !important;
    }
    /* Hide Ctrl+click DM hint texts and similar DM-only controls in players */
    body.session-players .mode-btn[data-mode-key="encounter"],
    body.session-players .mode-btn[data-mode-key="bestiary"] {
      opacity: 0.4; pointer-events: none;
    }
  `;
  const styleEl = document.createElement('style');
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  // ---- session badge ----
  function ensureBadge() {
    if (_badgeEl) return _badgeEl;
    const b = document.createElement('div');
    b.className = 'session-badge';
    b.id = 'session-badge';
    const roleLabel = role === 'dm' ? '🛡 DM' : '🎲 Players';
    // Compact line 1 (role + status), line 2 (sync version + module + sessionId short)
    b.innerHTML =
      `<div>${roleLabel} · <span id="session-status">conectando…</span> · <a href="#" id="session-diag-toggle" style="color:inherit;text-decoration:underline;">diag</a></div>` +
      `<div style="font-size:9px;opacity:0.85;margin-top:3px;font-family:monospace;">sync ${SYNC_VERSION} · <span id="session-module">…</span> · <span id="session-shortid">${(sessionId||'').slice(-8)}</span></div>`;
    document.body.appendChild(b);
    _badgeEl = b;
    setTimeout(() => {
      const t = document.getElementById('session-diag-toggle');
      if (t) t.onclick = (e) => { e.preventDefault(); toggleDiag(); };
    }, 100);
    return b;
  }

  function setStatus(s, color) {
    const el = document.getElementById('session-status');
    if (el) {
      el.textContent = s;
      if (color) el.style.color = color;
    }
  }

  // ---- in-app diagnostic panel (avoids needing devtools on iPad) ----
  let _diagOpen = false;
  let _diagLog = [];
  function ensureDiag() {
    let p = document.getElementById('session-diag-panel');
    if (p) return p;
    p = document.createElement('div');
    p.id = 'session-diag-panel';
    p.style.cssText = 'position:fixed;top:60px;right:8px;width:320px;max-height:60vh;overflow-y:auto;background:rgba(0,0,0,0.92);color:#7eef87;font-family:monospace;font-size:11px;padding:10px;border:1px solid #5dade2;border-radius:6px;z-index:9999;display:none;line-height:1.4;';
    p.innerHTML = '<div style="display:flex;gap:6px;margin-bottom:6px;"><b style="color:#d4a04a;flex:1;">DIAG</b><button onclick="document.getElementById(\'session-diag-panel\').style.display=\'none\';" style="background:#c44a3a;color:#fff;border:0;padding:2px 8px;border-radius:3px;cursor:pointer;">x</button></div><div id="session-diag-state"></div><hr style="border:0;border-top:1px solid #444;margin:6px 0;"><div id="session-diag-log" style="max-height:30vh;overflow-y:auto;"></div>';
    document.body.appendChild(p);
    return p;
  }
  function toggleDiag() {
    _diagOpen = !_diagOpen;
    const p = ensureDiag();
    p.style.display = _diagOpen ? 'block' : 'none';
    if (_diagOpen) refreshDiagState();
  }
  function refreshDiagState() {
    const s = document.getElementById('session-diag-state');
    if (!s) return;
    const g = (typeof window.gridState === 'function') ? window.gridState() : null;
    const lines = [];
    lines.push('SYNC version: ' + SYNC_VERSION);
    lines.push('Cockpit ver: ' + (window._COCKPIT_VERSION || '?'));
    lines.push('role: ' + role);
    lines.push('sessionId: ' + sessionId);
    lines.push('localVersion: ' + _localVersion);
    lines.push('apiBase: ' + API_BASE);
    lines.push('---');
    if (_state) {
      lines.push('moduleId: ' + (_state.moduleId || '?'));
      lines.push('sectionId: ' + (_state.sectionId || '?'));
      lines.push('---');
    }
    lines.push('typeof gridState: ' + typeof window.gridState);
    lines.push('typeof gridMoveReal: ' + typeof window.gridMoveReal);
    lines.push('typeof gridIsWalkableReal: ' + typeof window.gridIsWalkableReal);
    lines.push('typeof gridLoadRealMap: ' + typeof window.gridLoadRealMap);
    lines.push('typeof dgAdvance: ' + typeof window.dgAdvance);
    lines.push('typeof loadDungeon: ' + typeof window.loadDungeon);
    lines.push('state.dungeon: ' + (window.state && window.state.dungeon ? window.state.dungeon.id + ' (turns=' + window.state.dungeon.turns + ', torch=' + window.state.dungeon.torchTurnsLeft + ')' : 'NULL'));
    lines.push('wallmap ready (local): ' + (_wallmapReady ? 'YES ✓' : 'NO'));
    if (_wallmapInfo) {
      lines.push('  cols×rows: ' + _wallmapInfo.cols + '×' + _wallmapInfo.rows);
      lines.push('  sala_74A_cell: ' + JSON.stringify(_wallmapInfo.sala_74A_cell));
    }
    // Probe gridIsWalkableReal indirectly: if wallmap loaded internally, this
    // should return true for sala 74A and false for (-1,-1).
    if (typeof window.gridIsWalkableReal === 'function') {
      try {
        const a = window.gridIsWalkableReal(32, 84);
        const b = window.gridIsWalkableReal(-1, -1);
        lines.push('  probe walkable(32,84): ' + a + ' | (-1,-1): ' + b);
      } catch(e) {
        lines.push('  probe error: ' + e);
      }
    }
    lines.push('---');
    if (g) {
      lines.push('gridState.realPlayer: ' + JSON.stringify(g.realPlayer));
      lines.push('gridState.realTail: ' + JSON.stringify(g.realTail));
      lines.push('gridState.dmView: ' + g.dmView);
      lines.push('gridState.steps: ' + g.steps);
      lines.push('gridState.realSeen.length: ' + (g.realSeen ? g.realSeen.length : 'null'));
    } else {
      lines.push('gridState: NULL');
    }
    if (_state) {
      lines.push('---');
      lines.push('SERVER party: ' + JSON.stringify(_state.party));
      lines.push('SERVER version: ' + _state.version);
      lines.push('SERVER steps: ' + _state.steps);
      lines.push('SERVER markers count: ' + (_state.markers ? _state.markers.length : 'N/A'));
    }
    s.innerHTML = lines.map(l => '<div>' + l.replace(/</g,'&lt;') + '</div>').join('');
  }
  function diag(tag, msg) {
    const ts = new Date().toLocaleTimeString();
    _diagLog.unshift(`[${ts}] ${tag}: ${msg}`);
    if (_diagLog.length > 60) _diagLog.length = 60;
    const el = document.getElementById('session-diag-log');
    if (el) el.innerHTML = _diagLog.map(l => '<div style="border-bottom:1px solid #222;padding:2px 0;">' + l.replace(/</g,'&lt;') + '</div>').join('');
    if (_diagOpen) refreshDiagState();
    try { console.log('[Session] ' + tag + ': ' + msg); } catch(e){}
  }
  // Periodic refresh of diag state if open
  setInterval(() => { if (_diagOpen) refreshDiagState(); }, 500);
  // Expose for users to open from any tap
  window._sessionDiag = toggleDiag;

  // ---- V6k10.13: light source overlay (oscuridad total) ----
  let _darkOverlayEl = null;
  function ensureDarkOverlay() {
    if (_darkOverlayEl) return _darkOverlayEl;
    const o = document.createElement('div');
    o.id = 'session-dark-overlay';
    o.style.cssText = 'position:fixed;inset:0;background:#000;z-index:9990;display:none;flex-direction:column;align-items:center;justify-content:center;color:#7eef87;font-family:Georgia,serif;text-align:center;padding:30px;';
    o.innerHTML =
      '<div style="font-size:64px;margin-bottom:20px;">🌑</div>' +
      '<div style="font-size:28px;font-weight:bold;letter-spacing:2px;margin-bottom:14px;">OSCURIDAD TOTAL</div>' +
      '<div style="font-size:16px;color:#a8967a;max-width:400px;line-height:1.5;">Esperá las instrucciones del DM. Tu antorcha se apagó o algo bloqueó la luz.</div>';
    document.body.appendChild(o);
    _darkOverlayEl = o;
    return o;
  }
  function applyLightSource(lightSource) {
    const isDark = (lightSource === 'dark');
    // Players: overlay fullscreen negro
    if (role === 'players') {
      const o = ensureDarkOverlay();
      o.style.display = isDark ? 'flex' : 'none';
    }
    // DM: indicador discreto si players a ciegas
    if (role === 'dm') {
      let ind = document.getElementById('session-dm-light-indicator');
      if (!ind) {
        ind = document.createElement('div');
        ind.id = 'session-dm-light-indicator';
        ind.style.cssText = 'position:fixed;top:80px;right:8px;z-index:9000;padding:6px 10px;border-radius:14px;font-size:11px;font-weight:bold;background:rgba(0,0,0,0.85);border:1px solid #c44a3a;color:#c44a3a;';
        document.body.appendChild(ind);
      }
      if (isDark) {
        ind.style.display = 'block';
        ind.textContent = '🌑 Players a ciegas';
      } else {
        ind.style.display = 'none';
      }
    }
  }

  // ---- V6k10.14: pending event overlay (sorpresa / combate / narrativa) ----
  let _eventOverlayEl = null;
  let _activeEventId = null;
  function ensureEventOverlay() {
    if (_eventOverlayEl) return _eventOverlayEl;
    const o = document.createElement('div');
    o.id = 'session-event-overlay';
    o.style.cssText = 'position:fixed;inset:0;z-index:9995;display:none;flex-direction:column;align-items:center;justify-content:center;color:#fff;font-family:Georgia,serif;text-align:center;padding:30px;animation:none;';
    o.innerHTML =
      '<div id="se-emoji" style="font-size:96px;margin-bottom:24px;animation:pulseEmoji 0.6s ease-in-out infinite alternate;">⚔</div>' +
      '<div id="se-title" style="font-size:48px;font-weight:bold;letter-spacing:6px;margin-bottom:18px;text-shadow:0 2px 12px rgba(0,0,0,0.8);">SORPRESA</div>' +
      '<div id="se-subtitle" style="font-size:20px;max-width:600px;line-height:1.5;text-shadow:0 1px 6px rgba(0,0,0,0.8);"></div>';
    document.body.appendChild(o);
    // Animation keyframes
    if (!document.getElementById('session-event-keyframes')) {
      const style = document.createElement('style');
      style.id = 'session-event-keyframes';
      style.textContent =
        '@keyframes pulseEmoji { from { transform: scale(1); } to { transform: scale(1.2); } }' +
        '@keyframes fadeInEvent { from { opacity: 0; transform: scale(0.8); } to { opacity: 1; transform: scale(1); } }' +
        '#session-event-overlay.show { display:flex !important; animation: fadeInEvent 0.4s ease-out; }';
      document.head.appendChild(style);
    }
    return o;
  }
  function showEventOverlay(evt) {
    if (!evt || _activeEventId === evt.id) return;
    _activeEventId = evt.id;
    const o = ensureEventOverlay();
    o.style.background = 'radial-gradient(ellipse at center, ' + (evt.color || '#c44a3a') + ' 0%, #000 80%)';
    document.getElementById('se-emoji').textContent = evt.emoji || '⚔';
    document.getElementById('se-title').textContent = evt.title || 'EVENTO';
    document.getElementById('se-subtitle').textContent = evt.subtitle || '';
    o.classList.add('show');
    diag('event-show', evt.type + ' ' + evt.title);
    setTimeout(() => {
      o.classList.remove('show');
      o.style.display = 'none';
      // Ack event server-side so it doesn't replay
      fetch(`${API_BASE}/event/ack?role=${role}&t=${encodeURIComponent(token)}`, { method: 'POST' })
        .then(r => r.json())
        .then(d => diag('event-ack', d.ok ? 'cleared' : 'err'))
        .catch(e => diag('event-ack-err', String(e)));
    }, evt.durationMs || 4000);
  }

  // ---- apply server state to local UI ----
  function applyServerState(state) {
    _state = state;
    _localVersion = state.version || 0;
    const g = (typeof window.gridState === 'function') ? window.gridState() : null;
    if (!g) {
      // gridState may not be ready yet; try again later
      return;
    }
    // V6k10.10: detect step delta to trigger dgAdvance() for turn boundaries crossed
    // by the OTHER device. Without this, only the device that moves sees wandering
    // checks / antorcha / atardecer alerts. DM (passive) needs the same alerts.
    const oldSteps = g.steps || 0;
    const newSteps = state.steps || 0;
    const stepDelta = newSteps - oldSteps;

    // V6k10.3: sync realPlayer + reset realTail to current pos (avoids ghost markers)
    g.realPlayer = { x: state.party.x, y: state.party.y };
    g.realTail = { x: state.party.x, y: state.party.y };
    g.realSeen = state.seen || [];
    g.steps = newSteps;
    g.cellFt = state.cellFt || 10;
    g.partyFtPerTurn = state.partyFtPerTurn || 120;

    // V6k10.12: dgAdvance() (wandering checks + antorcha + atardecer + traps)
    // SOLO se ejecuta en role=dm. El DM es la fuente de verdad para mecánicas
    // de turno. Players solo ve party + steps + minutes (server-tracked).
    // Esto evita: doble roll, desincronía, players viendo banners DM-internos.
    if (role === 'dm' && stepDelta > 0 && state.cellFt > 0 && state.partyFtPerTurn > 0) {
      const tps = state.cellFt / Math.max(1, state.partyFtPerTurn);
      const crossed = Math.floor(newSteps * tps) - Math.floor(oldSteps * tps);
      if (crossed > 0) {
        const hasDungeon = (typeof window.state !== 'undefined' && window.state.dungeon);
        diag('dm-advance', 'cross ' + crossed + ' turn(s) (delta ' + stepDelta + ') hasDungeon=' + !!hasDungeon);
        if (typeof window.dgAdvance === 'function') {
          if (!hasDungeon && typeof window.loadDungeon === 'function') {
            try { window.loadDungeon('barrowmaze'); }
            catch(e) { diag('advance-err', 'loadDungeon: ' + e); }
          }
          for (let i = 0; i < crossed; i++) {
            try { window.dgAdvance(); }
            catch(e) { diag('advance-err', String(e)); }
          }
          if (typeof window.renderGridCrawler === 'function') {
            try { window.renderGridCrawler(); } catch(e){}
          }
        }
      }
    }
    // Force DM/players view based on role
    g.dmView = (role === 'dm');

    // Apply markers (only for DM — players have no markers field)
    if (Array.isArray(state.markers)) {
      g.sessionMarkers = state.markers;
    } else {
      g.sessionMarkers = [];
    }

    // Trigger redraw
    if (typeof window.redrawGridRealCanvas === 'function') {
      try { window.redrawGridRealCanvas(); } catch(e){}
    }
    // Update topbar info
    const elPos = document.getElementById('grid-real-pos');
    if (elPos) elPos.textContent = '(' + state.party.x + ',' + state.party.y + ')';
    const elSeen = document.getElementById('grid-real-seen');
    if (elSeen) elSeen.textContent = (state.seen || []).length;

    setStatus(`v${state.version} · ${(state.minutes||0).toFixed(1)}min`, '');
    // Update module label in badge
    const m = document.getElementById('session-module');
    if (m && state.moduleId) {
      m.textContent = state.moduleId + '/' + (state.sectionId || '?');
    }
    // V6k10.13: apply lightSource (oscuridad total para players)
    applyLightSource(state.lightSource || 'lit');
    // V6k10.14: show pendingEvent if there's a new one (only for players to see surprise)
    if (state.pendingEvent && role === 'players') {
      showEventOverlay(state.pendingEvent);
    }
    // DM also sees event briefly to confirm it was pushed
    if (state.pendingEvent && role === 'dm' && _activeEventId !== state.pendingEvent.id) {
      // DM gets a smaller toast instead of fullscreen overlay
      _activeEventId = state.pendingEvent.id;
      if (typeof window.dgToast === 'function') {
        window.dgToast('🎬 Evento enviado a players: ' + state.pendingEvent.title, 'info');
      }
    }
  }

  // ---- pull state from server ----
  let _consecutiveErrors = 0;
  function fetchState() {
    return fetch(`${API_BASE}?role=${role}&t=${encodeURIComponent(token)}`, { cache: 'no-store' })
      .then(r => r.json())
      .then(state => {
        if (state.error) throw new Error(state.error);
        _consecutiveErrors = 0;
        if (!_state || state.version !== _localVersion) {
          applyServerState(state);
        }
        return state;
      })
      .catch(err => {
        _consecutiveErrors++;
        const msg = _consecutiveErrors > 3 ? `error: ${err.message||err}` : 'reintentando…';
        setStatus(msg, '#c44a3a');
        throw err;
      });
  }

  // ---- override gridMoveReal: split por rol ----
  // V6k10.12: DM delega al original (dispara dgAdvance + dgCheckTrapAtCell + alerts).
  //           Players usa move-lite (solo mueve + reveal + redraw, NO advance).
  // El DM es la fuente de verdad para mecánicas de turno.
  // Players solo ven movement/seen, server tracks steps/minutes.
  function patchGridMove() {
    if (typeof window.gridMoveReal !== 'function') return false;
    const original = window.gridMoveReal;

    function syncMoveToServer(dx, dy, g) {
      fetch(`${API_BASE}/move?role=${role}&t=${encodeURIComponent(token)}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          dx, dy,
          visible: Array.isArray(g.realSeen) ? g.realSeen.slice(-50) : [],
          seen: Array.isArray(g.realSeen) ? g.realSeen : [],
        }),
      })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          diag('move-err', data.error);
          if (typeof window.dgToast === 'function') window.dgToast('Sync: ' + data.error, 'error');
          return;
        }
        if (data.state) {
          _state = data.state;
          _localVersion = data.state.version;
          setStatus(`v${data.state.version} · ${(data.state.minutes||0).toFixed(1)}min`, '');
          diag('move-ok', 'v' + data.state.version + ' (' + data.state.party.x + ',' + data.state.party.y + ')');
        }
      })
      .catch(err => diag('move-err', String(err)));
    }

    window.gridMoveReal = function(dir) {
      diag('move', 'gridMoveReal(' + dir + ') role=' + role);
      const g = window.gridState();
      if (!g) { diag('move-fail', 'gridState() null'); return; }
      if (!_wallmapReady) { diag('move-fail', 'wallmap not ready'); return; }
      const d = DIRS[dir];
      if (!d) { diag('move-fail', 'unknown dir ' + dir); return; }

      const beforeX = g.realPlayer.x;
      const beforeY = g.realPlayer.y;

      if (role === 'dm') {
        // DM: delegar al original. Dispara dgAdvance, dgCheckTrapAtCell, todo.
        try { original.call(this, dir); }
        catch (e) { diag('move-err', 'original threw: ' + e); return; }
      } else {
        // PLAYERS: move-lite. Sin dgAdvance, sin dgCheckTrapAtCell, sin alerts.
        // Solo move visual + reveal + redraw.
        const nx = beforeX + d.dx;
        const ny = beforeY + d.dy;
        if (typeof window.gridIsWalkableReal === 'function' && !window.gridIsWalkableReal(nx, ny)) {
          diag('move-block', '(' + nx + ',' + ny + ') NOT walkable');
          if (typeof window.dgToast === 'function') window.dgToast('Celda no transitable', 'info');
          return;
        }
        g.realTail = { x: beforeX, y: beforeY };
        g.realPlayer = { x: nx, y: ny };
        g.steps = (g.steps || 0) + 1;
        if (typeof window.gridRevealFromReal === 'function') {
          try { window.gridRevealFromReal(nx, ny, 3); } catch(e){}
        }
        if (typeof window.redrawGridRealCanvas === 'function') {
          try { window.redrawGridRealCanvas(); } catch(e){}
        }
      }

      // Verificar si la pos cambió
      const dx = g.realPlayer.x - beforeX;
      const dy = g.realPlayer.y - beforeY;
      if (dx === 0 && dy === 0) {
        diag('move-block', 'sin movimiento neto');
        return;
      }

      syncMoveToServer(dx, dy, g);
    };
    return true;
  }

  // ---- sessionAddMarker (DM API for placing markers) ----
  window.sessionAddMarker = function(x, y, label, color) {
    if (role !== 'dm') return Promise.reject(new Error('Only DM'));
    return fetch(`${API_BASE}/markers?role=dm&t=${encodeURIComponent(token)}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({x, y, label: label||'Marker', color: color||'red'}),
    })
    .then(r => r.json())
    .then(data => {
      if (data.state) applyServerState(data.state);
      return data;
    });
  };

  window.sessionDeleteMarker = function(markerId) {
    if (role !== 'dm') return Promise.reject(new Error('Only DM'));
    return fetch(`${API_BASE}/markers/${encodeURIComponent(markerId)}?role=dm&t=${encodeURIComponent(token)}`, {
      method: 'DELETE',
    })
    .then(r => r.json())
    .then(data => {
      if (data.state) applyServerState(data.state);
      return data;
    });
  };

  // V6k10.13: DM toggle de luz
  window.sessionToggleLight = function(lightSource) {
    if (role !== 'dm') return Promise.reject(new Error('Only DM'));
    const target = lightSource || (_state && _state.lightSource === 'dark' ? 'lit' : 'dark');
    return fetch(`${API_BASE}/light?role=dm&t=${encodeURIComponent(token)}`, {
      method: 'PATCH',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({lightSource: target}),
    })
    .then(r => r.json())
    .then(data => {
      if (data.state) applyServerState(data.state);
      return data;
    });
  };

  // V6k10.14: DM push de evento dramático
  window.sessionPushEvent = function(opts) {
    if (role !== 'dm') return Promise.reject(new Error('Only DM'));
    return fetch(`${API_BASE}/event?role=dm&t=${encodeURIComponent(token)}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(opts || {}),
    })
    .then(r => r.json())
    .then(data => {
      if (data.state) applyServerState(data.state);
      return data;
    });
  };

  // Presets de eventos comunes (atajos para el DM)
  window.sessionPushSurprise = function(monster) {
    return window.sessionPushEvent({
      type: 'surprise',
      title: '⚔ SORPRESA',
      subtitle: monster ? 'Aparece: ' + monster : 'Algo emerge de las sombras',
      color: '#c44a3a',
      emoji: '💀',
      durationMs: 4000,
    });
  };
  window.sessionPushCombat = function(monster) {
    return window.sessionPushEvent({
      type: 'combat',
      title: 'COMBATE',
      subtitle: monster ? 'Enemigo: ' + monster : '¡Iniciativa!',
      color: '#8b0000',
      emoji: '⚔',
      durationMs: 4000,
    });
  };
  window.sessionPushNarrative = function(text, emoji) {
    return window.sessionPushEvent({
      type: 'narrative',
      title: '',
      subtitle: text || '',
      color: '#2e8b7d',
      emoji: emoji || '📜',
      durationMs: 5000,
    });
  };

  window.sessionResetParty = function(startX, startY, clearMarkers) {
    if (role !== 'dm') return Promise.reject(new Error('Only DM'));
    return fetch(`${API_BASE}/reset?role=dm&t=${encodeURIComponent(token)}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({startX, startY, clearMarkers: !!clearMarkers}),
    })
    .then(r => r.json())
    .then(data => {
      if (data.state) applyServerState(data.state);
      return data;
    });
  };

  // ---- force role-specific flags ----
  function applyRoleFlags() {
    // Players nunca ven markers de rooms (Q1, D1, numbered) ni session markers DM
    if (role === 'players') {
      try { window._markersHidden = true; } catch(e){}
      // Force dmView=false: players can never toggle to DM view
      try {
        const g = window.gridState && window.gridState();
        if (g && g.dmView) g.dmView = false;
      } catch(e){}
    }
  }

  // ---- override gridToggleDM: players cannot toggle to DM view ----
  function patchToggleDM() {
    if (typeof window.gridToggleDM !== 'function') return false;
    const original = window.gridToggleDM;
    window.gridToggleDM = function() {
      if (role === 'players') {
        console.log('[Session] players no puede activar Vista DM');
        if (typeof window.dgToast === 'function') {
          window.dgToast('Vista DM solo disponible para el master', 'info');
        }
        // Force back to player view
        const g = window.gridState && window.gridState();
        if (g) g.dmView = false;
        return;
      }
      return original.apply(this, arguments);
    };
    return true;
  }

  // ---- if server position is not walkable, fallback to sala_74A_cell ----
  function ensureWalkablePosition(state) {
    if (typeof window._realWallmap === 'undefined' || !window._realWallmap) return state;
    const wm = window._realWallmap;
    if (typeof window.gridIsWalkableReal !== 'function') return state;
    if (window.gridIsWalkableReal(state.party.x, state.party.y)) return state;
    // Server position not walkable — log warning. The server is the source of truth,
    // so we don't auto-fix client-side. The DM should reset session with proper coords.
    console.warn(`[Session] Posición server (${state.party.x},${state.party.y}) NO es walkable en wallmap. ` +
                 `Sala 74A canónica está en (${wm.sala_74A_cell ? wm.sala_74A_cell.join(',') : '?'}). ` +
                 'El DM debe resetear la sesión con startX/Y correcto.');
    return state;
  }

  // ---- V6k10.13/14: DM control panel flotante (luz + eventos) ----
  function ensureDmControls() {
    if (role !== 'dm') return;
    if (document.getElementById('session-dm-controls')) return;
    const panel = document.createElement('div');
    panel.id = 'session-dm-controls';
    panel.style.cssText = 'position:fixed;bottom:calc(12px + var(--safe-bottom));right:12px;z-index:9000;display:flex;flex-direction:column;gap:6px;align-items:flex-end;';
    panel.innerHTML =
      '<button id="dm-btn-light" style="background:rgba(0,0,0,0.85);color:#7eef87;border:1px solid #7eef87;padding:8px 12px;border-radius:6px;font-weight:bold;font-size:13px;cursor:pointer;min-height:44px;box-shadow:0 2px 6px rgba(0,0,0,0.4);">🌑 Apagar luz players</button>' +
      '<div style="display:flex;gap:6px;">' +
        '<button id="dm-btn-surprise" style="background:rgba(196,74,58,0.9);color:#fff;border:1px solid #c44a3a;padding:8px 10px;border-radius:6px;font-weight:bold;font-size:12px;cursor:pointer;min-height:44px;">💀 Sorpresa</button>' +
        '<button id="dm-btn-combat" style="background:rgba(139,0,0,0.9);color:#fff;border:1px solid #8b0000;padding:8px 10px;border-radius:6px;font-weight:bold;font-size:12px;cursor:pointer;min-height:44px;">⚔ Combate</button>' +
        '<button id="dm-btn-custom" style="background:rgba(46,139,125,0.9);color:#fff;border:1px solid #2e8b7d;padding:8px 10px;border-radius:6px;font-weight:bold;font-size:12px;cursor:pointer;min-height:44px;">📜 Custom</button>' +
      '</div>';
    document.body.appendChild(panel);

    document.getElementById('dm-btn-light').onclick = () => {
      const isDark = _state && _state.lightSource === 'dark';
      window.sessionToggleLight(isDark ? 'lit' : 'dark').then(() => {
        document.getElementById('dm-btn-light').textContent = isDark ? '🌑 Apagar luz players' : '☀ Encender luz players';
      });
    };
    document.getElementById('dm-btn-surprise').onclick = () => {
      const m = prompt('Monstruo / texto de la sorpresa (opcional):', '') || '';
      window.sessionPushSurprise(m);
    };
    document.getElementById('dm-btn-combat').onclick = () => {
      const m = prompt('Enemigo (opcional):', '') || '';
      window.sessionPushCombat(m);
    };
    document.getElementById('dm-btn-custom').onclick = () => {
      const t = prompt('Texto narrativo:', '') || '';
      if (!t) return;
      const e = prompt('Emoji (opcional):', '📜') || '📜';
      window.sessionPushNarrative(t, e);
    };
  }

  // ---- bootstrap once cockpit is ready ----
  function boot() {
    ensureBadge();
    setStatus('conectando…', '#a8967a');
    applyRoleFlags();
    // Wait for grid functions to be available (cockpit JS is in same page, should be ready)
    let attempts = 0;
    function tryBoot() {
      attempts++;
      if (typeof window.gridState === 'function' && typeof window.gridMoveReal === 'function') {
        diag('boot', 'cockpit funcs ready, autoloading wallmap...');
        patchGridMove();
        patchToggleDM();
        applyRoleFlags();
        ensureDmControls(); // V6k10.13/14: panel DM flotante con botones de luz + eventos
        // V6k10.4: AUTO-LOAD wallmap + map image. Sin esto, el user tiene que ir
        // manualmente a tab Dungeon → Barrowmaze antes de poder mover.
        // Switch to dungeon tab + force grid mode 'real' + load assets.
        try {
          if (typeof window.setMode === 'function') window.setMode('dungeon');
        } catch(e) { diag('boot-warn', 'setMode failed: ' + e); }
        // V6k10.11: forzar loadDungeon('barrowmaze') para inicializar state.dungeon
        // (turns, torchTurnsLeft, wanderingTimer, dayInDungeon, partySize, rationsTotal).
        // Sin esto, dgAdvance() se llama pero el cockpit ignora porque state.dungeon es null.
        try {
          if (typeof window.loadDungeon === 'function') window.loadDungeon('barrowmaze');
        } catch(e) { diag('boot-warn', 'loadDungeon failed: ' + e); }
        try {
          if (typeof window.gridSetMode === 'function') window.gridSetMode('real');
        } catch(e) { diag('boot-warn', 'gridSetMode failed: ' + e); }
        const loadPromise = (typeof window.gridLoadRealMap === 'function')
          ? window.gridLoadRealMap()
          : Promise.resolve(null);

        loadPromise.then((res) => {
          _wallmapReady = true;
          if (res && res.wm) {
            _wallmapInfo = {
              cols: res.wm.cols,
              rows: res.wm.rows,
              sala_74A_cell: res.wm.sala_74A_cell,
            };
          }
          diag('boot', 'wallmap loaded ✓ (local flag set)');
          return fetchState();
        }).then((state) => {
          diag('boot', 'state applied v' + (state ? state.version : '?') + ' role=' + role);
          if (typeof window.renderGridCrawler === 'function') {
            try { window.renderGridCrawler(); } catch(e){}
          } else if (typeof window.redrawGridRealCanvas === 'function') {
            try { window.redrawGridRealCanvas(); } catch(e){}
          }
          setInterval(() => {
            fetchState().catch(()=>{});
            applyRoleFlags();
            // V6k10.7: retry only if our local flag says not ready
            // (NO usar window._realWallmap porque cockpit usa let, no var)
            if (!_wallmapReady && typeof window.gridLoadRealMap === 'function') {
              diag('retry-load', 'wallmap missing, retrying...');
              window.gridLoadRealMap().then((res) => {
                _wallmapReady = true;
                if (res && res.wm) {
                  _wallmapInfo = {
                    cols: res.wm.cols,
                    rows: res.wm.rows,
                    sala_74A_cell: res.wm.sala_74A_cell,
                  };
                }
                diag('retry-load', 'wallmap NOW loaded ✓');
                if (typeof window.renderGridCrawler === 'function') {
                  try { window.renderGridCrawler(); } catch(e){}
                }
              }).catch(e => diag('retry-err', String(e)));
            }
          }, 800);
        }).catch(err => {
          diag('boot-err', String(err));
          setStatus('error inicial', '#c44a3a');
        });
        return;
      }
      if (attempts > 60) {
        setStatus('grid no cargó', '#c44a3a');
        diag('boot-err', 'gridState/gridMoveReal NO disponibles tras 15s');
        return;
      }
      setTimeout(tryBoot, 250);
    }
    tryBoot();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
