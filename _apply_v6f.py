"""
v6f patches: Soporte multi-level Arden Vul (Ardis Vala) — viewer simple.

Wildcard mode delivery #6 (acumulativo).

Changes:
  - Detecta dungeon.type === 'multi-level' (Ardis Vala / Arden Vul).
  - Loader async del manifest + per-level (bg + coords).
  - Selector de level (dropdown) con los 27 levels (10 main + 17 sublevels).
  - Canvas-based viewer simple: bg image + markers dorados de las rooms detectadas
    por OCR (1293 rooms total).
  - Click marker → alert con room ID + level name (sin rooms_full por ahora).
  - Mantiene Barrowmaze (single-level) intacto con grid táctico real V6e.
  - SIN walls vectorizadas / LoS para Arden Vul (pendiente: generar wallmaps con
    pipeline sample-based por level). Marker-only viewer es deliberadamente simple.

Pipeline: cp v6e -> v6f, this script.
Asegurarse: maps/arden_vul/ copiados al deploy folder (27 bg + 27 coords + manifest).
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6f.html")
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
    "<title>Cockpit V6e — v6e: Wildcard polish (ACKS Assistant link + Quick refs + atajos)</title>",
    "<title>Cockpit V6f — v6f: Arden Vul multi-level viewer (27 levels, 1293 rooms OCR)</title>",
)


# ── 2) Helpers Arden Vul ──
patch(
    "v6f arden vul helpers",
    "// === v6c: Rooms keyed (244 rooms info) ===",
    "// === v6f: Arden Vul (Ardis Vala) multi-level viewer ===\n"
    "let _ardenManifest = null;\n"
    "const _ardenCache = {}; // {levelId: {bg: Image, coords: data, lvl: entry}}\n"
    "let _ardenLoadingLevel = null;\n"
    "\n"
    "function dgArdenLoadLevel(levelId) {\n"
    "  if (_ardenCache[levelId]) return Promise.resolve(_ardenCache[levelId]);\n"
    "  if (_ardenLoadingLevel === levelId) return new Promise((res) => {\n"
    "    var iv = setInterval(() => { if (_ardenCache[levelId]) { clearInterval(iv); res(_ardenCache[levelId]); } }, 100);\n"
    "  });\n"
    "  _ardenLoadingLevel = levelId;\n"
    "  const dgData = (state.world && state.world.dungeons && state.world.dungeons.ardis_vala) || null;\n"
    "  if (!dgData || !dgData.levels) return Promise.resolve(null);\n"
    "  const lvl = dgData.levels.find(l => l.id === levelId);\n"
    "  if (!lvl) return Promise.resolve(null);\n"
    "  return Promise.all([\n"
    "    fetch(lvl.coords_url).then(r => r.ok ? r.json() : null).catch(() => null),\n"
    "    new Promise((res, rej) => { var im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = lvl.bg_url; })\n"
    "  ]).then(([coords, img]) => {\n"
    "    _ardenCache[levelId] = { coords, img, lvl };\n"
    "    _ardenLoadingLevel = null;\n"
    "    return _ardenCache[levelId];\n"
    "  });\n"
    "}\n"
    "\n"
    "function dgArdenSwitchLevel(levelId) {\n"
    "  if (!state.dungeon) return;\n"
    "  state.dungeon.activeLevel = levelId;\n"
    "  saveState();\n"
    "  const wrap = document.getElementById('grid-crawler-container');\n"
    "  if (wrap && !_ardenCache[levelId]) wrap.innerHTML = '<div style=\"color:var(--ink-dim);padding:20px;\">Cargando '+levelId+'…</div>';\n"
    "  dgArdenLoadLevel(levelId).then(() => renderGridCrawler()).catch(err => { console.error(err); wrap && (wrap.innerHTML = '<div>Error cargando level: '+(err.message||err)+'</div>'); });\n"
    "}\n"
    "\n"
    "function renderArdenVulViewer() {\n"
    "  const wrap = document.getElementById('grid-crawler-container');\n"
    "  if (!wrap) return;\n"
    "  const dgData = (state.world && state.world.dungeons && state.world.dungeons.ardis_vala) || null;\n"
    "  if (!dgData || dgData.type !== 'multi-level') {\n"
    "    wrap.innerHTML = '<div style=\"color:var(--ink-dim);padding:20px;\">Ardis Vala no es multi-level en el JSON. Verificar campaign data.</div>';\n"
    "    return;\n"
    "  }\n"
    "  const activeLvlId = state.dungeon.activeLevel || dgData.startLevel || dgData.levels[0].id;\n"
    "  const cached = _ardenCache[activeLvlId];\n"
    "  if (!cached) {\n"
    "    wrap.innerHTML = '<div style=\"color:var(--ink-dim);padding:20px;\">Cargando '+activeLvlId+' (Arden Vul · 27 levels disponibles)…</div>';\n"
    "    dgArdenLoadLevel(activeLvlId).then(() => renderGridCrawler()).catch(err => {\n"
    "      wrap.innerHTML = '<div style=\"color:#e74c3c;padding:20px;\">Error: '+(err.message||err)+'</div>';\n"
    "    });\n"
    "    return;\n"
    "  }\n"
    "  const rc = (cached.coords && cached.coords.room_coords) || {};\n"
    "  const numRooms = Object.keys(rc).length;\n"
    "  let html = '';\n"
    "  // Selector de level + info\n"
    "  html += '<div style=\"display:flex;gap:8px;align-items:center;margin-bottom:10px;flex-wrap:wrap;\">';\n"
    "  html += '<label style=\"font-size:13px;font-weight:600;\">🏛 Nivel:</label>';\n"
    "  html += '<select onchange=\"dgArdenSwitchLevel(this.value)\" style=\"flex:1;min-width:240px;font-size:13px;padding:6px 8px;background:var(--bg-2);color:var(--ink);border:1px solid var(--border);border-radius:4px;\">';\n"
    "  for (const l of dgData.levels) {\n"
    "    html += '<option value=\"'+l.id+'\"'+(l.id === activeLvlId ? ' selected' : '')+'>'+escapeHTML(l.name)+'</option>';\n"
    "  }\n"
    "  html += '</select>';\n"
    "  html += '<span style=\"font-size:11px;color:var(--ink-dim);white-space:nowrap;\">'+numRooms+' rooms (OCR)</span>';\n"
    "  html += '</div>';\n"
    "  // Canvas + sidecard\n"
    "  html += '<div style=\"display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start;\">';\n"
    "  html += '<div style=\"flex:1;min-width:300px;\">';\n"
    "  html += '<div class=\"grid-real-wrap\" id=\"arden-wrap\">';\n"
    "  html += '<canvas id=\"arden-canvas\" class=\"grid-real-canvas\" width=\"'+cached.img.width+'\" height=\"'+cached.img.height+'\"></canvas>';\n"
    "  html += '</div>';\n"
    "  html += '<div class=\"grid-info\" style=\"margin-top:6px;\"><b>'+escapeHTML(cached.lvl.name)+'</b> · Page PDF: '+cached.lvl.page_pdf+' · BG: '+cached.lvl.bg_w+'×'+cached.lvl.bg_h+'</div>';\n"
    "  html += '<div class=\"grid-info\" style=\"font-size:11px;color:var(--ink-dim);margin-top:2px;\">Click sobre marker dorado → ID de sala. Arden Vul aún sin walls vectorizadas (no LoS / no grid táctico). Solo viewer multi-level.</div>';\n"
    "  html += '</div>';\n"
    "  // Right side card\n"
    "  html += '<div style=\"flex:1;min-width:280px;max-width:340px;\">';\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>🏛 Ardis Vala — Multi-level</h3>';\n"
    "  html += '<div style=\"font-size:13px;line-height:1.6;color:var(--ink);\">';\n"
    "  html += '<p style=\"margin:4px 0;\"><b>27 niveles</b> (10 main + 17 sublevels) extraídos del PDF.</p>';\n"
    "  html += '<p style=\"margin:4px 0;\"><b>~1293 rooms</b> auto-detectadas con OCR (cobertura ~80%).</p>';\n"
    "  html += '<p style=\"margin:4px 0;\">Status: <b style=\"color:'+(dgData.status === 'not_entered_party' ? '#aaa' : '#7ee787')+';\">'+escapeHTML(dgData.status||'?')+'</b></p>';\n"
    "  if (dgData._lore) html += '<div style=\"margin-top:8px;font-style:italic;color:var(--ink-dim);font-size:12px;line-height:1.5;border-left:2px solid var(--border);padding-left:8px;\">'+escapeHTML(dgData._lore.slice(0,260))+(dgData._lore.length > 260 ? '…' : '')+'</div>';\n"
    "  html += '</div>';\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:10px 0;\">';\n"
    "  html += '<div style=\"font-size:11px;color:var(--ink-dim);line-height:1.5;\">';\n"
    "  html += '<b>Limitaciones actuales:</b><br>';\n"
    "  html += '• Sin walls vectorizadas (a diferencia de Barrowmaze).<br>';\n"
    "  html += '• Sin LoS / fog of war / party rect.<br>';\n"
    "  html += '• Sin tracker de turnos integrado.<br>';\n"
    "  html += '• Sin info detallada de rooms (rooms_full no extraído todavía).<br>';\n"
    "  html += '<b>Para upgrade futuro:</b> generar wallmaps por level con pipeline sample-based (ya validado en Barrowmaze).';\n"
    "  html += '</div>';\n"
    "  html += '</div>';\n"
    "  // Quick navigation by level group\n"
    "  html += '<div class=\"card\" style=\"padding:10px;margin-top:10px;\">';\n"
    "  html += '<h3 style=\"font-size:13px;\">Navegación rápida</h3>';\n"
    "  html += '<div style=\"display:flex;gap:4px;flex-wrap:wrap;font-size:11px;\">';\n"
    "  for (const l of dgData.levels) {\n"
    "    const isMain = !l.id.startsWith('SL');\n"
    "    const active = l.id === activeLvlId;\n"
    "    html += '<button class=\"btn '+(active?'':'secondary')+'\" style=\"font-size:11px;padding:3px 6px;min-height:24px;'+(isMain?'':'opacity:0.75;')+'\" onclick=\"dgArdenSwitchLevel(\\''+l.id+'\\')\">'+l.id+'</button>';\n"
    "  }\n"
    "  html += '</div>';\n"
    "  html += '</div>';\n"
    "  html += '</div>';\n"
    "  html += '</div>';\n"
    "  wrap.innerHTML = html;\n"
    "  // Draw canvas\n"
    "  const canvas = document.getElementById('arden-canvas');\n"
    "  if (!canvas) return;\n"
    "  const ctx = canvas.getContext('2d');\n"
    "  ctx.drawImage(cached.img, 0, 0);\n"
    "  // Markers\n"
    "  const sx = cached.img.width / ((cached.coords && cached.coords.bg_w) || 1600);\n"
    "  const sy = cached.img.height / ((cached.coords && cached.coords.bg_h) || cached.img.height);\n"
    "  for (const rid of Object.keys(rc)) {\n"
    "    const pos = rc[rid];\n"
    "    const x = pos.x * sx, y = pos.y * sy;\n"
    "    ctx.fillStyle = 'rgba(212,160,74,0.92)';\n"
    "    ctx.strokeStyle = '#0d1117';\n"
    "    ctx.lineWidth = 1.5;\n"
    "    ctx.beginPath(); ctx.arc(x, y, 8, 0, Math.PI*2); ctx.fill(); ctx.stroke();\n"
    "    ctx.fillStyle = '#000';\n"
    "    ctx.font = '600 9px sans-serif';\n"
    "    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';\n"
    "    ctx.fillText(rid, x, y);\n"
    "  }\n"
    "  // Click handler\n"
    "  canvas.addEventListener('click', function(e) {\n"
    "    const rect = canvas.getBoundingClientRect();\n"
    "    const cx = (e.clientX - rect.left) * (canvas.width / rect.width);\n"
    "    const cy = (e.clientY - rect.top) * (canvas.height / rect.height);\n"
    "    let closest = null, dist = Infinity;\n"
    "    for (const rid of Object.keys(rc)) {\n"
    "      const pos = rc[rid];\n"
    "      const x = pos.x * sx, y = pos.y * sy;\n"
    "      const d = Math.hypot(x - cx, y - cy);\n"
    "      if (d < 30 && d < dist) { closest = rid; dist = d; }\n"
    "    }\n"
    "    if (closest) {\n"
    "      const p = rc[closest];\n"
    "      alert('Sala '+closest+'\\nNivel: '+cached.lvl.name+'\\nCoord: ('+p.x+', '+p.y+')\\n\\nInfo detallada (descripción, treasure, NPCs) aún no integrada para Arden Vul.\\n\\nPara ver descripción del módulo, consultar el PDF original (page '+cached.lvl.page_pdf+').');\n"
    "    }\n"
    "  });\n"
    "}\n"
    "\n"
    "// === v6c: Rooms keyed (244 rooms info) ===",
)


# ── 3) renderGridCrawler dispatch para multi-level ──
patch(
    "v6f renderGridCrawler dispatch multi-level",
    "  // v5x: dispatch to real renderer if mode='real'\n"
    "  const _g0 = gridState();\n"
    "  if (_g0 && _g0.mode === 'real') return renderGridReal();\n"
    "  const g = gridState();",
    "  // v6f: dispatch multi-level dungeons (Arden Vul / Ardis Vala) to its viewer\n"
    "  const _dgData = (state.world && state.world.dungeons && state.world.dungeons[state.dungeon.id]) || null;\n"
    "  if (_dgData && _dgData.type === 'multi-level') {\n"
    "    return renderArdenVulViewer();\n"
    "  }\n"
    "  // v5x: dispatch to real renderer if mode='real'\n"
    "  const _g0 = gridState();\n"
    "  if (_g0 && _g0.mode === 'real') return renderGridReal();\n"
    "  const g = gridState();",
)


# ── 4) loadDungeon: para multi-level, no auto-set 'real' mode (no aplica) ──
patch(
    "v6f loadDungeon multi-level skip real auto",
    "  // v5y: only grid view exists; if Barrowmaze and grid hasn't switched to real yet, do it.\n"
    "  state.dungeonView = 'grid';\n"
    "  setDungeonView('grid');\n"
    "  if (state.dungeon && state.dungeon.id === 'barrowmaze' && state.dungeon.grid && state.dungeon.grid.mode !== 'real') {\n"
    "    setTimeout(() => { try { gridSetMode('real'); } catch(e){} }, 50);\n"
    "  }",
    "  // v5y: only grid view exists; if Barrowmaze and grid hasn't switched to real yet, do it.\n"
    "  // v6f: for multi-level dungeons (ardis_vala), no real-mode (uses Arden Vul viewer).\n"
    "  state.dungeonView = 'grid';\n"
    "  setDungeonView('grid');\n"
    "  if (state.dungeon) {\n"
    "    const _dgD = (state.world && state.world.dungeons && state.world.dungeons[state.dungeon.id]) || null;\n"
    "    if (_dgD && _dgD.type === 'multi-level') {\n"
    "      // Ensure activeLevel is set\n"
    "      if (!state.dungeon.activeLevel) state.dungeon.activeLevel = _dgD.startLevel || (_dgD.levels && _dgD.levels[0] && _dgD.levels[0].id);\n"
    "    } else if (state.dungeon.id === 'barrowmaze' && state.dungeon.grid && state.dungeon.grid.mode !== 'real') {\n"
    "      setTimeout(() => { try { gridSetMode('real'); } catch(e){} }, 50);\n"
    "    }\n"
    "  }",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
