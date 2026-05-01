"""
v6i patches: Wallmap v2 fixes + click rooms unificado + Quick Refs ACKS corregido + DM open-cell tool.

CRÍTICO Marcos feedback 2026-05-01: la party no podía moverse por el dungeon
(solo 1.2% reachability). Wallmap v2 (any5x5_white sampling) sube a 90.8%.

Changes:
  - Texto del Quick Refs corregido a ACKS RAW (no D&D5e):
    * SIN infravisión racial. ACKS solo tiene Detect Hidden para Thief/Assassin.
    * Light radius de torch corregido (30 ft + 30 ft dim).
    * Listen y Search rules ACKS textual.
  - Click rooms unificado: TODOS los markers (375 con coords) abren modal.
    Si la sala no está en rooms_full (solo 244 keyed), modal muestra "Sin info
    detallada en el módulo extraído" pero sigue mostrando coords + level.
  - DM tool: ctrl+click sobre cell en modo DM toggle entre wall ↔ floor.
    Override persiste en state.dungeon.grid.wallOverrides[`x,y`] = 0|1.
    `gridIsWalkableReal` consulta overrides primero, luego wallmap default.
  - "Re-init" button: si wallmap default cambia (por nuevo deploy), force-reload.

Pipeline: cp v6h -> v6i, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6i.html")
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
    "<title>Cockpit V6h — v6h: Search/Listen integrados (tirada por clase ACKS)</title>",
    "<title>Cockpit V6i — v6i: Wallmap v2 (90% reachable) + click rooms uniform + ACKS RAW</title>",
)


# ── 2) gridIsWalkableReal: consulta wallOverrides primero ──
patch(
    "gridIsWalkableReal w/ overrides",
    "function gridIsWalkableReal(x, y) {\n"
    "  if (!_realWallmap) return false;\n"
    "  if (y < 0 || y >= _realWallmap.rows || x < 0 || x >= _realWallmap.cols) return false;\n"
    "  return _realWallmap.data[y][x] === 0;\n"
    "}",
    "function gridIsWalkableReal(x, y) {\n"
    "  if (!_realWallmap) return false;\n"
    "  if (y < 0 || y >= _realWallmap.rows || x < 0 || x >= _realWallmap.cols) return false;\n"
    "  // v6i: consult DM-managed wallOverrides first\n"
    "  const g = gridState();\n"
    "  if (g && g.wallOverrides) {\n"
    "    const k = x + ',' + y;\n"
    "    if (g.wallOverrides[k] === 0) return true;   // forced walkable\n"
    "    if (g.wallOverrides[k] === 1) return false;  // forced wall\n"
    "  }\n"
    "  return _realWallmap.data[y][x] === 0;\n"
    "}",
)


# ── 3) Helpers DM open-cell + reset overrides + Quick Refs corregidos ──
patch(
    "v6i DM open cell + ACKS Quick Refs fix",
    "function dgListenAtDoor() {",
    "// === v6i: DM tool — toggle wall/floor en cells (override del wallmap auto) ===\n"
    "function dgToggleCellOverride(cellX, cellY) {\n"
    "  if (!state.dungeon) return;\n"
    "  const g = gridState(); if (!g) return;\n"
    "  if (!g.dmView) { alert('Override solo disponible en Vista DM. Click 👁 primero.'); return; }\n"
    "  if (!g.wallOverrides) g.wallOverrides = {};\n"
    "  const k = cellX + ',' + cellY;\n"
    "  // Cycle: default → walkable → wall → default\n"
    "  if (g.wallOverrides[k] === undefined) g.wallOverrides[k] = 0;        // → walkable\n"
    "  else if (g.wallOverrides[k] === 0) g.wallOverrides[k] = 1;            // → wall\n"
    "  else delete g.wallOverrides[k];                                        // → default\n"
    "  const state2 = g.wallOverrides[k];\n"
    "  const label = state2 === 0 ? 'WALKABLE forzado' : state2 === 1 ? 'WALL forzado' : 'default (auto wallmap)';\n"
    "  logEvent('🔧 DM cell ('+cellX+','+cellY+') override: '+label);\n"
    "  saveState(); renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}\n"
    "function dgClearCellOverrides() {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  if (!confirm('Borrar TODOS los overrides de cells (volver a wallmap auto)?')) return;\n"
    "  g.wallOverrides = {};\n"
    "  saveState();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "  logEvent('🔧 DM cell overrides cleared.');\n"
    "  renderEventLog();\n"
    "}\n"
    "function dgCountCellOverrides() {\n"
    "  const g = gridState();\n"
    "  return (g && g.wallOverrides) ? Object.keys(g.wallOverrides).length : 0;\n"
    "}\n"
    "\n"
    "function dgListenAtDoor() {",
)


# ── 4) Click handler: ctrl+click → toggle override (DM mode) ──
patch(
    "v6i click handler ctrl override",
    "      // v6d: shift+click in DM mode → place trap\n"
    "      const _gg = gridState();\n"
    "      if (e.shiftKey && _gg && _gg.dmView && _realWallmap) {\n"
    "        const wm = _realWallmap;\n"
    "        const SCALE = _realImg.width / wm.stitched_image_dims[0];\n"
    "        const cellSizeDisp = wm.cell_size_px * SCALE;\n"
    "        const cellX = Math.floor(cx / cellSizeDisp);\n"
    "        const cellY = Math.floor(cy / cellSizeDisp);\n"
    "        if (typeof dgPromptPlaceTrap === 'function') dgPromptPlaceTrap(cellX, cellY);\n"
    "        return;\n"
    "      }\n"
    "      if (typeof dgHandleMapClick === 'function') dgHandleMapClick(cx, cy);",
    "      // v6d: shift+click in DM mode → place trap\n"
    "      // v6i: ctrl+click in DM mode → toggle wall/floor override\n"
    "      const _gg = gridState();\n"
    "      if (_gg && _gg.dmView && _realWallmap) {\n"
    "        const wm = _realWallmap;\n"
    "        const SCALE = _realImg.width / wm.stitched_image_dims[0];\n"
    "        const cellSizeDisp = wm.cell_size_px * SCALE;\n"
    "        const cellX = Math.floor(cx / cellSizeDisp);\n"
    "        const cellY = Math.floor(cy / cellSizeDisp);\n"
    "        if (e.ctrlKey || e.metaKey) {\n"
    "          if (typeof dgToggleCellOverride === 'function') dgToggleCellOverride(cellX, cellY);\n"
    "          return;\n"
    "        }\n"
    "        if (e.shiftKey) {\n"
    "          if (typeof dgPromptPlaceTrap === 'function') dgPromptPlaceTrap(cellX, cellY);\n"
    "          return;\n"
    "        }\n"
    "      }\n"
    "      if (typeof dgHandleMapClick === 'function') dgHandleMapClick(cx, cy);",
)


# ── 5) Render: dibujar overrides en canvas (DM only) ──
patch(
    "v6i render overrides on canvas",
    "  if (g.realTail) {\n"
    "    const tx = g.realTail.x * cellSize, ty = g.realTail.y * cellSize;\n"
    "    ctx.fillStyle = 'rgba(41,128,185,0.75)'; ctx.fillRect(tx, ty, cellSize, cellSize);\n"
    "    ctx.strokeStyle = '#0d1117'; ctx.lineWidth = 2; ctx.strokeRect(tx, ty, cellSize, cellSize);\n"
    "  }\n"
    "  // v6c: room markers (dorados)",
    "  if (g.realTail) {\n"
    "    const tx = g.realTail.x * cellSize, ty = g.realTail.y * cellSize;\n"
    "    ctx.fillStyle = 'rgba(41,128,185,0.75)'; ctx.fillRect(tx, ty, cellSize, cellSize);\n"
    "    ctx.strokeStyle = '#0d1117'; ctx.lineWidth = 2; ctx.strokeRect(tx, ty, cellSize, cellSize);\n"
    "  }\n"
    "  // v6i: DM overrides — show forced walkable/wall cells in DM mode\n"
    "  if (g.dmView && g.wallOverrides) {\n"
    "    ctx.save();\n"
    "    for (const k of Object.keys(g.wallOverrides)) {\n"
    "      const parts = k.split(',');\n"
    "      const ox = parseInt(parts[0],10), oy = parseInt(parts[1],10);\n"
    "      const v = g.wallOverrides[k];\n"
    "      const x0 = ox * cellSize, y0 = oy * cellSize;\n"
    "      ctx.fillStyle = v === 0 ? 'rgba(126,231,135,0.45)' : 'rgba(255,75,75,0.55)';\n"
    "      ctx.fillRect(x0, y0, cellSize, cellSize);\n"
    "      ctx.strokeStyle = v === 0 ? '#7ee787' : '#ff4b4b';\n"
    "      ctx.lineWidth = 1;\n"
    "      ctx.strokeRect(x0, y0, cellSize, cellSize);\n"
    "    }\n"
    "    ctx.restore();\n"
    "  }\n"
    "  // v6c: room markers (dorados)",
)


# ── 6) Click rooms unificado: TODOS abren modal aunque rooms_full no tenga la entry ──
patch(
    "v6i click rooms unified modal",
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
    "}",
    "function dgShowRoomInfo(rid) {\n"
    "  // v6i: unified modal — todos los rooms abren modal aunque no haya entry en rooms_full.\n"
    "  let room = null;\n"
    "  let pos = null;\n"
    "  if (_roomsFullCache) {\n"
    "    const rooms = _roomsFullCache.rooms || _roomsFullCache;\n"
    "    room = rooms[rid] || rooms[String(rid)];\n"
    "  }\n"
    "  if (_roomCoordsCache && _roomCoordsCache.room_coords) {\n"
    "    pos = _roomCoordsCache.room_coords[rid] || _roomCoordsCache.room_coords[String(rid)];\n"
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
    "    // v6i: even without rooms_full entry, show useful info\n"
    "    modal += '<div style=\"background:rgba(241,196,15,0.12);padding:10px;border-radius:6px;margin-bottom:12px;border-left:3px solid #f1c40f;\">';\n"
    "    modal += '<b>Sala '+rid+' detectada en el mapa</b>, pero <b>sin entrada en rooms_full</b> (244 rooms keyed; este coord viene de room_coords con 375 rooms detectadas).<br><br>';\n"
    "    modal += '<span style=\"font-size:12px;color:var(--ink-dim);\">Causas posibles: (1) sub-room (74A, 74B…) cuya descripción está en la sala padre; (2) cross-reference numérica en margen del PDF; (3) sala no keyed en este corte del módulo.</span>';\n"
    "    modal += '</div>';\n"
    "  }\n"
    "  if (pos) modal += '<div style=\"font-size:11px;color:var(--ink-dim);\">Coords SVG (800w): ('+pos.x+', '+pos.y+')</div>';\n"
    "  modal += '<div style=\"display:flex;gap:8px;margin-top:12px;\">';\n"
    "  modal += '<button class=\"btn\" onclick=\"document.getElementById(\\'_dg-room-modal\\').remove()\">Cerrar</button>';\n"
    "  modal += '</div>';\n"
    "  modal += '</div></div>';\n"
    "  const existing = document.getElementById('_dg-room-modal');\n"
    "  if (existing) existing.remove();\n"
    "  const tmp = document.createElement('div');\n"
    "  tmp.innerHTML = modal;\n"
    "  document.body.appendChild(tmp.firstChild);\n"
    "}",
)


# NOTE: Quick Refs ACKS RAW corregido con Edit manual fuera del script (anchor era ambiguo, dos copias del bloque).


# ── 8) Boton "DM tools" en Posición real card (overrides) ──
patch(
    "v6i DM tools button in real-mode card",
    "  // v6d: traps management\n"
    "  var _trapsCount = (g.traps||[]).length;\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:8px 0;\">';\n"
    "  html += '<div style=\"font-size:11px;color:var(--ink-dim);margin-bottom:6px;\">DM: shift+click sobre el mapa para colocar trampa.</div>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgListTrapsModal()\" style=\"width:100%;\">⚠ Trampas marcadas ('+_trapsCount+')</button>';\n"
    "  if (_trapsCount > 0) html += '<button class=\"btn secondary\" onclick=\"dgClearAllTraps()\" style=\"width:100%;margin-top:6px;color:#e74c3c;\">Borrar todas</button>';\n"
    "  html += '</div>';",
    "  // v6d: traps management\n"
    "  var _trapsCount = (g.traps||[]).length;\n"
    "  var _overrideCount = (typeof dgCountCellOverrides === 'function') ? dgCountCellOverrides() : 0;\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:8px 0;\">';\n"
    "  html += '<div style=\"font-size:11px;color:var(--ink-dim);margin-bottom:6px;line-height:1.4;\">DM (en vista DM):<br>· <kbd>shift+click</kbd> coloca trampa<br>· <kbd>ctrl+click</kbd> abre/cierra cell (override del wallmap)</div>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgListTrapsModal()\" style=\"width:100%;\">⚠ Trampas marcadas ('+_trapsCount+')</button>';\n"
    "  if (_trapsCount > 0) html += '<button class=\"btn secondary\" onclick=\"dgClearAllTraps()\" style=\"width:100%;margin-top:6px;color:#e74c3c;\">Borrar todas</button>';\n"
    "  if (_overrideCount > 0) html += '<button class=\"btn secondary\" onclick=\"dgClearCellOverrides()\" style=\"width:100%;margin-top:6px;color:#e74c3c;\">Limpiar '+_overrideCount+' overrides de cells</button>';\n"
    "  html += '</div>';",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
