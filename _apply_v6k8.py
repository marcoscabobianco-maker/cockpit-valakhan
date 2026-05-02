# V6k8: integrar rooms_full v3 al cockpit. Q/D muestran todas las instancias.

import re, sys

SRC = 'prototipo_v6k7.html'
DST = 'prototipo_v6k8.html'
src = open(SRC, encoding='utf-8').read()

def patch(s, old, new, expected=1):
    n = s.count(old)
    if n != expected:
        print(f'PATCH FAILED ({n} hits, expected {expected}): {old[:80]!r}', file=sys.stderr)
        sys.exit(1)
    return s.replace(old, new, expected)

# Title + version
src = patch(src,
    '<title>Cockpit v6k7 · Valakhan ATEM Farol Club</title>',
    '<title>Cockpit v6k8 · Valakhan ATEM Farol Club</title>'
)
src = patch(src,
    '  const _COCKPIT_VERSION = "v6k7";',
    '  const _COCKPIT_VERSION = "v6k8";'
)

# Coords v8 -> v9
src = patch(src,
    "const BARROWMAZE_ROOMS_COORDS_SRC = 'maps/barrowmaze_room_coords_v8.json' + _CACHE_BUST;",
    "const BARROWMAZE_ROOMS_COORDS_SRC = 'maps/barrowmaze_room_coords_v9.json' + _CACHE_BUST;"
)

# Rooms full -> v3
src = patch(src,
    "const BARROWMAZE_ROOMS_FULL_SRC  = 'maps/barrowmaze_rooms_full.json' + _CACHE_BUST;",
    "const BARROWMAZE_ROOMS_FULL_SRC  = 'maps/barrowmaze_rooms_full_v3.json' + _CACHE_BUST;"
)

# Diagnostic overlay V6k7 -> V6k8
src = patch(src,
    "  ctx.fillText('🛠 V6k7 · Mobile=' + ((typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE) ? 'YES' : 'no'), 16, 14);",
    "  ctx.fillText('🛠 V6k8 · Mobile=' + ((typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE) ? 'YES' : 'no'), 16, 14);"
)

# Re-enable rooms_full lookup in modal AND show all_instances for Q/D
# Find the "V6k6: NO usar _roomsFullCache" block and replace it
src = patch(src,
    '  let room = null, pos = null;\n  // V6k6: NO usar _roomsFullCache (v1 tenia descripciones mal asociadas — room 1 traia texto del final del modulo).\n  // Re-extraer rooms_full con IDs reales (Q/D/sub) queda como pendiente futuro.\n  // Por ahora el modal solo muestra el ID confirmado del PDF vectorial.',
    '  let room = null, pos = null;\n  // V6k8: usar rooms_full_v3 (re-extraido del modulo PDF con IDs reales).\n  if (_roomsFullCache && _roomsFullCache.rooms) {\n    room = _roomsFullCache.rooms[rid] || _roomsFullCache.rooms[String(rid)];\n  }'
)

# Replace the "V6k6 modal message" with new content that uses room.text
src = patch(src,
    "    modal += '<b>Sala '+rid+' (PDF vector — V6k7 con table fix)</b><br><br>';\n    modal += '<span style=\"font-size:13px;color:var(--ink);\">Posición confirmada en el mapa real. <b>Re-extracción de descripción del módulo pendiente</b> — la tabla v1 estaba mal asociada (rooms 1-375 secuenciales arbitrarios, no Q/D/sub-rooms reales).</span><br><br>';\n    modal += '<span style=\"font-size:12px;color:var(--ink-dim);\">Para info detallada, consultar manualmente el módulo PDF.</span>';",
    "    modal += '<b>Sala '+rid+'</b><br><br>';\n    modal += '<span style=\"font-size:12px;color:var(--ink-dim);\">Sin descripción extraída para este ID (probable sub-zona embedded en parent room).</span>';"
)

