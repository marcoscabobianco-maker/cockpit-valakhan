"""
Apply v5x patches to prototipo_v5x.html (already cp from v5w).

Major change: real Barrowmaze map mode with vectorized walls.
  - Background: maps/barrowmaze_real.webp (combined_v3 stitched, 2628x2444, 557 KB).
  - Wallmap: maps/wallmap_barrowmaze.json (203 rows x 219 cols, cell=24px in 5256x4888 coords).
  - Toggle button: ASCII / Real mode.
  - In Real mode: canvas-based renderer with bg image + fog overlay + party rect.
  - LoS Bresenham reuses logic but consults wallmap.data instead of ASCII map.
  - Auto-center scroll on player on each move.
  - Sala 74A cell (32, 84) saved in wallmap JSON; real player initialized there.
  - All v5w tracker features (turns, torch, wandering, rest, alerts) work identically.

Pipeline:
  cp v5w -> v5x
  this script
  validate JS
  cp to deploy + assets
  wrangler deploy
  git commit + push

Usage: PYTHONIOENCODING=utf-8 python _apply_v5x.py
"""
import io, os

ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v5x.html")

with io.open(TARGET, "r", encoding="utf-8") as f:
    html = f.read()
original_len = len(html)
patches = []


def patch(label, old, new, *, count=1):
    global html
    n = html.count(old)
    if n != count:
        raise SystemExit(f"PATCH FAIL [{label}]: expected {count}, found {n}.\nold[:300]: {old[:300]}\n")
    html = html.replace(old, new)
    patches.append(label)
    print(f"  [OK] {label}: {count}x")


# ── 1) title ──
patch(
    "title",
    "<title>Cockpit V5w — v5w: Tracker dungeon + party rect + alertas</title>",
    "<title>Cockpit V5x — v5x: Barrowmaze real (walls vectorizadas + LoS)</title>",
)

# ── 2) CSS for canvas mode ──
patch(
    "css real mode",
    "  .grid-cell-player-tail { background: #2980b9; box-shadow: inset 0 0 0 2px var(--bg); opacity: 0.75; }",
    "  .grid-cell-player-tail { background: #2980b9; box-shadow: inset 0 0 0 2px var(--bg); opacity: 0.75; }\n"
    "  /* v5x real-map canvas mode */\n"
    "  .grid-real-wrap { position:relative; display:inline-block; max-width:100%; max-height:70vh; overflow:auto; border:1px solid var(--border); border-radius:4px; background:#000; }\n"
    "  .grid-real-canvas { display:block; cursor:crosshair; image-rendering:pixelated; }\n"
    "  .grid-mode-toggle { display:flex; gap:6px; align-items:center; margin-bottom:8px; flex-wrap:wrap; }\n"
    "  .grid-mode-toggle .active { background: var(--accent); color: var(--bg); }",
)

# ── 3) gridState extension with real fields ──
patch(
    "gridState v5x extension",
    "  } else {\n"
    "    var g = state.dungeon.grid;\n"
    "    // v5v migration\n"
    "    if (g.steps == null) g.steps = 0;\n"
    "    if (g.partyFtPerTurn == null) g.partyFtPerTurn = 200;\n"
    "    if (g.cellFt == null) g.cellFt = 10;\n"
    "    if (g.dmView == null) g.dmView = false;\n"
    "    // v5w migration\n"
    "    if (g.tail == null) g.tail = { x: g.player.x, y: g.player.y };\n"
    "    if (g.partyShape == null) g.partyShape = { w: 1, h: 2 };\n"
    "    if (g.torchesInPack == null) g.torchesInPack = 6;\n"
    "    if (g.formation == null) g.formation = [];\n"
    "    if (g.lightBearer == null) g.lightBearer = null;\n"
    "    if (g.traps == null) g.traps = [];\n"
    "  }",
    "  } else {\n"
    "    var g = state.dungeon.grid;\n"
    "    // v5v migration\n"
    "    if (g.steps == null) g.steps = 0;\n"
    "    if (g.partyFtPerTurn == null) g.partyFtPerTurn = 200;\n"
    "    if (g.cellFt == null) g.cellFt = 10;\n"
    "    if (g.dmView == null) g.dmView = false;\n"
    "    // v5w migration\n"
    "    if (g.tail == null) g.tail = { x: g.player.x, y: g.player.y };\n"
    "    if (g.partyShape == null) g.partyShape = { w: 1, h: 2 };\n"
    "    if (g.torchesInPack == null) g.torchesInPack = 6;\n"
    "    if (g.formation == null) g.formation = [];\n"
    "    if (g.lightBearer == null) g.lightBearer = null;\n"
    "    if (g.traps == null) g.traps = [];\n"
    "    // v5x migration: real mode\n"
    "    if (g.mode == null) g.mode = 'ascii';\n"
    "    if (g.realPlayer == null) g.realPlayer = null;\n"
    "    if (g.realTail == null) g.realTail = null;\n"
    "    if (g.realSeen == null) g.realSeen = [];\n"
    "  }",
)

