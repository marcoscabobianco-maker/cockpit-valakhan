# V6k6: Markers reales (room_coords_v3) + iPad markers mas chicos + bloquear
# descripciones v1 mal asociadas (rooms_full viejo).
#
# Cambios:
# 1. Title + version: v6k5 -> v6k6
# 2. URL: barrowmaze_room_coords.json -> barrowmaze_room_coords_v3.json
# 3. iPad markers: radius 22 -> 12, label size 16 -> 11
# 4. Bloquear lookup en _roomsFullCache (datos v1 estaban mal asociados)
# 5. Overlay diagnostico V6k4 -> V6k6

import re
import sys

SRC = 'prototipo_v6k5.html'
DST = 'prototipo_v6k6.html'

with open(SRC, encoding='utf-8') as f:
    src = f.read()

def patch(s, old, new, expected=1):
    n = s.count(old)
    if n != expected:
        print(f'PATCH FAILED: expected {expected} hits, got {n}', file=sys.stderr)
        print(f'OLD: {old[:160]!r}', file=sys.stderr)
        sys.exit(1)
    return s.replace(old, new, expected)

# 1. Title HTML
src = patch(src,
    '<title>Cockpit v6k5 · Valakhan ATEM Farol Club</title>',
    '<title>Cockpit v6k6 · Valakhan ATEM Farol Club</title>'
)

# 2. _COCKPIT_VERSION constant
src = patch(src,
    '  const _COCKPIT_VERSION = "v6k5";',
    '  const _COCKPIT_VERSION = "v6k6";'
)

# 3. URL: room_coords -> room_coords_v3
src = patch(src,
    "const BARROWMAZE_ROOMS_COORDS_SRC = 'maps/barrowmaze_room_coords.json' + _CACHE_BUST;",
    "const BARROWMAZE_ROOMS_COORDS_SRC = 'maps/barrowmaze_room_coords_v3.json' + _CACHE_BUST;"
)

# 4. iPad markers MAS CHICOS para no tapar el grid
src = patch(src,
    '    const markerRadius = isMob ? 22 : 8;\n    const markerLabelSize = isMob ? 16 : 11;',
    '    // V6k6: markers iPad reducidos (de 22 a 12) — antes tapaban el grid del mapa\n    const markerRadius = isMob ? 12 : 8;\n    const markerLabelSize = isMob ? 11 : 11;'
)

# 5. Reducir borders de markers para que no se vean tan masivos en mobile
# V6k4 usa: outer ring (+2 radius), middle white (+0.5), inner gold (-1.5)
# Para markers chicos, los borders proporcionalmente quedan demasiado gruesos.
# Cambio: outer +1.5, middle +0.5, inner -1
src = patch(src,
    '      // Doble border para máxima visibilidad sobre fondo blanco/negro:\n      // 1. Outer ring negro (borde grueso)\n      ctx.fillStyle = \'#000\';\n      ctx.beginPath(); ctx.arc(x, y, markerRadius + 2, 0, Math.PI*2); ctx.fill();\n      // 2. Middle ring blanco (contraste)\n      ctx.fillStyle = \'#fff\';\n      ctx.beginPath(); ctx.arc(x, y, markerRadius + 0.5, 0, Math.PI*2); ctx.fill();\n      // 3. Inner dorado SOLID (sin shadowBlur que puede fallar en iOS)\n      ctx.fillStyle = \'#f5b342\';\n      ctx.beginPath(); ctx.arc(x, y, markerRadius - 1.5, 0, Math.PI*2); ctx.fill();',
    '      // V6k6: borders proporcionales al tamaño (markers chicos no necesitan borde tan grueso)\n      const borderOuter = isMob ? 1.5 : 2;\n      const borderMid = 0.5;\n      const innerInset = isMob ? 0.5 : 1.5;\n      ctx.fillStyle = \'#000\';\n      ctx.beginPath(); ctx.arc(x, y, markerRadius + borderOuter, 0, Math.PI*2); ctx.fill();\n      ctx.fillStyle = \'#fff\';\n      ctx.beginPath(); ctx.arc(x, y, markerRadius + borderMid, 0, Math.PI*2); ctx.fill();\n      ctx.fillStyle = \'#f5b342\';\n      ctx.beginPath(); ctx.arc(x, y, markerRadius - innerInset, 0, Math.PI*2); ctx.fill();'
)

# 6. Bloquear lookup en _roomsFullCache (datos v1 mal asociados — room 1 tenia
#    texto de Nergal's Beckoning del final del modulo, etc.)
src = patch(src,
    '  let room = null, pos = null;\n  if (_roomsFullCache) {\n    const rooms = _roomsFullCache.rooms || _roomsFullCache;\n    room = rooms[rid] || rooms[String(rid)];\n  }',
    '  let room = null, pos = null;\n  // V6k6: NO usar _roomsFullCache (v1 tenia descripciones mal asociadas — room 1 traia texto del final del modulo).\n  // Re-extraer rooms_full con IDs reales (Q/D/sub) queda como pendiente futuro.\n  // Por ahora el modal solo muestra el ID confirmado del PDF vectorial.'
)

# 7. Customizar el mensaje "sin descripcion" para V6k6 (mas honest, sin conditional para evitar bugs de quoting)
src = patch(src,
    "    modal += '<b>Sala '+rid+' detectada en el mapa</b>, pero <b>sin descripción en el módulo extraído</b>.<br><br>';\n    modal += '<span style=\"font-size:12px;color:var(--ink-dim);\">Causas posibles: (1) sub-room (74A, 74B…) cuya descripción está en la sala padre; (2) cross-reference numérica en margen del PDF; (3) sala no keyed en este corte del módulo.</span>';",
    "    modal += '<b>Sala '+rid+' (PDF vector — V6k6)</b><br><br>';\n    modal += '<span style=\"font-size:13px;color:var(--ink);\">Posición confirmada en el mapa real. <b>Re-extracción de descripción del módulo pendiente</b> — la tabla v1 estaba mal asociada (rooms 1-375 secuenciales arbitrarios, no Q/D/sub-rooms reales).</span><br><br>';\n    modal += '<span style=\"font-size:12px;color:var(--ink-dim);\">Para info detallada, consultar manualmente el módulo PDF.</span>';"
)

# 8. Overlay diagnostico: V6k4 -> V6k6
src = patch(src,
    "  ctx.fillText('🛠 V6k4 · Mobile=' + ((typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE) ? 'YES' : 'no'), 16, 14);",
    "  ctx.fillText('🛠 V6k6 · Mobile=' + ((typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE) ? 'YES' : 'no'), 16, 14);"
)

# 9. Bump comentario V6k4 en el bloque de markers a V6k6 (cosmetic but accurate)
src = patch(src,
    '  // v6k4: room markers HIPER-visibles para iPad (sin shadowBlur que falla en iOS Safari)\n  // v6k5: respeta toggle _markersHidden (boton flotante en grid-real-wrap)\n  let _markersDrawn = 0;',
    '  // v6k4: room markers HIPER-visibles para iPad\n  // v6k5: respeta toggle _markersHidden (boton flotante en grid-real-wrap)\n  // v6k6: usa room_coords_v3 (IDs reales del PDF vectorial), markers iPad mas chicos\n  let _markersDrawn = 0;'
)

with open(DST, 'w', encoding='utf-8') as f:
    f.write(src)

print(f'OK: wrote {DST} ({len(src):,} chars)')