# Find and replace the room rendering block to handle text + all_instances for Q/D
# The current code uses {summary, narrative, stats, treasure, page} — old schema.
# New schema: {text, page_book, all_instances}.
# Replace the entire `if (room) { ... }` block with new logic.
src = patch(src,
    '  if (room) {\n    // Schema nuevo (v6j) o legacy\n    const summary = room.summary || (room.desc ? room.desc.slice(0, 400) + (room.desc.length > 400 ? \'…\' : \'\') : null);\n    const narrative = room.narrative || room.desc || null;\n    const stats = room.stats || null;\n    const treasure = room.treasure || room.treasure_coins || null;\n    if (summary) modal += \'<div style="line-height:1.6;margin-bottom:12px;font-size:14px;background:rgba(255,255,255,0.03);padding:10px;border-radius:6px;border-left:3px solid #5dade2;"><b>Resumen:</b> \'+escapeHTML(summary)+\'</div>\';\n    if (treasure && treasure.length) {\n      const tArr = Array.isArray(treasure) ? treasure : [treasure];\n      modal += \'<div style="background:rgba(212,160,74,0.15);padding:10px;border-radius:6px;margin-bottom:12px;border-left:3px solid #d4a04a;"><b>💰 Tesoro:</b> \'+tArr.map(t => escapeHTML(String(t))).join(\', \')+\'</div>\';\n    }\n    if (stats) modal += \'<div style="background:rgba(231,76,60,0.12);padding:10px;border-radius:6px;margin-bottom:12px;border-left:3px solid #e74c3c;font-family:monospace;font-size:12px;line-height:1.5;"><b>⚔ Stats / Encounters detectados:</b><br>\'+escapeHTML(stats)+\'</div>\';\n    if (narrative && narrative !== summary) {\n      modal += \'<details style="margin-bottom:8px;"><summary style="cursor:pointer;font-size:12px;color:var(--ink-dim);padding:6px;">Ver narrativa completa (puede tener artefactos del extractor)</summary>\';\n      modal += \'<div style="line-height:1.6;font-size:13px;white-space:pre-line;padding:8px;background:rgba(0,0,0,0.2);border-radius:4px;">\'+escapeHTML(narrative)+\'</div>\';\n      modal += \'</details>\';\n    }\n  }',
    '  if (room) {\n    // V6k8 schema: {text, page_book, page_pdf, all_instances?}\n    const txt = room.text || \'\';\n    const pgBook = room.page_book;\n    if (pgBook) modal += \'<div style="font-size:11px;color:var(--ink-dim);margin-bottom:8px;">Página \'+pgBook+\' del módulo (PDF p.\'+room.page_pdf+\')</div>\';\n    if (txt) modal += \'<div style="line-height:1.6;font-size:14px;background:rgba(255,255,255,0.03);padding:12px;border-radius:6px;border-left:3px solid #5dade2;white-space:pre-line;">\'+escapeHTML(txt)+\'</div>\';\n    if (room.all_instances && room.all_instances.length > 1) {\n      modal += \'<details style="margin-top:12px;background:rgba(212,160,74,0.08);padding:8px;border-radius:6px;border-left:3px solid #d4a04a;"><summary style="cursor:pointer;font-weight:bold;color:#d4a04a;">⚠ Hay \'+room.all_instances.length+\' \'+rid+\' en el módulo (uno por área del dungeon). Click para ver todas.</summary>\';\n      for (let i = 0; i < room.all_instances.length; i++) {\n        const inst = room.all_instances[i];\n        const isCurrent = inst.page_book === pgBook;\n        modal += \'<div style="margin-top:10px;padding:8px;background:rgba(0,0,0,0.2);border-radius:4px;\'+(isCurrent?\'border:1px solid #d4a04a;\':\'\')+\'">\';\n        modal += \'<div style="font-size:11px;color:var(--ink-dim);margin-bottom:4px;">Página \'+inst.page_book+\' del módulo\'+(isCurrent?\' <b>(mostrada arriba)</b>\':\'\')+\'</div>\';\n        modal += \'<div style="font-size:13px;line-height:1.5;white-space:pre-line;">\'+escapeHTML(inst.text)+\'</div></div>\';\n      }\n      modal += \'</details>\';\n    }\n  }'
)

open(DST, 'w', encoding='utf-8').write(src)
print(f'OK: wrote {DST} ({len(src):,} chars)')