# Also include real fields in initial state
patch(
    "gridState v5x init real fields",
    "      formation: [],\n"
    "      lightBearer: null,\n"
    "      traps: []\n"
    "    };",
    "      formation: [],\n"
    "      lightBearer: null,\n"
    "      traps: [],\n"
    "      // v5x real-map state (lazy init on first switch to 'real')\n"
    "      mode: 'ascii',\n"
    "      realPlayer: null,\n"
    "      realTail: null,\n"
    "      realSeen: []\n"
    "    };",
)

# ── 4) renderGridCrawler dispatch on g.mode ──
patch(
    "renderGridCrawler dispatch real mode",
    "function renderGridCrawler() {\n"
    "  const wrap = document.getElementById('grid-crawler-container');\n"
    "  if (!wrap) return;\n"
    "  if (!state.dungeon) {\n"
    "    wrap.innerHTML = '<div style=\"color:var(--ink-dim);padding:20px;\">Selecciona un dungeon primero.</div>';\n"
    "    return;\n"
    "  }\n"
    "  const g = gridState();",
    "function renderGridCrawler() {\n"
    "  const wrap = document.getElementById('grid-crawler-container');\n"
    "  if (!wrap) return;\n"
    "  if (!state.dungeon) {\n"
    "    wrap.innerHTML = '<div style=\"color:var(--ink-dim);padding:20px;\">Selecciona un dungeon primero.</div>';\n"
    "    return;\n"
    "  }\n"
    "  // v5x: dispatch to real renderer if mode='real'\n"
    "  const _g0 = gridState();\n"
    "  if (_g0 && _g0.mode === 'real') return renderGridReal();\n"
    "  const g = gridState();",
)

# ── 5) Add ASCII <-> Real toggle button at the top of ASCII renderer's right column ──
# Insert before the existing Vista DM card
patch(
    "ascii toggle real mode button",
    "  // RIGHT: Editor + legend (v5v: + tiempo + DM toggle)\n"
    "  html += '<div style=\"flex:1;min-width:280px;\">';\n"
    "\n"
    "  // v5v: Vista DM toggle\n",
    "  // RIGHT: Editor + legend (v5v: + tiempo + DM toggle, v5x: + mode toggle)\n"
    "  html += '<div style=\"flex:1;min-width:280px;\">';\n"
    "\n"
    "  // v5x: ASCII / Real mode toggle\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>Mapa</h3>';\n"
    "  html += '<div class=\"grid-mode-toggle\">';\n"
    "  html += '<button class=\"btn active\" onclick=\"gridSetMode(\\'ascii\\')\">⊞ ASCII (default)</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridSetMode(\\'real\\')\">🗺 Barrowmaze real</button>';\n"
    "  html += '</div>';\n"
    "  html += '<div style=\"font-size:11px;color:var(--ink-dim);margin-top:6px;\">Real: walls vectorizadas del PDF, LoS Bresenham real, party rect sobre mapa stitched.</div>';\n"
    "  html += '</div>';\n"
    "\n"
    "  // v5v: Vista DM toggle\n",
)

