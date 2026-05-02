// Session Sync layer para cockpit Valakhan.
// Activa cuando la URL tiene ?sessionId=...&role=...&t=...
// Sincroniza state via Worker en mc-prism-session.marcoscabobianco.workers.dev.
//
// Modos:
//   role=dm:      ve mapa completo + markers DM. NO mueve. Ve party en vivo.
//   role=players: solo ve fog + party. Mueve la party (caller). NO ve markers DM.

(function(){
  const API_BASE_HOST = 'https://mc-prism-session.marcoscabobianco.workers.dev';
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
    body.session-players #_dg-room-modal {
      display: none !important;
    }
    body.session-players .mode-btn[data-mode-key="encounter"],
    body.session-players .mode-btn[data-mode-key="bestiary"] {
      opacity: 0.4; pointer-events: none;
    }
    body.session-players #toggle-markers-btn {
      display: none !important;
    }
    /* Players: discreet hint */
    body.session-players::after {
      content: '';
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
    b.innerHTML = `${roleLabel} · <span id="session-status">conectando…</span>`;
    document.body.appendChild(b);
    _badgeEl = b;
    return b;
  }

  function setStatus(s, color) {
    const el = document.getElementById('session-status');
    if (el) {
      el.textContent = s;
      if (color) el.style.color = color;
    }
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
    g.realPlayer = { x: state.party.x, y: state.party.y };
    g.realTail = g.realTail || { x: state.party.x, y: state.party.y };
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
      if (role !== 'players') {
        console.warn('[Session] DM no puede mover. El caller (players) controla movimiento.');
        if (typeof window.dgToast === 'function') window.dgToast('DM no mueve. El caller mueve.', 'info');
        return;
      }
      const g = window.gridState();
      if (!g || !window._realWallmap) return;
      const d = window.GRID_DIRECTIONS && window.GRID_DIRECTIONS[dir];
      if (!d) return;
      const nx = g.realPlayer.x + d.dx;
      const ny = g.realPlayer.y + d.dy;
      if (typeof window.gridIsWalkableReal === 'function' && !window.gridIsWalkableReal(nx, ny)) return;

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

      // Send to server
      fetch(`${API_BASE}/move?role=players&t=${encodeURIComponent(token)}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({dx: d.dx, dy: d.dy, visible, seen: seenAdds}),
      })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          console.error('[Session] move error:', data.error);
          if (typeof window.dgToast === 'function') window.dgToast('Move: ' + data.error, 'error');
          return;
        }
        if (data.state) applyServerState(data.state);
      })
      .catch(err => {
        console.error('[Session] move failed', err);
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

  // ---- bootstrap once cockpit is ready ----
  function boot() {
    ensureBadge();
    setStatus('conectando…', '#a8967a');
    // Wait for grid functions to be available (cockpit JS is in same page, should be ready)
    let attempts = 0;
    function tryBoot() {
      attempts++;
      if (typeof window.gridState === 'function' && typeof window.gridMoveReal === 'function') {
        patchGridMove();
        fetchState().then(() => {
          setInterval(() => {
            fetchState().catch(()=>{});
          }, 800);
        }).catch(err => {
          console.error('[Session] Initial fetch failed', err);
          setStatus('error inicial', '#c44a3a');
        });
        return;
      }
      if (attempts > 60) {
        setStatus('grid no cargó', '#c44a3a');
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
