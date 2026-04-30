"""
v5y patches: focus on the real Barrowmaze grid (drop everything else).

Decisions confirmed by Marcos 2026-04-30 after testing v5x:
  - Remove Room Graph view (svg dgmap with rectangles + connections).
  - Remove Cia Zafiro fog/imgmap view.
  - Remove Cia Zafiro background JPEG behind dungeon view.
  - Auto-default dungeonView='grid' (real mode if Barrowmaze).
  - Make DM-view toggle prominent (big button above canvas, not buried in side card).
  - Add keyboard shortcut 'G' to toggle DM-view.
  - Performance: separate canvas redraw from full HTML rebuild so movement is snappy.
    On gridMoveReal: only redrawCanvas + updateQuickStats, full renderGridCrawler() ONLY when
    a turn boundary triggers a new alert.

Pipeline: cp v5x -> v5y, this script, validate, deploy.
Usage: PYTHONIOENCODING=utf-8 python _apply_v5y.py
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v5y.html")
with io.open(TARGET, "r", encoding="utf-8") as f:
    html = f.read()
original_len = len(html)
patches = []
def patch(label, old, new, *, count=1):
    global html
    n = html.count(old)
    if n != count:
        raise SystemExit(f"PATCH FAIL [{label}]: expected {count}, found {n}.\nold[:240]: {old[:240]}\n")
    html = html.replace(old, new)
    patches.append(label)
    print(f"  [OK] {label}: {count}x")


# ── 1) title ──
patch(
    "title",
    "<title>Cockpit V5x — v5x: Barrowmaze real (walls vectorizadas + LoS)</title>",
    "<title>Cockpit V5y — v5y: Grid Barrowmaze focus (DM prominent + perf)</title>",
)

# ── 2) Quitar la barra de 3 botones (graph/image/grid) y los divs dg-graph-view + dg-image-view.
#    Dejar solo el dg-grid-view.
patch(
    "remove dungeon view buttons + extra views",
    "    <div>\n"
    "      <div class=\"row\" style=\"margin-bottom:6px;\">\n"
    "        <button class=\"btn\" onclick=\"setDungeonView('graph')\" id=\"btn-dg-graph\">Room graph</button>\n"
    "        <button class=\"btn secondary\" onclick=\"setDungeonView('image')\" id=\"btn-dg-image\">📍 Mapa real (Cía Zafiro)</button>\n"
    "        <button class=\"btn secondary\" onclick=\"setDungeonView('grid')\" id=\"btn-dg-grid\">⊞ Grid táctico</button>\n"
    "      </div>\n"
    "      <div id=\"dg-graph-view\" class=\"dungeon-map\">\n"
    "        <svg id=\"dgmap\" width=\"900\" height=\"500\" viewBox=\"0 0 900 500\"></svg>\n"
    "      </div>\n"
    "      <div id=\"dg-image-view\" style=\"display:none;\">\n"
    "        <div id=\"fog-toolbar\"></div>\n"
    "        <div id=\"fog-container\"></div>\n"
    "        <div id=\"imgmap-container\" style=\"margin-top:8px;\"></div>\n"
    "      </div>\n"
    "      <div id=\"dg-grid-view\" style=\"display:none;\">\n"
    "        <div id=\"grid-crawler-container\"></div>\n"
    "      </div>\n"
    "    </div>",
    "    <div>\n"
    "      <!-- v5y: only grid táctico view; Room Graph + Cía Zafiro fog/img views removed -->\n"
    "      <div id=\"dg-grid-view\">\n"
    "        <div id=\"grid-crawler-container\"></div>\n"
    "      </div>\n"
    "    </div>",
)

# ── 3) renderDungeon: quitar el bloque que setea backgroundImage (Cía Zafiro JPEG) ──
patch(
    "remove dungeon background image",
    "  // Set background image based on dungeon\n"
    "  const dgmapEl = document.getElementById('dgmap');\n"
    "  if (state.dungeon && dgmapEl) {\n"
    "    const dgWrap = dgmapEl.parentElement;\n"
    "    const id = state.dungeon.id;\n"
    "    let bgImg = null;\n"
    "    if (id === 'barrowmaze') bgImg = 'cockpit-imgs/barrowmaze-cia-zafiro-2026-04-06.jpeg';\n"
    "    else if (id === 'sunless_citadel') bgImg = null;\n"
    "    else if (id === 'ardis_vala') bgImg = null;\n"
    "    if (bgImg) {\n"
    "      dgWrap.style.backgroundImage = 'url('+bgImg+')';\n"
    "      dgWrap.style.backgroundSize = 'contain';\n"
    "      dgWrap.style.backgroundRepeat = 'no-repeat';\n"
    "      dgWrap.style.backgroundPosition = 'center';\n"
    "      dgWrap.style.backgroundColor = 'rgba(0,0,0,0.5)';\n"
    "    } else {\n"
    "      dgWrap.style.backgroundImage = '';\n"
    "    }\n"
    "  }",
    "  // v5y: Cía Zafiro background image removed (was on Room Graph svg parent).",
)

# ── 4) renderDungeon: quitar el bloque del SVG dgmap rooms+connections (already orphaned but cleanup)
#    Keep the rest of renderDungeon (header stats setting). Just no svg work.
patch(
    "remove room graph svg drawing",
    "  const svg = document.getElementById('dgmap');\n"
    "  svg.innerHTML = '';\n"
    "  const rooms = data.rooms || {};\n"
    "  // Compute bounding\n"
    "  const rs = Object.values(rooms);\n"
    "  const maxX = Math.max(...rs.map(r => r.x + r.w)) + 30;\n"
    "  const maxY = Math.max(...rs.map(r => r.y + r.h)) + 30;\n"
    "  svg.setAttribute('viewBox', '0 0 ' + maxX + ' ' + maxY);\n"
    "  // Connections\n"
    "  (data.connections || []).forEach(([a,b]) => {\n"
    "    const ra = rooms[a], rb = rooms[b];\n"
    "    if (!ra || !rb) return;\n"
    "    const visA = dg.fogOfWar[a], visB = dg.fogOfWar[b];\n"
    "    if (!visA && !visB) return;\n"
    "    const ax = ra.x + ra.w/2, ay = ra.y + ra.h/2, bx = rb.x + rb.w/2, by = rb.y + rb.h/2;\n"
    "    const ln = document.createElementNS('http://www.w3.org/2000/svg','line');\n"
    "    ln.setAttribute('x1',ax); ln.setAttribute('y1',ay); ln.setAttribute('x2',bx); ln.setAttribute('y2',by);\n"
    "    ln.setAttribute('class','dungeon-room-conn'); svg.appendChild(ln);\n"
    "  });\n"
    "  Object.entries(rooms).forEach(([rid, r]) => {\n"
    "    const visited = dg.fogOfWar[rid];\n"
    "    const isCurrent = String(dg.currentRoom) === String(rid);\n"
    "    const rect = document.createElementNS('http://www.w3.org/2000/svg','rect');\n"
    "    rect.setAttribute('x', r.x); rect.setAttribute('y', r.y);\n"
    "    rect.setAttribute('width', r.w); rect.setAttribute('height', r.h);\n"
    "    rect.setAttribute('class', 'dungeon-room' + (visited?'':' fog') + (isCurrent?' current':''));\n"
    "    rect.setAttribute('fill', visited ? 'rgba(58,45,35,0.85)' : 'rgba(14,10,8,0.85)');\n"
    "    rect.setAttribute('rx', 4);\n"
    "    rect.addEventListener('click', () => moveToRoom(rid));\n"
    "    svg.appendChild(rect);\n"
    "    if (visited) {\n"
    "      const lbl = document.createElementNS('http://www.w3.org/2000/svg','text');\n"
    "      lbl.setAttribute('class','dungeon-room-label'); lbl.setAttribute('x', r.x + r.w/2); lbl.setAttribute('y', r.y + r.h/2 + 3);\n"
    "      lbl.textContent = r.name; svg.appendChild(lbl);\n"
    "    }\n"
    "  });\n"
    "}",
    "  // v5y: room graph svg removed; grid crawler (real or ASCII) is the only dungeon view.\n"
    "}",
)

# ── 5) setDungeonView: simplificar (solo grid mode existe ahora) ──
patch(
    "simplify setDungeonView",
    "function setDungeonView(v) {\n"
    "  state.dungeonView = v;\n"
    "  const gview = document.getElementById('dg-graph-view');\n"
    "  const iview = document.getElementById('dg-image-view');\n"
    "  const grview = document.getElementById('dg-grid-view');\n"
    "  if (gview) gview.style.display = v === 'graph' ? '' : 'none';\n"
    "  if (iview) iview.style.display = v === 'image' ? '' : 'none';\n"
    "  if (grview) grview.style.display = v === 'grid' ? '' : 'none';\n"
    "  const bg = document.getElementById('btn-dg-graph');\n"
    "  const bi = document.getElementById('btn-dg-image');\n"
    "  const br = document.getElementById('btn-dg-grid');\n"
    "  if (bg) bg.className = v === 'graph' ? 'btn' : 'btn secondary';\n"
    "  if (bi) bi.className = v === 'image' ? 'btn' : 'btn secondary';\n"
    "  if (br) br.className = v === 'grid' ? 'btn' : 'btn secondary';\n"
    "  saveState();\n"
    "  if (v === 'image') { renderFogOfWar(); renderImgMap(); }\n"
    "  if (v === 'grid') { renderGridCrawler(); }\n"
    "}",
    "function setDungeonView(v) {\n"
    "  // v5y: only 'grid' view exists. Coerce any legacy value to 'grid'.\n"
    "  state.dungeonView = 'grid';\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}",
)

# ── 6) Default dungeonView = 'grid' siempre, y si es Barrowmaze auto-modo 'real' ──
patch(
    "default to grid + auto real for barrowmaze",
    "  if (!state.dungeonView) state.dungeonView = (state.dungeon?.id === 'barrowmaze') ? 'grid' : 'graph';\n"
    "  setDungeonView(state.dungeonView);",
    "  // v5y: only grid view exists; if Barrowmaze and grid hasn't switched to real yet, do it.\n"
    "  state.dungeonView = 'grid';\n"
    "  setDungeonView('grid');\n"
    "  if (state.dungeon && state.dungeon.id === 'barrowmaze' && state.dungeon.grid && state.dungeon.grid.mode !== 'real') {\n"
    "    setTimeout(() => { try { gridSetMode('real'); } catch(e){} }, 50);\n"
    "  }",
)

# ── 7) Performance: split renderGridReal in two ──
# 7a) Make renderGridReal call redrawGridRealCanvas at the end (instead of inline drawing).
patch(
    "split renderGridReal canvas drawing into helper",
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
    "  wrap.innerHTML = html;\n"
    "  // v5y: delegate canvas drawing to redrawGridRealCanvas() so movement can call it directly\n"
    "  redrawGridRealCanvas();\n"
    "}\n"
    "\n"
    "// v5y: pure canvas+scroll redraw, no HTML rebuild. Called per movement.\n"
    "function redrawGridRealCanvas() {\n"
    "  if (!_realWallmap || !_realImg) return;\n"
    "  const g = gridState(); if (!g) return;\n"
    "  const canvas = document.getElementById('grid-real-canvas');\n"
    "  if (!canvas) return;\n"
    "  const ctx = canvas.getContext('2d');\n"
    "  const wm = _realWallmap;\n"
    "  const img = _realImg;\n"
    "  const SCALE = img.width / wm.stitched_image_dims[0];\n"
    "  const cellSize = wm.cell_size_px * SCALE;\n"
    "  const seenSet = new Set(g.realSeen || []);\n"
    "  const visibleNow = new Set();\n"
    "  for (let dy=-3; dy<=3; dy++) {\n"
    "    for (let dx=-3; dx<=3; dx++) {\n"
    "      const nx = g.realPlayer.x+dx, ny = g.realPlayer.y+dy;\n"
    "      if (Math.abs(dx)+Math.abs(dy) > 3) continue;\n"
    "      if (gridLineOfSightReal(g.realPlayer.x, g.realPlayer.y, nx, ny)) visibleNow.add(gridKey(nx, ny));\n"
    "    }\n"
    "  }\n"
    "  ctx.drawImage(img, 0, 0, img.width, img.height);\n"
    "  if (!g.dmView) {\n"
    "    for (let ry = 0; ry < wm.rows; ry++) {\n"
    "      for (let cx = 0; cx < wm.cols; cx++) {\n"
    "        const k = gridKey(cx, ry);\n"
    "        const x0 = cx * cellSize, y0 = ry * cellSize;\n"
    "        const wasSeen = seenSet.has(k);\n"
    "        const isVisible = visibleNow.has(k);\n"
    "        if (!wasSeen) { ctx.fillStyle = 'rgba(0,0,0,0.97)'; ctx.fillRect(x0, y0, cellSize+1, cellSize+1); }\n"
    "        else if (!isVisible) { ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.fillRect(x0, y0, cellSize+1, cellSize+1); }\n"
    "      }\n"
    "    }\n"
    "  }\n"
    "  if (g.realTail) {\n"
    "    const tx = g.realTail.x * cellSize, ty = g.realTail.y * cellSize;\n"
    "    ctx.fillStyle = 'rgba(41,128,185,0.75)'; ctx.fillRect(tx, ty, cellSize, cellSize);\n"
    "    ctx.strokeStyle = '#0d1117'; ctx.lineWidth = 2; ctx.strokeRect(tx, ty, cellSize, cellSize);\n"
    "  }\n"
    "  const px = g.realPlayer.x * cellSize, py = g.realPlayer.y * cellSize;\n"
    "  ctx.fillStyle = '#5dade2'; ctx.fillRect(px, py, cellSize, cellSize);\n"
    "  ctx.strokeStyle = '#0d1117'; ctx.lineWidth = 2; ctx.strokeRect(px, py, cellSize, cellSize);\n"
    "  const w = document.getElementById('grid-real-wrap');\n"
    "  if (w) {\n"
    "    const wrapW = w.clientWidth || 800, wrapH = w.clientHeight || 600;\n"
    "    w.scrollLeft = Math.max(0, px - wrapW/2 + cellSize/2);\n"
    "    w.scrollTop  = Math.max(0, py - wrapH/2 + cellSize/2);\n"
    "  }\n"
    "  // Update inline stat numbers if present\n"
    "  updateRealQuickStats();\n"
    "}\n"
    "\n"
    "function updateRealQuickStats() {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  var elPos = document.getElementById('grid-real-pos'); if (elPos) elPos.textContent = '(' + g.realPlayer.x + ',' + g.realPlayer.y + ')';\n"
    "  var elSeen = document.getElementById('grid-real-seen'); if (elSeen) elSeen.textContent = (g.realSeen||[]).length;\n"
    "  var elSteps = document.getElementById('grid-real-steps'); if (elSteps) elSteps.textContent = (g.steps||0);\n"
    "  var ftRatio = (g.cellFt || 10) / Math.max(1, (g.partyFtPerTurn || 200));\n"
    "  var turnsRaw = (g.steps || 0) * ftRatio;\n"
    "  var elTurns = document.getElementById('grid-real-turns'); if (elTurns) elTurns.textContent = Math.floor(turnsRaw);\n"
    "  var elMins = document.getElementById('grid-real-mins'); if (elMins) elMins.textContent = (turnsRaw * 10).toFixed(1);\n"
    "  var elDmLabel = document.getElementById('grid-real-dm-label');\n"
    "  if (elDmLabel) elDmLabel.innerHTML = g.dmView ? '<span style=\"color:#5dade2;\">👁 Vista DM</span>' : '<span style=\"color:#aaa;\">👤 Vista jugadores</span>';\n"
    "}",
)

# ── 7b) gridMoveReal: solo redraw + quickStats si no hubo cambio de turn ──
patch(
    "gridMoveReal perf-friendly",
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
    "}",
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
    "  // v5y: turn-boundary advance. If a turn happened, alerts may change -> full rerender.\n"
    "  // Otherwise, just redraw canvas + stats (much faster).\n"
    "  let _turnHappened = false;\n"
    "  if (state.dungeon && typeof dgAdvance === 'function') {\n"
    "    var _tps = (g.cellFt || 10) / Math.max(1, (g.partyFtPerTurn || 200));\n"
    "    var _crossed = Math.floor(g.steps * _tps) - Math.floor((g.steps - 1) * _tps);\n"
    "    if (_crossed > 0) _turnHappened = true;\n"
    "    for (var _i = 0; _i < _crossed; _i++) dgAdvance();\n"
    "  }\n"
    "  gridRevealFromReal(nx, ny, 3);\n"
    "  saveState();\n"
    "  if (_turnHappened) {\n"
    "    renderGridCrawler();\n"
    "  } else {\n"
    "    redrawGridRealCanvas();\n"
    "  }\n"
    "}",
)

# ── 7c) IDs en los stats inline para que updateRealQuickStats los actualice ──
patch(
    "stat ids inline",
    "  html += '<div class=\"grid-info\">Posición: <b>(' + g.realPlayer.x + ',' + g.realPlayer.y + ')</b> · Recorrido: ' + (g.realSeen||[]).length + ' celdas · Radio visión: 3 · ' + (g.dmView ? '<span style=\"color:#5dade2;\">👁 Vista DM</span>' : '<span style=\"color:#aaa;\">👤 Vista jugadores</span>') + '</div>';\n"
    "  html += '<div class=\"grid-info\" style=\"margin-top:2px;\">⏱ Pasos: <b>' + (g.steps||0) + '</b> · Turnos (10min): <b>' + _turns + '</b> · Minutos: <b>' + _minutes + '</b></div>';",
    "  html += '<div class=\"grid-info\">Posición: <b id=\"grid-real-pos\">(' + g.realPlayer.x + ',' + g.realPlayer.y + ')</b> · Recorrido: <b id=\"grid-real-seen\">' + (g.realSeen||[]).length + '</b> celdas · Radio visión: 3 · <span id=\"grid-real-dm-label\">' + (g.dmView ? '<span style=\"color:#5dade2;\">👁 Vista DM</span>' : '<span style=\"color:#aaa;\">👤 Vista jugadores</span>') + '</span></div>';\n"
    "  html += '<div class=\"grid-info\" style=\"margin-top:2px;\">⏱ Pasos: <b id=\"grid-real-steps\">' + (g.steps||0) + '</b> · Turnos (10min): <b id=\"grid-real-turns\">' + _turns + '</b> · Minutos: <b id=\"grid-real-mins\">' + _minutes + '</b></div>';",
)

# ── 8) DM toggle prominente arriba del mapa (en lugar de oculto en panel derecho) ──
patch(
    "DM toggle prominent above canvas",
    "  // Mode toggle\n"
    "  html += '<div class=\"grid-mode-toggle\">';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridSetMode(\\'ascii\\')\">⊞ ASCII</button>';\n"
    "  html += '<button class=\"btn active\" onclick=\"gridSetMode(\\'real\\')\">🗺 Barrowmaze real</button>';\n"
    "  html += '<span style=\"font-size:12px;color:var(--ink-dim);margin-left:auto;\">Cell '+wm.cell_size_px+'px (orig) · Display '+cellSize.toFixed(1)+'px · Grid '+wm.cols+'×'+wm.rows+' · Walkable '+wm.walkable_pct.toFixed(1)+'%</span>';\n"
    "  html += '</div>';",
    "  // v5y: Vista DM toggle prominent + mode toggle compact\n"
    "  html += '<div style=\"display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap;\">';\n"
    "  html += '<button class=\"btn ' + (g.dmView ? 'active' : '') + '\" onclick=\"gridToggleDM()\" style=\"font-size:14px;padding:10px 18px;flex:1;min-width:240px;\">';\n"
    "  html += g.dmView ? '👁 Vista DM (todo visible) — click para ocultar' : '👤 Vista jugadores — click para ver TODO (DM)';\n"
    "  html += '</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridSetMode(\\'ascii\\')\" title=\"Cambiar a ASCII default\" style=\"font-size:12px;\">⊞ ASCII</button>';\n"
    "  html += '<span style=\"font-size:11px;color:var(--ink-dim);\">Atajo G · Grid '+wm.cols+'×'+wm.rows+' · Walkable '+wm.walkable_pct.toFixed(1)+'%</span>';\n"
    "  html += '</div>';",
)

# ── 9) Quitar la card "Vista" duplicada del panel derecho (ahora está prominente arriba) ──
patch(
    "remove duplicate Vista card from right panel",
    "  html += '<div class=\"card\" style=\"padding:10px;\"><h3>Vista</h3><button class=\"btn\" onclick=\"gridToggleDM()\" style=\"font-size:14px;width:100%;\">' + (g.dmView ? '👁 DM (ver todo) — click para ocultar' : '👤 Jugadores (con niebla) — click para revelar') + '</button><div style=\"font-size:11px;color:var(--ink-dim);margin-top:6px;\">' + (g.dmView ? 'Modo DM: ves todo el dungeon. Marker celeste sigue visible.' : 'Modo jugadores: solo lo iluminado por LoS o lo ya recorrido.') + '</div></div>';\n"
    "  // Tracker card",
    "  // v5y: 'Vista' card moved to prominent position above map; right panel only has Tracker + Posición.\n"
    "  // Tracker card",
)

# ── 10) Keyboard: agregar 'G' para toggle DM ──
patch(
    "keyboard G shortcut for DM toggle",
    "// Keyboard arrow support\n"
    "document.addEventListener('keydown', function(e) {\n"
    "  if (state.mode !== 'dungeon' || state.dungeonView !== 'grid') return;\n"
    "  if (document.activeElement && document.activeElement.tagName === 'TEXTAREA') return;\n"
    "  let dir = null;\n"
    "  if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') dir = 'up';\n"
    "  else if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') dir = 'down';",
    "// Keyboard arrow support (v5y: + 'G' for DM toggle, + 'T' for +1 turn)\n"
    "document.addEventListener('keydown', function(e) {\n"
    "  if (state.mode !== 'dungeon' || state.dungeonView !== 'grid') return;\n"
    "  if (document.activeElement && (document.activeElement.tagName === 'TEXTAREA' || document.activeElement.tagName === 'INPUT')) return;\n"
    "  if (e.key === 'g' || e.key === 'G') { e.preventDefault(); gridToggleDM(); return; }\n"
    "  if (e.key === 't' || e.key === 'T') { e.preventDefault(); if (typeof gridAddTurn==='function') gridAddTurn(); return; }\n"
    "  let dir = null;\n"
    "  if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') dir = 'up';\n"
    "  else if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') dir = 'down';",
)

# ── 11) gridToggleDM debe redibujar el canvas si estamos en real-mode (sin re-rebuild full) ──
patch(
    "gridToggleDM real-mode optimized",
    "function gridToggleDM() {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  g.dmView = !g.dmView;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}",
    "function gridToggleDM() {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  g.dmView = !g.dmView;\n"
    "  saveState();\n"
    "  // v5y: in real-mode, only redraw canvas + flip the prominent button text via rebuild.\n"
    "  // The prominent button label is in the structural HTML, so we still rerender once.\n"
    "  // Future: target only the toggle button text. For now, full rerender on toggle (rare).\n"
    "  renderGridCrawler();\n"
    "}",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
