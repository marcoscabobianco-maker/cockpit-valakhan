"""
v6d patches: Trampas place + detect + trigger sobre el grid.

Wildcard mode delivery #4 (acumulativo).

Changes:
  - state.dungeon.grid.traps ya existía (groundwork v5w). Ahora se usa.
  - Modo DM + tecla TRAP-PLACE: shift+click en una cell agrega trap.
  - Cell con trap (detected o triggered) se dibuja con overlay rojo + ⚠.
  - En modo jugador solo se ven detected/triggered.
  - Cuando party-leader entra a cell con trap:
    - Si detected → log informativo, nada pasa.
    - Si no detected → tirada 1d6: 1-2 = detect (party tiene un thief en formación
      vanguardia? +1, si no -1). Si pasa: marca detected. Si falla: triggered →
      banner rojo prominente con desc + save type.
  - Botones helpers: dgClearTraps (DM), dgListTraps (modal con todas).
  - dgPCHpDelta(pcId, -damage) ya disponible para aplicar daño tras trigger.

Pipeline: cp v6c -> v6d, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6d.html")
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
    "<title>Cockpit V6c — v6c: Click rooms keyed (244 rooms con desc/treasure)</title>",
    "<title>Cockpit V6d — v6d: Trampas place + detect + trigger sobre el grid</title>",
)


# ── 2) Helpers de trampas ──
patch(
    "v6d trap helpers",
    "// === v6c: Rooms keyed (244 rooms info) ===",
    "// === v6d: Trampas (place / detect / trigger / render) ===\n"
    "function dgPlaceTrap(cellX, cellY, desc, saveType) {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  if (!g.traps) g.traps = [];\n"
    "  // Replace if already trap at that cell\n"
    "  g.traps = g.traps.filter(t => !(t.x === cellX && t.y === cellY));\n"
    "  g.traps.push({\n"
    "    x: cellX, y: cellY,\n"
    "    desc: desc || 'Trampa sin descripción',\n"
    "    saveType: saveType || 'unknown',\n"
    "    detected: false,\n"
    "    triggered: false,\n"
    "    placedAt: state.dungeon.turns || 0\n"
    "  });\n"
    "  saveState();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "  logEvent('⚠ DM: Trampa colocada en cell ('+cellX+','+cellY+'): '+desc+' [save vs '+saveType+']');\n"
    "  renderEventLog();\n"
    "}\n"
    "function dgRemoveTrap(cellX, cellY) {\n"
    "  const g = gridState(); if (!g || !g.traps) return;\n"
    "  g.traps = g.traps.filter(t => !(t.x === cellX && t.y === cellY));\n"
    "  saveState();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}\n"
    "function dgClearAllTraps() {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  if (!confirm('Borrar TODAS las trampas marcadas?')) return;\n"
    "  g.traps = [];\n"
    "  saveState();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "  logEvent('⚠ DM: trampas borradas.');\n"
    "  renderEventLog();\n"
    "}\n"
    "function dgListTrapsModal() {\n"
    "  const g = gridState();\n"
    "  const traps = (g && g.traps) || [];\n"
    "  let modal = '<div id=\"_dg-traps-modal\" style=\"position:fixed;inset:0;background:rgba(0,0,0,0.75);display:flex;align-items:center;justify-content:center;z-index:9999;\" onclick=\"if(event.target===this)this.remove()\">';\n"
    "  modal += '<div style=\"background:var(--bg-2);max-width:600px;width:90%;max-height:80vh;overflow-y:auto;padding:20px;border-radius:8px;border:1px solid var(--border);\">';\n"
    "  modal += '<div style=\"display:flex;align-items:center;gap:8px;margin-bottom:12px;\"><h2 style=\"margin:0;flex:1;\">⚠ Trampas marcadas ('+traps.length+')</h2>';\n"
    "  modal += '<button class=\"btn secondary\" onclick=\"document.getElementById(\\'_dg-traps-modal\\').remove()\">✕</button></div>';\n"
    "  if (!traps.length) {\n"
    "    modal += '<div style=\"color:var(--ink-dim);\">Sin trampas marcadas. Modo DM: shift+click en una cell para colocar una.</div>';\n"
    "  } else {\n"
    "    for (const t of traps) {\n"
    "      const stateLabel = t.triggered ? '<span style=\"color:#e74c3c;font-weight:bold;\">DISPARADA</span>' : (t.detected ? '<span style=\"color:#f1c40f;\">Detectada</span>' : '<span style=\"color:#aaa;\">Oculta</span>');\n"
    "      modal += '<div style=\"background:rgba(0,0,0,0.3);padding:8px;border-radius:4px;margin:6px 0;border-left:3px solid #e74c3c;\">';\n"
    "      modal += '<div style=\"display:flex;align-items:center;gap:6px;\"><b>Cell ('+t.x+','+t.y+')</b> · '+stateLabel+' · <span style=\"font-size:11px;color:var(--ink-dim);\">vs '+(t.saveType||'?')+'</span><button class=\"btn secondary\" style=\"margin-left:auto;font-size:11px;padding:2px 6px;\" onclick=\"dgRemoveTrap('+t.x+','+t.y+');document.getElementById(\\'_dg-traps-modal\\').remove();\">✕ Borrar</button></div>';\n"
    "      modal += '<div style=\"font-size:13px;margin-top:4px;\">'+escapeHTML(t.desc||'')+'</div>';\n"
    "      modal += '</div>';\n"
    "    }\n"
    "  }\n"
    "  modal += '<div style=\"margin-top:8px;font-size:11px;color:var(--ink-dim);\">DM: shift+click en cell para colocar. Click sobre trampa marcada para info de la sala (rooms tienen prioridad si son cercanas).</div>';\n"
    "  modal += '</div></div>';\n"
    "  const existing = document.getElementById('_dg-traps-modal');\n"
    "  if (existing) existing.remove();\n"
    "  const tmp = document.createElement('div');\n"
    "  tmp.innerHTML = modal;\n"
    "  document.body.appendChild(tmp.firstChild);\n"
    "}\n"
    "function dgPromptPlaceTrap(cellX, cellY) {\n"
    "  const desc = prompt('Descripción de la trampa en cell ('+cellX+','+cellY+'):', 'Pit trap (1d6 dmg)');\n"
    "  if (!desc) return;\n"
    "  const saveType = prompt('Tipo de save (Petrification / Breath / Paralyze / Spells / RodStaff): ', 'Breath');\n"
    "  dgPlaceTrap(cellX, cellY, desc, saveType || 'unknown');\n"
    "}\n"
    "function dgCheckTrapAtCell(cellX, cellY) {\n"
    "  // Called on party entering cell. Returns the trap if triggered/detected, else null.\n"
    "  const g = gridState(); if (!g || !g.traps || !g.traps.length) return null;\n"
    "  const trap = g.traps.find(t => t.x === cellX && t.y === cellY);\n"
    "  if (!trap) return null;\n"
    "  if (trap.detected || trap.triggered) {\n"
    "    if (!trap.triggered) logEvent('⚠ Pasando cerca de la trampa marcada en ('+cellX+','+cellY+'): '+trap.desc);\n"
    "    return trap;\n"
    "  }\n"
    "  // Detection check: 1d6, 1 = detect (assassin/thief in vanguard => 1-2)\n"
    "  let detectThreshold = 1;\n"
    "  // Check if party has thief/assassin in vanguard via partyState\n"
    "  if (state.dungeon && state.dungeon.partyState) {\n"
    "    const pcs = _getPCList();\n"
    "    for (const pc of pcs) {\n"
    "      const ps = state.dungeon.partyState[pc.id];\n"
    "      if (!ps || ps.position !== 'vanguard') continue;\n"
    "      const cls = (pc.class||'').toLowerCase();\n"
    "      if (cls.includes('thief') || cls.includes('assassin') || cls.includes('explorer') || cls.includes('ranger')) {\n"
    "        detectThreshold = 2;\n"
    "        break;\n"
    "      }\n"
    "    }\n"
    "  }\n"
    "  const r = rollDie(6);\n"
    "  if (r <= detectThreshold) {\n"
    "    trap.detected = true;\n"
    "    logEvent('🔍 Trampa DETECTADA en ('+cellX+','+cellY+') (1d6='+r+', umbral '+detectThreshold+'+): '+trap.desc);\n"
    "    saveState();\n"
    "    return trap;\n"
    "  } else {\n"
    "    trap.triggered = true;\n"
    "    logEvent('💥 TRAMPA DISPARADA en ('+cellX+','+cellY+') (1d6='+r+', umbral '+detectThreshold+'+): '+trap.desc+' — save vs '+(trap.saveType||'?'));\n"
    "    saveState();\n"
    "    return trap;\n"
    "  }\n"
    "}\n"
    "\n"
    "// === v6c: Rooms keyed (244 rooms info) ===",
)


# ── 3) gridMoveReal: chequear trampas al entrar cell ──
patch(
    "gridMoveReal trap check",
    "  if (!gridIsWalkableReal(nx, ny)) return;\n"
    "  g.realTail = { x: g.realPlayer.x, y: g.realPlayer.y };\n"
    "  g.realPlayer = { x: nx, y: ny };\n"
    "  g.steps = (g.steps || 0) + 1;",
    "  if (!gridIsWalkableReal(nx, ny)) return;\n"
    "  g.realTail = { x: g.realPlayer.x, y: g.realPlayer.y };\n"
    "  g.realPlayer = { x: nx, y: ny };\n"
    "  g.steps = (g.steps || 0) + 1;\n"
    "  // v6d: trap check at new cell\n"
    "  if (typeof dgCheckTrapAtCell === 'function') dgCheckTrapAtCell(nx, ny);",
)


# ── 4) Render markers traps en redrawGridRealCanvas (después de markers de rooms) ──
patch(
    "v6d draw traps in canvas",
    "  // Party (head + tail) drawn AFTER markers so they overlap (party in front)\n"
    "  const px = g.realPlayer.x * cellSize, py = g.realPlayer.y * cellSize;\n"
    "  ctx.fillStyle = '#5dade2'; ctx.fillRect(px, py, cellSize, cellSize);\n"
    "  ctx.strokeStyle = '#0d1117'; ctx.lineWidth = 2; ctx.strokeRect(px, py, cellSize, cellSize);",
    "  // v6d: trap markers\n"
    "  if (g.traps && g.traps.length) {\n"
    "    ctx.save();\n"
    "    for (const t of g.traps) {\n"
    "      const visibleToPlayer = t.detected || t.triggered;\n"
    "      if (!g.dmView && !visibleToPlayer) continue;\n"
    "      const tx0 = t.x * cellSize, ty0 = t.y * cellSize;\n"
    "      // Different color based on state\n"
    "      let bg, border;\n"
    "      if (t.triggered) { bg = 'rgba(231,76,60,0.55)';  border = '#c0392b'; }\n"
    "      else if (t.detected) { bg = 'rgba(241,196,15,0.4)'; border = '#f1c40f'; }\n"
    "      else { bg = 'rgba(231,76,60,0.25)'; border = '#922b21'; }\n"
    "      ctx.fillStyle = bg;\n"
    "      ctx.fillRect(tx0, ty0, cellSize, cellSize);\n"
    "      ctx.strokeStyle = border;\n"
    "      ctx.lineWidth = 2;\n"
    "      ctx.strokeRect(tx0, ty0, cellSize, cellSize);\n"
    "      // Warning glyph in center\n"
    "      ctx.fillStyle = '#000';\n"
    "      ctx.font = '700 10px sans-serif';\n"
    "      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';\n"
    "      ctx.fillText('⚠', tx0 + cellSize/2, ty0 + cellSize/2);\n"
    "    }\n"
    "    ctx.restore();\n"
    "  }\n"
    "  // Party (head + tail) drawn AFTER markers so they overlap (party in front)\n"
    "  const px = g.realPlayer.x * cellSize, py = g.realPlayer.y * cellSize;\n"
    "  ctx.fillStyle = '#5dade2'; ctx.fillRect(px, py, cellSize, cellSize);\n"
    "  ctx.strokeStyle = '#0d1117'; ctx.lineWidth = 2; ctx.strokeRect(px, py, cellSize, cellSize);",
)


# ── 5) Modify click handler: shift+click → place trap (DM mode), regular click → room info ──
patch(
    "v6d click handler shift place trap",
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
    "  }",
    "  // v6c+v6d: attach click handler. shift+click in DM mode → place trap. plain click → room info.\n"
    "  const _cv = document.getElementById('grid-real-canvas');\n"
    "  if (_cv) {\n"
    "    _cv.addEventListener('click', function(e) {\n"
    "      const rect = _cv.getBoundingClientRect();\n"
    "      const sx = _cv.width / rect.width;\n"
    "      const sy = _cv.height / rect.height;\n"
    "      const cx = (e.clientX - rect.left) * sx;\n"
    "      const cy = (e.clientY - rect.top) * sy;\n"
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
    "      if (typeof dgHandleMapClick === 'function') dgHandleMapClick(cx, cy);\n"
    "    });\n"
    "  }",
)


# ── 6) Banner alertas: trampa triggered ──
patch(
    "v6d alert banner trap triggered",
    "    // v6a: active encounter from Barrowmaze wandering table\n"
    "    if (dgB.activeEncounter) {",
    "    // v6d: trap triggered alert (from any cell entry)\n"
    "    const _gT = (state.dungeon && state.dungeon.grid) || {};\n"
    "    if (_gT.traps && _gT.traps.length) {\n"
    "      // Alert for any newly triggered + not yet resolved\n"
    "      const triggered = _gT.traps.filter(t => t.triggered && !t._resolved);\n"
    "      for (const t of triggered) {\n"
    "        alerts.push({color:'#c0392b', emoji:'💥', msg:'<b>TRAMPA DISPARADA</b> en cell ('+t.x+','+t.y+'): '+escapeHTML(t.desc)+'. <b>Save vs '+escapeHTML(t.saveType||'?')+'</b>. Aplicar daño con −1d6 sobre PCs vanguardia o usar el roster.', action:'dgResolveTrap('+t.x+','+t.y+')', actionLabel:'Resolver'});\n"
    "      }\n"
    "    }\n"
    "    // v6a: active encounter from Barrowmaze wandering table\n"
    "    if (dgB.activeEncounter) {",
)


# ── 7) Helper dgResolveTrap (mark as resolved so banner goes away) ──
patch(
    "v6d dgResolveTrap helper",
    "function dgPromptPlaceTrap(cellX, cellY) {",
    "function dgResolveTrap(x, y) {\n"
    "  const g = gridState(); if (!g || !g.traps) return;\n"
    "  const t = g.traps.find(tt => tt.x === x && tt.y === y);\n"
    "  if (!t) return;\n"
    "  t._resolved = true;\n"
    "  saveState();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "  logEvent('⚠ Trampa ('+x+','+y+') marcada como resuelta. Aplicar consecuencias en mesa.');\n"
    "  renderEventLog();\n"
    "}\n"
    "function dgPromptPlaceTrap(cellX, cellY) {",
)


# ── 8) Botón "⚠ Trampas" en card "Posición real" ──
patch(
    "v6d traps button in real-mode panel",
    "  // Real-mode controls\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\"><h3>Posición real</h3>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetReal74A()\" style=\"width:100%;\">⟲ Reset a Sala 74A</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetSeenReal()\" style=\"width:100%;margin-top:6px;\">⟲ Reset niebla</button>';\n"
    "  html += '</div>';",
    "  // Real-mode controls + traps\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\"><h3>Posición real</h3>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetReal74A()\" style=\"width:100%;\">⟲ Reset a Sala 74A</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetSeenReal()\" style=\"width:100%;margin-top:6px;\">⟲ Reset niebla</button>';\n"
    "  // v6d: traps management\n"
    "  var _trapsCount = (g.traps||[]).length;\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:8px 0;\">';\n"
    "  html += '<div style=\"font-size:11px;color:var(--ink-dim);margin-bottom:6px;\">DM: shift+click sobre el mapa para colocar trampa.</div>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgListTrapsModal()\" style=\"width:100%;\">⚠ Trampas marcadas ('+_trapsCount+')</button>';\n"
    "  if (_trapsCount > 0) html += '<button class=\"btn secondary\" onclick=\"dgClearAllTraps()\" style=\"width:100%;margin-top:6px;color:#e74c3c;\">Borrar todas</button>';\n"
    "  html += '</div>';",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
