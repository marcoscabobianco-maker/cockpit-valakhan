"""
v6c patches: Click rooms keyed (244 rooms con desc/treasure) sobre el mapa.

Wildcard mode delivery #3 (acumulativo sobre v6a + v6b).

Changes:
  - dgLoadRoomsData(): async fetch de barrowmaze_room_coords.json + barrowmaze_rooms_full.json
    desde maps/.
  - Render markers dorados (4px radius) sobre el canvas en cada room conocida.
  - Visibility de markers: en DM mode todos visibles; en player mode solo si la cell
    de la room está en seenSet.
  - Click handler en canvas: detecta room cercana (<20 px), muestra modal info con:
    name, area, chunk, descripción narrativa, treasure_coins.
  - Modal con close button, oscurece fondo, click fuera cierra.

Pipeline: cp v6b -> v6c, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6c.html")
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
    "<title>Cockpit V6b — v6b: PC roster (11 novatos) + formación + lightBearer</title>",
    "<title>Cockpit V6c — v6c: Click rooms keyed (244 rooms con desc/treasure)</title>",
)


# ── 2) Helpers de carga + modal info ──
patch(
    "v6c rooms data + modal helpers",
    "function _renderPartyCard() {",
    "// === v6c: Rooms keyed (244 rooms info) ===\n"
    "const BARROWMAZE_ROOMS_COORDS_SRC = 'maps/barrowmaze_room_coords.json';\n"
    "const BARROWMAZE_ROOMS_FULL_SRC  = 'maps/barrowmaze_rooms_full.json';\n"
    "let _roomCoordsCache = null;\n"
    "let _roomsFullCache = null;\n"
    "let _roomsLoading = false;\n"
    "function dgLoadRoomsData() {\n"
    "  if (_roomCoordsCache && _roomsFullCache) return Promise.resolve({coords:_roomCoordsCache, full:_roomsFullCache});\n"
    "  if (_roomsLoading) return new Promise((res) => {\n"
    "    var iv = setInterval(() => { if (_roomCoordsCache && _roomsFullCache) { clearInterval(iv); res({coords:_roomCoordsCache, full:_roomsFullCache}); } }, 100);\n"
    "  });\n"
    "  _roomsLoading = true;\n"
    "  return Promise.all([\n"
    "    fetch(BARROWMAZE_ROOMS_COORDS_SRC).then(r => r.ok ? r.json() : null).catch(() => null).then(d => { _roomCoordsCache = d; }),\n"
    "    fetch(BARROWMAZE_ROOMS_FULL_SRC).then(r => r.ok ? r.json() : null).catch(() => null).then(d => { _roomsFullCache = d; })\n"
    "  ]).then(() => { _roomsLoading = false; return {coords:_roomCoordsCache, full:_roomsFullCache}; });\n"
    "}\n"
    "function dgShowRoomInfo(rid) {\n"
    "  let room = null;\n"
    "  if (_roomsFullCache) {\n"
    "    const rooms = _roomsFullCache.rooms || _roomsFullCache;\n"
    "    room = rooms[rid] || rooms[String(rid)];\n"
    "  }\n"
    "  let modal = '<div id=\"_dg-room-modal\" style=\"position:fixed;inset:0;background:rgba(0,0,0,0.75);display:flex;align-items:center;justify-content:center;z-index:9999;\" onclick=\"if(event.target===this)this.remove()\">';\n"
    "  modal += '<div style=\"background:var(--bg-2);max-width:640px;width:90%;max-height:80vh;overflow-y:auto;padding:20px;border-radius:8px;border:1px solid var(--border);box-shadow:0 12px 40px rgba(0,0,0,0.6);\">';\n"
    "  modal += '<div style=\"display:flex;align-items:center;gap:8px;margin-bottom:8px;\">';\n"
    "  modal += '<h2 style=\"margin:0;flex:1;\">Sala '+rid+(room && room.name ? ': '+escapeHTML(String(room.name).split(',')[0].split(':')[0]) : '')+'</h2>';\n"
    "  modal += '<button class=\"btn secondary\" onclick=\"document.getElementById(\\'_dg-room-modal\\').remove()\">✕</button>';\n"
    "  modal += '</div>';\n"
    "  if (room) {\n"
    "    const meta = [];\n"
    "    if (room.area)  meta.push('Área: <b>'+escapeHTML(room.area)+'</b>');\n"
    "    if (room.chunk) meta.push('Chunk: <b>'+escapeHTML(room.chunk)+'</b>');\n"
    "    if (meta.length) modal += '<div style=\"font-size:12px;color:var(--ink-dim);margin-bottom:12px;\">'+meta.join(' · ')+'</div>';\n"
    "    if (room.desc) modal += '<div style=\"line-height:1.6;margin-bottom:12px;white-space:pre-line;font-size:14px;\">'+escapeHTML(room.desc)+'</div>';\n"
    "    if (room.treasure_coins && room.treasure_coins.length) {\n"
    "      modal += '<div style=\"background:rgba(212,160,74,0.15);padding:10px;border-radius:6px;margin-bottom:12px;border-left:3px solid #d4a04a;\"><b>💰 Tesoro:</b> '+room.treasure_coins.map(t => escapeHTML(String(t))).join(', ')+'</div>';\n"
    "    }\n"
    "  } else {\n"
    "    modal += '<div style=\"color:var(--ink-dim);\">Sin info detallada en barrowmaze_rooms_full.json para esta sala. Solo posición conocida.</div>';\n"
    "  }\n"
    "  modal += '<div style=\"display:flex;gap:8px;margin-top:12px;\">';\n"
    "  modal += '<button class=\"btn\" onclick=\"document.getElementById(\\'_dg-room-modal\\').remove()\">Cerrar</button>';\n"
    "  modal += '</div>';\n"
    "  modal += '</div></div>';\n"
    "  // Remove existing modal if any\n"
    "  const existing = document.getElementById('_dg-room-modal');\n"
    "  if (existing) existing.remove();\n"
    "  const tmp = document.createElement('div');\n"
    "  tmp.innerHTML = modal;\n"
    "  document.body.appendChild(tmp.firstChild);\n"
    "}\n"
    "function dgHandleMapClick(canvasX, canvasY) {\n"
    "  if (!_realImg || !_roomCoordsCache || !_roomCoordsCache.room_coords) return;\n"
    "  const sx = _realImg.width  / _roomCoordsCache.svg_w;\n"
    "  const sy = _realImg.height / _roomCoordsCache.svg_h;\n"
    "  const threshold = 22;\n"
    "  let closest = null, closestDist = Infinity;\n"
    "  for (const rid of Object.keys(_roomCoordsCache.room_coords)) {\n"
    "    const pos = _roomCoordsCache.room_coords[rid];\n"
    "    const x = pos.x * sx, y = pos.y * sy;\n"
    "    const d = Math.hypot(x - canvasX, y - canvasY);\n"
    "    if (d < threshold && d < closestDist) { closest = rid; closestDist = d; }\n"
    "  }\n"
    "  if (closest) dgShowRoomInfo(closest);\n"
    "}\n"
    "\nfunction _renderPartyCard() {",
)


# ── 3) Trigger load + render markers en redrawGridRealCanvas ──
patch(
    "v6c draw room markers + click handler",
    "  if (g.realTail) {\n"
    "    const tx = g.realTail.x * cellSize, ty = g.realTail.y * cellSize;\n"
    "    ctx.fillStyle = 'rgba(41,128,185,0.75)'; ctx.fillRect(tx, ty, cellSize, cellSize);\n"
    "    ctx.strokeStyle = '#0d1117'; ctx.lineWidth = 2; ctx.strokeRect(tx, ty, cellSize, cellSize);\n"
    "  }\n"
    "  const px = g.realPlayer.x * cellSize, py = g.realPlayer.y * cellSize;\n"
    "  ctx.fillStyle = '#5dade2'; ctx.fillRect(px, py, cellSize, cellSize);\n"
    "  ctx.strokeStyle = '#0d1117'; ctx.lineWidth = 2; ctx.strokeRect(px, py, cellSize, cellSize);",
    "  if (g.realTail) {\n"
    "    const tx = g.realTail.x * cellSize, ty = g.realTail.y * cellSize;\n"
    "    ctx.fillStyle = 'rgba(41,128,185,0.75)'; ctx.fillRect(tx, ty, cellSize, cellSize);\n"
    "    ctx.strokeStyle = '#0d1117'; ctx.lineWidth = 2; ctx.strokeRect(tx, ty, cellSize, cellSize);\n"
    "  }\n"
    "  // v6c: room markers (dorados)\n"
    "  if (_roomCoordsCache && _roomCoordsCache.room_coords) {\n"
    "    const sx = img.width  / _roomCoordsCache.svg_w;\n"
    "    const sy = img.height / _roomCoordsCache.svg_h;\n"
    "    ctx.save();\n"
    "    for (const rid of Object.keys(_roomCoordsCache.room_coords)) {\n"
    "      const pos = _roomCoordsCache.room_coords[rid];\n"
    "      const x = pos.x * sx, y = pos.y * sy;\n"
    "      let show = false;\n"
    "      if (g.dmView) show = true;\n"
    "      else {\n"
    "        const cellX = Math.floor(x / cellSize), cellY = Math.floor(y / cellSize);\n"
    "        if (seenSet.has(gridKey(cellX, cellY))) show = true;\n"
    "      }\n"
    "      if (!show) continue;\n"
    "      ctx.fillStyle = 'rgba(212,160,74,0.92)';\n"
    "      ctx.strokeStyle = '#0d1117';\n"
    "      ctx.lineWidth = 1.5;\n"
    "      ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI*2); ctx.fill(); ctx.stroke();\n"
    "      // Optional: small label of room number for DM\n"
    "      if (g.dmView) {\n"
    "        ctx.fillStyle = '#000';\n"
    "        ctx.font = '600 9px sans-serif';\n"
    "        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';\n"
    "        ctx.fillText(rid, x, y);\n"
    "      }\n"
    "    }\n"
    "    ctx.restore();\n"
    "  }\n"
    "  // Party (head + tail) drawn AFTER markers so they overlap (party in front)\n"
    "  const px = g.realPlayer.x * cellSize, py = g.realPlayer.y * cellSize;\n"
    "  ctx.fillStyle = '#5dade2'; ctx.fillRect(px, py, cellSize, cellSize);\n"
    "  ctx.strokeStyle = '#0d1117'; ctx.lineWidth = 2; ctx.strokeRect(px, py, cellSize, cellSize);",
)


# ── 4) Trigger load on mode 'real' switch ──
patch(
    "v6c trigger rooms load on real mode",
    "  if (mode === 'real') {\n"
    "    const wrap = document.getElementById('grid-crawler-container');\n"
    "    if (wrap) wrap.innerHTML = '<div style=\"color:var(--ink-dim);padding:20px;\">Cargando mapa real (Barrowmaze stitched + walls)…</div>';\n"
    "    gridLoadRealMap().then(({wm}) => {",
    "  if (mode === 'real') {\n"
    "    const wrap = document.getElementById('grid-crawler-container');\n"
    "    if (wrap) wrap.innerHTML = '<div style=\"color:var(--ink-dim);padding:20px;\">Cargando mapa real (Barrowmaze stitched + walls + 244 rooms)…</div>';\n"
    "    // v6c: kick off rooms data load in parallel (non-blocking, redraw will pick it up)\n"
    "    if (typeof dgLoadRoomsData === 'function') dgLoadRoomsData().then(() => { if (typeof redrawGridRealCanvas === 'function') redrawGridRealCanvas(); }).catch(()=>{});\n"
    "    gridLoadRealMap().then(({wm}) => {",
)


# ── 5) Click handler en canvas (in renderGridReal, after wrap.innerHTML = html) ──
patch(
    "v6c click handler in renderGridReal",
    "  wrap.innerHTML = html;\n"
    "  // v5y: delegate canvas drawing to redrawGridRealCanvas() so movement can call it directly\n"
    "  redrawGridRealCanvas();\n"
    "}",
    "  wrap.innerHTML = html;\n"
    "  // v6c: attach click handler for room markers\n"
    "  const _cv = document.getElementById('grid-real-canvas');\n"
    "  if (_cv) {\n"
    "    _cv.addEventListener('click', function(e) {\n"
    "      const rect = _cv.getBoundingClientRect();\n"
    "      const sx = _cv.width / rect.width;\n"
    "      const sy = _cv.height / rect.height;\n"
    "      const cx = (e.clientX - rect.left) * sx;\n"
    "      const cy = (e.clientY - rect.top) * sy;\n"
    "      if (typeof dgHandleMapClick === 'function') dgHandleMapClick(cx, cy);\n"
    "    });\n"
    "  }\n"
    "  // v5y: delegate canvas drawing to redrawGridRealCanvas() so movement can call it directly\n"
    "  redrawGridRealCanvas();\n"
    "}",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
