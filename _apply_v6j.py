"""
v6j patches: Modal rooms con datos limpios + Wandering auto-combat + Trampas DM-strict.

Marcos feedback 2026-05-01:
  1. Click rooms muestra texto MAL formateado (cross-column bleed). FIX: re-extracted
     barrowmaze_rooms_full.json desde el PDF completo (264p) con parsing column-aware
     + split de stats. Nuevo schema: title / summary / narrative / stats / treasure / page.
  2. Wandering check positivo: solo avisa, debería SWITCHEAR auto a combat panel.
  3. Trampas: en vista jugador NO mostrar nada hasta detected/triggered. Verify.

Pipeline: cp v6i -> v6j, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6j.html")
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
    "<title>Cockpit V6i — v6i: Wallmap v2 (90% reachable) + click rooms uniform + ACKS RAW</title>",
    "<title>Cockpit V6j — v6j: Rooms re-extracted (clean) + wandering auto-combat + traps DM-strict</title>",
)


# ── 2) Modal rooms con nueva estructura (title/summary/narrative/stats/treasure/page) ──
patch(
    "v6j modal rooms with clean data",
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
    "function dgShowRoomInfo(rid) {\n"
    "  // v6j: modal con schema nuevo (title / summary / narrative / stats / treasure / page).\n"
    "  let room = null, pos = null;\n"
    "  if (_roomsFullCache) {\n"
    "    const rooms = _roomsFullCache.rooms || _roomsFullCache;\n"
    "    room = rooms[rid] || rooms[String(rid)];\n"
    "  }\n"
    "  if (_roomCoordsCache && _roomCoordsCache.room_coords) {\n"
    "    pos = _roomCoordsCache.room_coords[rid] || _roomCoordsCache.room_coords[String(rid)];\n"
    "  }\n"
    "  let modal = '<div id=\"_dg-room-modal\" style=\"position:fixed;inset:0;background:rgba(0,0,0,0.75);display:flex;align-items:center;justify-content:center;z-index:9999;\" onclick=\"if(event.target===this)this.remove()\">';\n"
    "  modal += '<div style=\"background:var(--bg-2);max-width:680px;width:90%;max-height:85vh;overflow-y:auto;padding:20px;border-radius:8px;border:1px solid var(--border);box-shadow:0 12px 40px rgba(0,0,0,0.6);\">';\n"
    "  // Header con sala + título limpio\n"
    "  modal += '<div style=\"display:flex;align-items:center;gap:8px;margin-bottom:6px;\">';\n"
    "  const titleStr = room && room.title ? room.title : (room && room.name ? String(room.name).split(',')[0].split(':')[0] : '');\n"
    "  modal += '<h2 style=\"margin:0;flex:1;font-size:18px;\">Sala '+rid+(titleStr ? ': '+escapeHTML(titleStr) : '')+'</h2>';\n"
    "  modal += '<button class=\"btn secondary\" onclick=\"document.getElementById(\\'_dg-room-modal\\').remove()\">✕</button>';\n"
    "  modal += '</div>';\n"
    "  if (room && room.page) modal += '<div style=\"font-size:11px;color:var(--ink-dim);margin-bottom:12px;\">Page '+room.page+' del módulo PDF · ID '+rid+'</div>';\n"
    "  if (room) {\n"
    "    // Schema nuevo (v6j) o legacy\n"
    "    const summary = room.summary || (room.desc ? room.desc.slice(0, 400) + (room.desc.length > 400 ? '…' : '') : null);\n"
    "    const narrative = room.narrative || room.desc || null;\n"
    "    const stats = room.stats || null;\n"
    "    const treasure = room.treasure || room.treasure_coins || null;\n"
    "    if (summary) modal += '<div style=\"line-height:1.6;margin-bottom:12px;font-size:14px;background:rgba(255,255,255,0.03);padding:10px;border-radius:6px;border-left:3px solid #5dade2;\"><b>Resumen:</b> '+escapeHTML(summary)+'</div>';\n"
    "    if (treasure && treasure.length) {\n"
    "      const tArr = Array.isArray(treasure) ? treasure : [treasure];\n"
    "      modal += '<div style=\"background:rgba(212,160,74,0.15);padding:10px;border-radius:6px;margin-bottom:12px;border-left:3px solid #d4a04a;\"><b>💰 Tesoro:</b> '+tArr.map(t => escapeHTML(String(t))).join(', ')+'</div>';\n"
    "    }\n"
    "    if (stats) modal += '<div style=\"background:rgba(231,76,60,0.12);padding:10px;border-radius:6px;margin-bottom:12px;border-left:3px solid #e74c3c;font-family:monospace;font-size:12px;line-height:1.5;\"><b>⚔ Stats / Encounters detectados:</b><br>'+escapeHTML(stats)+'</div>';\n"
    "    if (narrative && narrative !== summary) {\n"
    "      modal += '<details style=\"margin-bottom:8px;\"><summary style=\"cursor:pointer;font-size:12px;color:var(--ink-dim);padding:6px;\">Ver narrativa completa (puede tener artefactos del extractor)</summary>';\n"
    "      modal += '<div style=\"line-height:1.6;font-size:13px;white-space:pre-line;padding:8px;background:rgba(0,0,0,0.2);border-radius:4px;\">'+escapeHTML(narrative)+'</div>';\n"
    "      modal += '</details>';\n"
    "    }\n"
    "  } else {\n"
    "    modal += '<div style=\"background:rgba(241,196,15,0.12);padding:10px;border-radius:6px;margin-bottom:12px;border-left:3px solid #f1c40f;\">';\n"
    "    modal += '<b>Sala '+rid+' detectada en el mapa</b>, pero <b>sin descripción en el módulo extraído</b>.<br><br>';\n"
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


# ── 3) Wandering check positivo → switchear auto a combat panel después de 1.5s ──
patch(
    "v6j wandering auto-combat",
    "    if (state.dungeon.id === 'barrowmaze' && typeof dgRollBarrowmazeEncounter === 'function') {\n"
    "      const enc = dgRollBarrowmazeEncounter();\n"
    "      if (enc) {\n"
    "        state.dungeon.activeEncounter = enc;\n"
    "        logEvent('🜍 ENCUENTRO Barrowmaze (1d20='+enc.rollD20+'): '+enc.count+'× '+enc.name +\n"
    "          ' (HD '+enc.hd+' AC '+enc.ac+' DMG '+enc.dmg+') a '+enc.distance+' ft. ' +\n"
    "          (enc.surpriseParty ? '⚡ Party SORPRENDIDA. ' : '') +\n"
    "          (enc.surpriseMonsters ? '✨ Monsters SORPRENDIDOS. ' : '') +\n"
    "          enc.notes, '1d6='+r.total+noiseStr);\n"
    "      }\n"
    "    } else {",
    "    if (state.dungeon.id === 'barrowmaze' && typeof dgRollBarrowmazeEncounter === 'function') {\n"
    "      const enc = dgRollBarrowmazeEncounter();\n"
    "      if (enc) {\n"
    "        state.dungeon.activeEncounter = enc;\n"
    "        logEvent('🜍 ENCUENTRO Barrowmaze (1d20='+enc.rollD20+'): '+enc.count+'× '+enc.name +\n"
    "          ' (HD '+enc.hd+' AC '+enc.ac+' DMG '+enc.dmg+') a '+enc.distance+' ft. ' +\n"
    "          (enc.surpriseParty ? '⚡ Party SORPRENDIDA. ' : '') +\n"
    "          (enc.surpriseMonsters ? '✨ Monsters SORPRENDIDOS. ' : '') +\n"
    "          enc.notes, '1d6='+r.total+noiseStr);\n"
    "        // v6j: auto-switch to combat panel after a short delay (allows dismiss banner)\n"
    "        setTimeout(() => {\n"
    "          if (state.dungeon && state.dungeon.activeEncounter && typeof dgEncounterToCombat === 'function') {\n"
    "            dgEncounterToCombat();\n"
    "          }\n"
    "        }, 1800);\n"
    "      }\n"
    "    } else {",
)


# ── 4) Trampas: render canvas estricto - en vista jugador SOLO si triggered ──
# Antes: detected o triggered hacían visible. Ahora: solo triggered (DM puede revelar via toggle).
patch(
    "v6j traps strict DM-only (player sees only triggered)",
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
    "  }",
    "  // v6j: trap markers — STRICT DM mode. Players only see TRIGGERED traps.\n"
    "  // Detected (pero no triggered) sólo visibles en DM mode — DM decide cuándo revelar.\n"
    "  if (g.traps && g.traps.length) {\n"
    "    ctx.save();\n"
    "    for (const t of g.traps) {\n"
    "      // Player view: ONLY triggered traps. Detected stays hidden hasta DM revele.\n"
    "      const playerCanSee = t.triggered === true;\n"
    "      if (!g.dmView && !playerCanSee) continue;\n"
    "      const tx0 = t.x * cellSize, ty0 = t.y * cellSize;\n"
    "      let bg, border;\n"
    "      if (t.triggered) { bg = 'rgba(231,76,60,0.55)';  border = '#c0392b'; }\n"
    "      else if (t.detected) { bg = 'rgba(241,196,15,0.4)'; border = '#f1c40f'; }\n"
    "      else { bg = 'rgba(231,76,60,0.25)'; border = '#922b21'; }\n"
    "      ctx.fillStyle = bg;\n"
    "      ctx.fillRect(tx0, ty0, cellSize, cellSize);\n"
    "      ctx.strokeStyle = border;\n"
    "      ctx.lineWidth = 2;\n"
    "      ctx.strokeRect(tx0, ty0, cellSize, cellSize);\n"
    "      ctx.fillStyle = '#000';\n"
    "      ctx.font = '700 10px sans-serif';\n"
    "      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';\n"
    "      ctx.fillText('⚠', tx0 + cellSize/2, ty0 + cellSize/2);\n"
    "    }\n"
    "    ctx.restore();\n"
    "  }",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