# ── 6) Helpers nuevos v5x: load/io/walkable/lineOfSight/move/render/reset ──
patch(
    "v5x helpers block",
    "function gridSetTorches(n) {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  var v = parseInt(n, 10);\n"
    "  if (isNaN(v) || v < 0) v = 0;\n"
    "  g.torchesInPack = v;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}",
    "function gridSetTorches(n) {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  var v = parseInt(n, 10);\n"
    "  if (isNaN(v) || v < 0) v = 0;\n"
    "  g.torchesInPack = v;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "\n"
    "// === v5x: Real-map mode (Barrowmaze stitched + vectorized walls) ===\n"
    "const REAL_MAP_BG_SRC = 'maps/barrowmaze_real.webp';\n"
    "const REAL_MAP_WALLMAP_SRC = 'maps/wallmap_barrowmaze.json';\n"
    "let _realWallmap = null;\n"
    "let _realImg = null;\n"
    "let _realLoading = false;\n"
    "\n"
    "function gridLoadRealMap() {\n"
    "  if (_realWallmap && _realImg) return Promise.resolve({wm:_realWallmap, img:_realImg});\n"
    "  if (_realLoading) return new Promise((res) => {\n"
    "    var iv = setInterval(() => {\n"
    "      if (_realWallmap && _realImg) { clearInterval(iv); res({wm:_realWallmap, img:_realImg}); }\n"
    "    }, 100);\n"
    "  });\n"
    "  _realLoading = true;\n"
    "  return Promise.all([\n"
    "    fetch(REAL_MAP_WALLMAP_SRC).then(r => r.json()),\n"
    "    new Promise((res, rej) => { var im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = REAL_MAP_BG_SRC; })\n"
    "  ]).then(([wm, img]) => {\n"
    "    _realWallmap = wm; _realImg = img; _realLoading = false;\n"
    "    return { wm, img };\n"
    "  });\n"
    "}\n"
    "\n"
    "function gridIsWalkableReal(x, y) {\n"
    "  if (!_realWallmap) return false;\n"
    "  if (y < 0 || y >= _realWallmap.rows || x < 0 || x >= _realWallmap.cols) return false;\n"
    "  return _realWallmap.data[y][x] === 0;\n"
    "}\n"
    "\n"
    "function gridLineOfSightReal(x0, y0, x1, y1) {\n"
    "  let cx = x0, cy = y0;\n"
    "  const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);\n"
    "  const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;\n"
    "  let err = dx - dy;\n"
    "  while (true) {\n"
    "    if (cx === x1 && cy === y1) return true;\n"
    "    if (!(cx === x0 && cy === y0) && !gridIsWalkableReal(cx, cy)) return false;\n"
    "    const e2 = 2 * err;\n"
    "    if (e2 > -dy) { err -= dy; cx += sx; }\n"
    "    if (e2 <  dx) { err += dx; cy += sy; }\n"
    "  }\n"
    "}\n"
    "\n"
    "function gridRevealFromReal(x, y, radius) {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  const next = new Set(g.realSeen || []);\n"
    "  for (let dy = -radius; dy <= radius; dy++) {\n"
    "    for (let dx = -radius; dx <= radius; dx++) {\n"
    "      const nx = x + dx, ny = y + dy;\n"
    "      if (Math.abs(dx) + Math.abs(dy) > radius) continue;\n"
    "      if (gridLineOfSightReal(x, y, nx, ny)) next.add(gridKey(nx, ny));\n"
    "    }\n"
    "  }\n"
    "  g.realSeen = Array.from(next);\n"
    "}\n"
    "\n"
    "function gridSetMode(mode) {\n"
    "  if (!state.dungeon) { alert('Cargá un dungeon primero'); return; }\n"
    "  const g = gridState();\n"
    "  if (mode === g.mode) return;\n"
    "  if (mode === 'real') {\n"
    "    const wrap = document.getElementById('grid-crawler-container');\n"
    "    if (wrap) wrap.innerHTML = '<div style=\"color:var(--ink-dim);padding:20px;\">Cargando mapa real (Barrowmaze stitched + walls)…</div>';\n"
    "    gridLoadRealMap().then(({wm}) => {\n"
    "      g.mode = 'real';\n"
    "      if (!g.realPlayer) {\n"
    "        const start = (wm.sala_74A_cell && wm.sala_74A_cell.length === 2) ? wm.sala_74A_cell : [1, 1];\n"
    "        g.realPlayer = { x: start[0], y: start[1] };\n"
    "        g.realTail   = { x: start[0], y: start[1] };\n"
    "        g.realSeen   = [gridKey(start[0], start[1])];\n"
    "      }\n"
    "      gridRevealFromReal(g.realPlayer.x, g.realPlayer.y, 3);\n"
    "      saveState();\n"
    "      renderGridCrawler();\n"
    "      logEvent('🗺 Modo Barrowmaze real activado · Sala 74A · LoS con walls vectorizadas');\n"
    "      renderEventLog();\n"
    "    }).catch(err => {\n"
    "      console.error(err);\n"
    "      alert('Error cargando mapa real: ' + (err.message || err));\n"
    "      g.mode = 'ascii';\n"
    "      renderGridCrawler();\n"
    "    });\n"
    "  } else {\n"
    "    g.mode = 'ascii';\n"
    "    saveState();\n"
    "    renderGridCrawler();\n"
    "    logEvent('⊞ Modo ASCII activado');\n"
    "    renderEventLog();\n"
    "  }\n"
    "}\n"
    "\n"
    "function gridMoveReal(dir) {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  if (!_realWallmap) return;\n"
    "  const d = GRID_DIRECTIONS[dir]; if (!d) return;\n"
    "  const nx = g.realPlayer.x + d.dx;\n"
    "  const ny = g.realPlayer.y + d.dy;\n"
    "  if (!gridIsWalkableReal(nx, ny)) return;\n"
    "  g.realTail = { x: g.realPlayer.x, y: g.realPlayer.y };\n"
    "  g.realPlayer = { x: nx, y: ny };\n"
    "  g.steps = (g.steps || 0) + 1;\n"
    "  if (state.dungeon && typeof dgAdvance === 'function') {\n"
    "    var _tps = (g.cellFt || 10) / Math.max(1, (g.partyFtPerTurn || 200));\n"
    "    var _crossed = Math.floor(g.steps * _tps) - Math.floor((g.steps - 1) * _tps);\n"
    "    for (var _i = 0; _i < _crossed; _i++) dgAdvance();\n"
    "  }\n"
    "  gridRevealFromReal(nx, ny, 3);\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "\n"
    "function gridResetReal74A() {\n"
    "  if (!_realWallmap) return;\n"
    "  if (!confirm('Volver a Sala 74A (perdés posición actual)?')) return;\n"
    "  const g = gridState(); if (!g) return;\n"
    "  const start = _realWallmap.sala_74A_cell || [1,1];\n"
    "  g.realPlayer = { x: start[0], y: start[1] };\n"
    "  g.realTail   = { x: start[0], y: start[1] };\n"
    "  g.realSeen   = [gridKey(start[0], start[1])];\n"
    "  gridRevealFromReal(start[0], start[1], 3);\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "function gridResetSeenReal() {\n"
    "  if (!confirm('Resetear niebla en mapa real (party vuelve a ver solo su LoS actual)?')) return;\n"
    "  const g = gridState(); if (!g) return;\n"
    "  g.realSeen = [gridKey(g.realPlayer.x, g.realPlayer.y)];\n"
    "  gridRevealFromReal(g.realPlayer.x, g.realPlayer.y, 3);\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "\n"
    "function renderGridReal() {\n"
    "  const wrap = document.getElementById('grid-crawler-container');\n"
    "  if (!wrap) return;\n"
    "  if (!_realWallmap || !_realImg) {\n"
    "    wrap.innerHTML = '<div style=\"color:var(--ink-dim);padding:20px;\">Cargando mapa real…</div>';\n"
    "    gridLoadRealMap().then(() => renderGridCrawler());\n"
    "    return;\n"
    "  }\n"
    "  const g = gridState();\n"
    "  const wm = _realWallmap;\n"
    "  const img = _realImg;\n"
    "  const seenSet = new Set(g.realSeen || []);\n"
    "  const visibleNow = new Set();\n"
    "  for (let dy=-3; dy<=3; dy++) {\n"
    "    for (let dx=-3; dx<=3; dx++) {\n"
    "      const nx = g.realPlayer.x+dx, ny = g.realPlayer.y+dy;\n"
    "      if (Math.abs(dx)+Math.abs(dy) > 3) continue;\n"
    "      if (gridLineOfSightReal(g.realPlayer.x, g.realPlayer.y, nx, ny)) visibleNow.add(gridKey(nx, ny));\n"
    "    }\n"
    "  }\n"
    "  const SCALE = img.width / wm.stitched_image_dims[0];\n"
    "  const cellSize = wm.cell_size_px * SCALE;\n"
    "  // ----- Build HTML -----\n"
    "  let html = '';\n"
    "  // Alerts banner (same as v5w)\n"
    "  if (state.dungeon) {\n"
    "    var dgB = state.dungeon;\n"
    "    var alerts = [];\n"
    "    if (dgB.restTimer === 0) alerts.push({color:'#e67e22', emoji:'😴', msg:'Rest DUE — 5 turnos sin descanso. Penalty -1/-1 hasta descansar.', action:'dgRest()', actionLabel:'Descansar'});\n"
    "    if (dgB.wanderingTimer === 0) alerts.push({color:'#c0392b', emoji:'👹', msg:'Wandering check DUE — tirar 1d6' + (dgB.wanderingNoise>0 ? ' (ruido +'+dgB.wanderingNoise+', umbral ≤'+(1+dgB.wanderingNoise)+')' : ''), action:'dgWanderingCheck()', actionLabel:'Tirar 1d6'});\n"
    "    if (dgB.torchTurnsLeft === 0) alerts.push({color:'#1a1410', emoji:'🌑', msg:'Antorcha AGOTADA. Combate -4 to-hit. Encender otra de mochila.', action:'gridLightTorch()', actionLabel:'Encender'});\n"
    "    else if (dgB.torchTurnsLeft <= 2) alerts.push({color:'#d4a04a', emoji:'🔥', msg:'Antorcha en últimos '+dgB.torchTurnsLeft+' turnos — preparar otra.', action:null});\n"
    "    if (alerts.length) {\n"
    "      html += '<div style=\"display:flex;flex-direction:column;gap:6px;margin-bottom:10px;\">';\n"
    "      alerts.forEach(function(a){\n"
    "        html += '<div style=\"background:'+a.color+';color:#fff;padding:8px 12px;border-radius:4px;font-weight:600;display:flex;align-items:center;gap:8px;border:1px solid rgba(255,255,255,0.15);\">';\n"
    "        html += '<span style=\"font-size:18px;\">'+a.emoji+'</span><span style=\"flex:1;\">'+a.msg+'</span>';\n"
    "        if (a.action) html += '<button class=\"btn\" onclick=\"'+a.action+'\" style=\"min-width:auto;\">'+a.actionLabel+'</button>';\n"
    "        html += '</div>';\n"
    "      });\n"
    "      html += '</div>';\n"
    "    }\n"
    "  }\n"
    "  // Mode toggle\n"
    "  html += '<div class=\"grid-mode-toggle\">';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridSetMode(\\'ascii\\')\">⊞ ASCII</button>';\n"
    "  html += '<button class=\"btn active\" onclick=\"gridSetMode(\\'real\\')\">🗺 Barrowmaze real</button>';\n"
    "  html += '<span style=\"font-size:12px;color:var(--ink-dim);margin-left:auto;\">Cell '+wm.cell_size_px+'px (orig) · Display '+cellSize.toFixed(1)+'px · Grid '+wm.cols+'×'+wm.rows+' · Walkable '+wm.walkable_pct.toFixed(1)+'%</span>';\n"
    "  html += '</div>';\n"
    "  // Layout: canvas + cards\n"
    "  html += '<div style=\"display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start;\">';\n"
    "  html += '<div>';\n"
    "  html += '<div class=\"grid-real-wrap\" id=\"grid-real-wrap\">';\n"
    "  html += '<canvas id=\"grid-real-canvas\" class=\"grid-real-canvas\" width=\"'+img.width+'\" height=\"'+img.height+'\"></canvas>';\n"
    "  html += '</div>';\n"
    "  // grid-info + tracker line\n"
    "  var _ftRatio = (g.cellFt || 10) / Math.max(1, (g.partyFtPerTurn || 200));\n"
    "  var _turnsRaw = (g.steps || 0) * _ftRatio;\n"
    "  var _turns = Math.floor(_turnsRaw);\n"
    "  var _minutes = (_turnsRaw * 10).toFixed(1);\n"
    "  html += '<div class=\"grid-info\">Posición: <b>(' + g.realPlayer.x + ',' + g.realPlayer.y + ')</b> · Recorrido: ' + (g.realSeen||[]).length + ' celdas · Radio visión: 3 · ' + (g.dmView ? '<span style=\"color:#5dade2;\">👁 Vista DM</span>' : '<span style=\"color:#aaa;\">👤 Vista jugadores</span>') + '</div>';\n"
    "  html += '<div class=\"grid-info\" style=\"margin-top:2px;\">⏱ Pasos: <b>' + (g.steps||0) + '</b> · Turnos (10min): <b>' + _turns + '</b> · Minutos: <b>' + _minutes + '</b></div>';\n"
    "  // Touch controls\n"
    "  html += '<div class=\"grid-controls\">';\n"
    "  html += '<div></div><button onclick=\"gridMove(\\'up\\')\" title=\"W\">↑</button><div></div>';\n"
    "  html += '<button onclick=\"gridMove(\\'left\\')\" title=\"A\">←</button>';\n"
    "  html += '<button onclick=\"gridMove(\\'down\\')\" title=\"S\">↓</button>';\n"
    "  html += '<button onclick=\"gridMove(\\'right\\')\" title=\"D\">→</button>';\n"
    "  html += '</div>';\n"
    "  html += '</div>';\n"
    "  // Right column: same cards as v5w\n"
    "  html += '<div style=\"flex:1;min-width:280px;\">';\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\"><h3>Vista</h3><button class=\"btn\" onclick=\"gridToggleDM()\" style=\"font-size:14px;width:100%;\">' + (g.dmView ? '👁 DM (ver todo) — click para ocultar' : '👤 Jugadores (con niebla) — click para revelar') + '</button><div style=\"font-size:11px;color:var(--ink-dim);margin-top:6px;\">' + (g.dmView ? 'Modo DM: ves todo el dungeon. Marker celeste sigue visible.' : 'Modo jugadores: solo lo iluminado por LoS o lo ya recorrido.') + '</div></div>';\n"
    "  // Tracker card\n"
    "  var dgT = state.dungeon || {};\n"
    "  var torchMax = dgT.torchTurnsMax || 6;\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>⏱ Tracker de exploración</h3>';\n"
    "  html += '<div style=\"display:grid;grid-template-columns:auto 1fr;gap:4px 12px;font-size:13px;\">';\n"
    "  html += '<span>Pasos:</span><b>' + (g.steps||0) + '</b>';\n"
    "  html += '<span>Turnos (10 min):</span><b>' + _turns + '</b>';\n"
    "  html += '<span>Minutos acumulados:</span><b>' + _minutes + '</b>';\n"
    "  html += '</div>';\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:10px 0;\">';\n"
    "  html += '<div style=\"font-size:13px;line-height:1.8;\">';\n"
    "  html += '<div>🔥 Antorcha: <b>' + (dgT.torchTurnsLeft||0) + ' / ' + torchMax + '</b> turns &nbsp;·&nbsp; Mochila: <b>' + (g.torchesInPack||0) + '</b></div>';\n"
    "  html += '<div>👹 Wandering: <b>' + (dgT.wanderingTimer||0) + ' / 2</b> turns &nbsp;·&nbsp; Ruido: <b>+' + (dgT.wanderingNoise||0) + '</b> (umbral 1d6 ≤ ' + (1 + (dgT.wanderingNoise||0)) + ')</div>';\n"
    "  html += '<div>😴 Descanso: <b>' + (dgT.restTimer != null ? dgT.restTimer : 5) + ' / 5</b> turns hasta rest</div>';\n"
    "  html += '</div>';\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:10px 0;\">';\n"
    "  html += '<div style=\"display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:12px;\">';\n"
    "  html += '<label>Party ft/turn:</label><input type=\"number\" value=\"' + (g.partyFtPerTurn||200) + '\" min=\"30\" max=\"600\" step=\"10\" style=\"width:70px;\" onchange=\"gridSetSpeed(this.value, null)\">';\n"
    "  html += '<label>Cell ft:</label><input type=\"number\" value=\"' + (g.cellFt||10) + '\" min=\"1\" max=\"50\" step=\"1\" style=\"width:55px;\" onchange=\"gridSetSpeed(null, this.value)\">';\n"
    "  html += '<label>Antorchas:</label><input type=\"number\" value=\"' + (g.torchesInPack||0) + '\" min=\"0\" max=\"99\" step=\"1\" style=\"width:55px;\" onchange=\"gridSetTorches(this.value)\">';\n"
    "  html += '</div>';\n"
    "  html += '<div style=\"margin-top:10px;display:grid;grid-template-columns:repeat(2,1fr);gap:6px;\">';\n"
    "  html += '<button class=\"btn\" onclick=\"gridAddTurn()\">+1 Turno (actividad)</button>';\n"
    "  html += '<button class=\"btn\" onclick=\"dgRest()\">😴 Descansar 1 turno</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridLightTorch()\">🔥 Encender antorcha</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgWanderingCheck()\">🎲 Wandering check</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridAddNoise()\">🔊 Ruido +1</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetTime()\">⟲ Reset pasos</button>';\n"
    "  html += '</div>';\n"
    "  html += '</div>';\n"
    "  // Real-mode controls\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\"><h3>Posición real</h3>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetReal74A()\" style=\"width:100%;\">⟲ Reset a Sala 74A</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetSeenReal()\" style=\"width:100%;margin-top:6px;\">⟲ Reset niebla</button>';\n"
    "  html += '</div>';\n"
    "  html += '</div>';\n"
    "  html += '</div>';\n"
    "  wrap.innerHTML = html;\n"
    "  // ----- Canvas drawing -----\n"
    "  const canvas = document.getElementById('grid-real-canvas');\n"
    "  if (!canvas) return;\n"
    "  const ctx = canvas.getContext('2d');\n"
    "  ctx.drawImage(img, 0, 0, img.width, img.height);\n"
    "  // Fog overlay\n"
    "  for (let ry = 0; ry < wm.rows; ry++) {\n"
    "    for (let cx = 0; cx < wm.cols; cx++) {\n"
    "      const k = gridKey(cx, ry);\n"
    "      const x0 = cx * cellSize;\n"
    "      const y0 = ry * cellSize;\n"
    "      if (g.dmView) continue;\n"
    "      const wasSeen = seenSet.has(k);\n"
    "      const isVisible = visibleNow.has(k);\n"
    "      if (!wasSeen) {\n"
    "        ctx.fillStyle = 'rgba(0,0,0,0.97)';\n"
    "        ctx.fillRect(x0, y0, cellSize+1, cellSize+1);\n"
    "      } else if (!isVisible) {\n"
    "        ctx.fillStyle = 'rgba(0,0,0,0.45)';\n"
    "        ctx.fillRect(x0, y0, cellSize+1, cellSize+1);\n"
    "      }\n"
    "    }\n"
    "  }\n"
    "  // Tail\n"
    "  if (g.realTail) {\n"
    "    const tx = g.realTail.x * cellSize;\n"
    "    const ty = g.realTail.y * cellSize;\n"
    "    ctx.fillStyle = 'rgba(41,128,185,0.75)';\n"
    "    ctx.fillRect(tx, ty, cellSize, cellSize);\n"
    "    ctx.strokeStyle = '#0d1117';\n"
    "    ctx.lineWidth = 2;\n"
    "    ctx.strokeRect(tx, ty, cellSize, cellSize);\n"
    "  }\n"
    "  // Head (party leader)\n"
    "  const px = g.realPlayer.x * cellSize;\n"
    "  const py = g.realPlayer.y * cellSize;\n"
    "  ctx.fillStyle = '#5dade2';\n"
    "  ctx.fillRect(px, py, cellSize, cellSize);\n"
    "  ctx.strokeStyle = '#0d1117';\n"
    "  ctx.lineWidth = 2;\n"
    "  ctx.strokeRect(px, py, cellSize, cellSize);\n"
    "  // Auto-center scroll on player\n"
    "  const w = document.getElementById('grid-real-wrap');\n"
    "  if (w) {\n"
    "    const wrapW = w.clientWidth || 800;\n"
    "    const wrapH = w.clientHeight || 600;\n"
    "    w.scrollLeft = Math.max(0, px - wrapW/2 + cellSize/2);\n"
    "    w.scrollTop  = Math.max(0, py - wrapH/2 + cellSize/2);\n"
    "  }\n"
    "}",
)

# ── 7) gridMove dispatch by mode ──
patch(
    "gridMove dispatch real",
    "function gridMove(dir) {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  const d = GRID_DIRECTIONS[dir]; if (!d) return;\n"
    "  const map = gridParseMap(g.raw);\n",
    "function gridMove(dir) {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  // v5x: dispatch to real-mode mover when mode='real'\n"
    "  if (g.mode === 'real') return gridMoveReal(dir);\n"
    "  const d = GRID_DIRECTIONS[dir]; if (!d) return;\n"
    "  const map = gridParseMap(g.raw);\n",
)

# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
