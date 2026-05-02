// Session Sync layer para cockpit Valakhan.
// Activa cuando la URL tiene ?sessionId=...&role=...&t=...
// Sincroniza state via Worker en mc-prism-session.marcoscabobianco.workers.dev.

(function(){
  const SYNC_VERSION = 'v6k10p8'; // bump cada deploy de session-sync.js para verificar live
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

  // ---- apply server state to local UI ----
  function applyServerState(state) {
    _state = state;
    _localVersion = state.version || 0;
    const g = (typeof window.gridState === 'function') ? window.gridState() : null;
    if (!g) {
      // gridState may not be ready yet; try again later
      return;
    }
    // V6k10.3: sync realPlayer + reset realTail to same position to avoid ghost markers
    // (3-cuadrados bug: tail vieja persistía de standalone init mientras player estaba en server pos)
    g.realPlayer = { x: state.party.x, y: state.party.y };
    g.realTail = { x: state.party.x, y: state.party.y };
    g.realSeen = state.seen || [];
    g.steps = state.steps || 0;
    g.cellFt = state.cellFt || 10;
    g.partyFtPerTurn = state.partyFtPerTurn || 240;
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

  // ---- override gridMoveReal: only players in session mode can move ----
  function patchGridMove() {
    if (typeof window.gridMoveReal !== 'function') {
      // Not loaded yet — retry
      return false;
    }
    const original = window.gridMoveReal;
    window.gridMoveReal = function(dir) {
      diag('move', 'gridMoveReal(' + dir + ') role=' + role);
      // V6k10.3: ambos roles pueden mover. El primero que apriete tecla manda el delta.
      const g = window.gridState();
      if (!g) { diag('move-fail', 'gridState() null'); return; }
      if (!_wallmapReady) { diag('move-fail', 'wallmap not ready (local flag)'); return; }
      const d = DIRS[dir];
      if (!d) { diag('move-fail', 'unknown dir ' + dir + ' (DIRS keys: ' + Object.keys(DIRS).join(',') + ')'); return; }
      const nx = g.realPlayer.x + d.dx;
      const ny = g.realPlayer.y + d.dy;
      if (typeof window.gridIsWalkableReal === 'function' && !window.gridIsWalkableReal(nx, ny)) {
        diag('move-block', '(' + nx + ',' + ny + ') NOT walkable. From (' + g.realPlayer.x + ',' + g.realPlayer.y + ')');
        if (typeof window.dgToast === 'function') window.dgToast('Celda no transitable', 'info');
        return;
      }

      // Compute LoS at new position client-side (cockpit ya tiene la lógica)
      const visible = [];
      const seenAdds = [];
      for (let dy=-3; dy<=3; dy++) {
        for (let dx=-3; dx<=3; dx++) {
          if (Math.abs(dx)+Math.abs(dy) > 3) continue;
          const cx = nx+dx, cy = ny+dy;
          if (typeof window.gridLineOfSightReal === 'function' &&
              window.gridLineOfSightReal(nx, ny, cx, cy)) {
            const k = window.gridKey(cx, cy);
            visible.push(k);
            seenAdds.push(k);
          }
        }
      }

      // Optimistic local update
      g.realTail = { x: g.realPlayer.x, y: g.realPlayer.y };
      g.realPlayer = { x: nx, y: ny };
      g.steps = (g.steps || 0) + 1;
      const seenSet = new Set(g.realSeen || []);
      for (const k of seenAdds) seenSet.add(k);
      g.realSeen = Array.from(seenSet);
      if (typeof window.redrawGridRealCanvas === 'function') {
        try { window.redrawGridRealCanvas(); } catch(e){}
      }

      // Send to server (V6k10.3: any role can move)
      fetch(`${API_BASE}/move?role=${role}&t=${encodeURIComponent(token)}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({dx: d.dx, dy: d.dy, visible, seen: seenAdds}),
      })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          diag('move-err', data.error);
          if (typeof window.dgToast === 'function') window.dgToast('Move: ' + data.error, 'error');
          return;
        }
        if (data.state) {
          applyServerState(data.state);
          diag('move-ok', 'v' + data.state.version + ' (' + data.state.party.x + ',' + data.state.party.y + ')');
        }
      })
      .catch(err => {
        diag('move-err', String(err));
      });
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
        // V6k10.4: AUTO-LOAD wallmap + map image. Sin esto, el user tiene que ir
        // manualmente a tab Dungeon → Barrowmaze antes de poder mover.
        // Switch to dungeon tab + force grid mode 'real' + load assets.
        try {
          if (typeof window.setMode === 'function') window.setMode('dungeon');
        } catch(e) { diag('boot-warn', 'setMode failed: ' + e); }
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
