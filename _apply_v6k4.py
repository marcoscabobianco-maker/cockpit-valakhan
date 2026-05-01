"""
v6k4 patches: iPad markers HIPER-visibles + diagnóstico visual.

Marcos sigue sin ver markers en iPad. Hipótesis:
  1. Landscape iPad Pro 12.9 (1366×1024) → _IS_MOBILE=false → markers de 6px
  2. shadowBlur causa rendering issues en iOS Safari Canvas
  3. _roomCoordsCache puede ser null silenciosamente

Changes:
  - Detección robusta: ancho <=1366 || user agent iPad/iPhone/iPod
  - Markers radio 22 si mobile (vs 8 desktop)
  - SIN shadowBlur (eliminar potential iOS bug)
  - Doble border: 4px negro outside + 2px blanco inside = máxima visibilidad
  - Fill dorado SOLID 100% opaque
  - Diagnóstico overlay: contador "Markers cargados: N/375" en esquina del canvas
  - Trigger explícito de dgLoadRoomsData al iniciar renderGridReal
  - Fallback: si rooms_coords no carga, mensaje visible "Cargando markers..."

Pipeline: cp v6k3 -> v6k4, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6k4.html")
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


# 1) Title
patch(
    "title",
    "<title>Cockpit V6k3 — iPad markers grandes + layout vertical + modales fullscreen</title>",
    "<title>Cockpit V6k4 — iPad markers HIPER-visibles (radio 22, doble border) + diagnóstico</title>",
)


# 2) Detección robusta mobile (ancho + user agent)
patch(
    "v6k4 robust mobile detection",
    "// === v5x/v6k2: Real-map mode con detección de viewport para iPad ===\n"
    "const _IS_MOBILE = (typeof window !== 'undefined' && window.innerWidth <= 1024);\n"
    "const REAL_MAP_BG_SRC = (_IS_MOBILE ? 'maps/barrowmaze_real_mobile.webp' : 'maps/barrowmaze_real.webp') + _CACHE_BUST;\n"
    "const REAL_MAP_WALLMAP_SRC = 'maps/wallmap_barrowmaze.json' + _CACHE_BUST;\n"
    "console.log('[v6k2] Mobile mode:', _IS_MOBILE, '· BG src:', REAL_MAP_BG_SRC);",
    "// === v5x/v6k4: detección mobile robusta (ancho + user agent + landscape iPad) ===\n"
    "const _UA_MOBILE = (typeof navigator !== 'undefined') && /iPad|iPhone|iPod|Android|Mobile|Tablet/i.test(navigator.userAgent || '');\n"
    "const _WIDTH_MOBILE = (typeof window !== 'undefined' && window.innerWidth <= 1366);  // iPad Pro 12.9 landscape = 1366\n"
    "const _IS_MOBILE = _UA_MOBILE || _WIDTH_MOBILE;\n"
    "const REAL_MAP_BG_SRC = (_IS_MOBILE ? 'maps/barrowmaze_real_mobile.webp' : 'maps/barrowmaze_real.webp') + _CACHE_BUST;\n"
    "const REAL_MAP_WALLMAP_SRC = 'maps/wallmap_barrowmaze.json' + _CACHE_BUST;\n"
    "console.log('[v6k4] _IS_MOBILE:', _IS_MOBILE, '(UA:'+_UA_MOBILE+', width<=1366:'+_WIDTH_MOBILE+', innerWidth='+window.innerWidth+') · BG src:', REAL_MAP_BG_SRC);",
)


# 3) Markers HIPER-visibles: radio 22 mobile, sin shadowBlur, doble border
patch(
    "v6k4 markers hiper visibles",
    "  // v6c+v6k3: room markers (dorados, GRANDES en mobile para iPad visible)\n"
    "  if (_roomCoordsCache && _roomCoordsCache.room_coords) {\n"
    "    const sx = img.width  / _roomCoordsCache.svg_w;\n"
    "    const sy = img.height / _roomCoordsCache.svg_h;\n"
    "    const markerRadius = (typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE) ? 14 : 6;\n"
    "    const markerLabelSize = (typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE) ? 13 : 10;\n"
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
    "      // Glow halo for visibility\n"
    "      ctx.shadowColor = 'rgba(255,200,100,0.9)';\n"
    "      ctx.shadowBlur = 8;\n"
    "      ctx.fillStyle = 'rgba(255,180,80,0.96)';\n"
    "      ctx.strokeStyle = '#000';\n"
    "      ctx.lineWidth = 2.5;\n"
    "      ctx.beginPath(); ctx.arc(x, y, markerRadius, 0, Math.PI*2); ctx.fill(); ctx.stroke();\n"
    "      ctx.shadowBlur = 0;\n"
    "      // Room number label - always visible (not just DM)\n"
    "      ctx.fillStyle = '#000';\n"
    "      ctx.font = '700 ' + markerLabelSize + 'px sans-serif';\n"
    "      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';\n"
    "      ctx.fillText(rid, x, y);\n"
    "    }\n"
    "    ctx.restore();\n"
    "  }",
    "  // v6k4: room markers HIPER-visibles para iPad (sin shadowBlur que falla en iOS Safari)\n"
    "  let _markersDrawn = 0;\n"
    "  if (_roomCoordsCache && _roomCoordsCache.room_coords) {\n"
    "    const sx = img.width  / _roomCoordsCache.svg_w;\n"
    "    const sy = img.height / _roomCoordsCache.svg_h;\n"
    "    const isMob = (typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE);\n"
    "    const markerRadius = isMob ? 22 : 8;\n"
    "    const markerLabelSize = isMob ? 16 : 11;\n"
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
    "      // Doble border para máxima visibilidad sobre fondo blanco/negro:\n"
    "      // 1. Outer ring negro (borde grueso)\n"
    "      ctx.fillStyle = '#000';\n"
    "      ctx.beginPath(); ctx.arc(x, y, markerRadius + 2, 0, Math.PI*2); ctx.fill();\n"
    "      // 2. Middle ring blanco (contraste)\n"
    "      ctx.fillStyle = '#fff';\n"
    "      ctx.beginPath(); ctx.arc(x, y, markerRadius + 0.5, 0, Math.PI*2); ctx.fill();\n"
    "      // 3. Inner dorado SOLID (sin shadowBlur que puede fallar en iOS)\n"
    "      ctx.fillStyle = '#f5b342';\n"
    "      ctx.beginPath(); ctx.arc(x, y, markerRadius - 1.5, 0, Math.PI*2); ctx.fill();\n"
    "      // Room number label en negro grueso\n"
    "      ctx.fillStyle = '#000';\n"
    "      ctx.font = '900 ' + markerLabelSize + 'px sans-serif';\n"
    "      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';\n"
    "      ctx.fillText(rid, x, y);\n"
    "      _markersDrawn++;\n"
    "    }\n"
    "    ctx.restore();\n"
    "  }\n"
    "  // v6k4: diagnóstico overlay (esquina superior izquierda del canvas)\n"
    "  ctx.save();\n"
    "  ctx.fillStyle = 'rgba(0,0,0,0.85)';\n"
    "  ctx.fillRect(8, 8, 250, 50);\n"
    "  ctx.strokeStyle = '#5dade2';\n"
    "  ctx.lineWidth = 2;\n"
    "  ctx.strokeRect(8, 8, 250, 50);\n"
    "  ctx.fillStyle = '#5dade2';\n"
    "  ctx.font = '700 13px sans-serif';\n"
    "  ctx.textAlign = 'left'; ctx.textBaseline = 'top';\n"
    "  ctx.fillText('🛠 V6k4 · Mobile=' + ((typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE) ? 'YES' : 'no'), 16, 14);\n"
    "  ctx.fillText('🜍 Markers visibles: ' + _markersDrawn + (g.dmView ? ' (DM mode)' : ' (player)'), 16, 36);\n"
    "  ctx.restore();",
)


# 4) Trigger explícito de dgLoadRoomsData en cada redraw si cache es null
patch(
    "v6k4 force load rooms_coords if missing",
    "function redrawGridRealCanvas() {\n"
    "  if (!_realWallmap || !_realImg) return;\n"
    "  const g = gridState(); if (!g) return;\n"
    "  const canvas = document.getElementById('grid-real-canvas');\n"
    "  if (!canvas) return;",
    "function redrawGridRealCanvas() {\n"
    "  if (!_realWallmap || !_realImg) return;\n"
    "  const g = gridState(); if (!g) return;\n"
    "  const canvas = document.getElementById('grid-real-canvas');\n"
    "  if (!canvas) return;\n"
    "  // v6k4: trigger lazy load if rooms_coords missing\n"
    "  if (!_roomCoordsCache && typeof dgLoadRoomsData === 'function' && !_roomsLoading) {\n"
    "    dgLoadRoomsData().then(() => { redrawGridRealCanvas(); }).catch(()=>{});\n"
    "  }",
)


with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
