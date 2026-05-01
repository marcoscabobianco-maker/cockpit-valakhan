"""
v6k3 patches: iPad visibility fixes (markers grandes + layout estricto vertical).

Marcos feedback iPad Pro 12.9 (1024×1366 portrait):
  - Markers dorados invisibles (radio 5px → en CSS ~2px = invisible).
  - Botones quedan fuera de pantalla.
  - Necesita ver imágenes y descripciones bien en pantalla touch.

Changes:
  - Markers radio 12px (vs 5) si _IS_MOBILE. Border 2.5px.
  - Markers labels (números de room) más grandes (font 11px → 14px en mobile).
  - CSS: forzar layout vertical estricto en iPad portrait. Modales full-width.
  - Modal de room: max-width 100% en mobile, padding pequeño.
  - Botones: padding 10px+, min-height 44px (iOS HIG touch target).
  - Inputs touch-friendly siempre.

Pipeline: cp v6k2 -> v6k3, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6k3.html")
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
    "<title>Cockpit V6k2 — iPad fixes: responsive layout + mapa liviano + touch + error handling</title>",
    "<title>Cockpit V6k3 — iPad markers grandes + layout vertical + modales fullscreen</title>",
)


# 2) CSS: forzar todo vertical en iPad + markers visibles + modales fullscreen
patch(
    "v6k3 CSS aggressive mobile",
    "  /* iPad portrait safety: ensure no horizontal overflow */\n"
    "  @media (max-width: 820px) {\n"
    "    body, #grid-crawler-container { overflow-x: hidden; }\n"
    "    .card { font-size: 12px; }\n"
    "    .card input[type=number] { width: 50px !important; min-height: 32px; }\n"
    "    .card label { font-size: 11px; }\n"
    "    .grid-controls button { min-width: 44px; min-height: 44px; font-size: 18px; }\n"
    "  }",
    "  /* iPad portrait safety: ensure no horizontal overflow */\n"
    "  @media (max-width: 820px) {\n"
    "    body, #grid-crawler-container { overflow-x: hidden; }\n"
    "    .card { font-size: 12px; }\n"
    "    .card input[type=number] { width: 50px !important; min-height: 32px; }\n"
    "    .card label { font-size: 11px; }\n"
    "    .grid-controls button { min-width: 44px; min-height: 44px; font-size: 18px; }\n"
    "  }\n"
    "  /* v6k3: iPad Pro 12.9 portrait (1024×1366) - layout vertical estricto */\n"
    "  @media (max-width: 1100px) {\n"
    "    /* Force ALL flex containers in dungeon area to wrap and stack */\n"
    "    #grid-crawler-container * [style*='display:flex'],\n"
    "    #grid-crawler-container > div,\n"
    "    .grid-mode-toggle {\n"
    "      flex-wrap: wrap !important;\n"
    "    }\n"
    "    .grid-real-wrap {\n"
    "      max-width: 100% !important;\n"
    "      width: 100% !important;\n"
    "      max-height: 50vh !important;\n"
    "    }\n"
    "    .grid-real-canvas {\n"
    "      max-width: 100% !important;\n"
    "      height: auto !important;\n"
    "    }\n"
    "    /* Right-column cards: full width on mobile */\n"
    "    #grid-crawler-container > div > div[style*='min-width'] {\n"
    "      min-width: 0 !important;\n"
    "      max-width: 100% !important;\n"
    "      width: 100% !important;\n"
    "    }\n"
    "    /* Touch-friendly button sizes */\n"
    "    .btn {\n"
    "      min-height: 44px !important;\n"
    "      padding: 10px 14px !important;\n"
    "      font-size: 14px !important;\n"
    "    }\n"
    "    /* Cards stack with full width and proper margins */\n"
    "    .card {\n"
    "      margin-bottom: 10px !important;\n"
    "      width: 100% !important;\n"
    "      box-sizing: border-box;\n"
    "    }\n"
    "    /* Modals fullscreen on iPad */\n"
    "    #_dg-room-modal > div,\n"
    "    #_dg-bestiary-modal > div,\n"
    "    #_dg-mw-modal > div,\n"
    "    #_dg-traps-modal > div {\n"
    "      max-width: 95% !important;\n"
    "      width: 95% !important;\n"
    "      max-height: 92vh !important;\n"
    "    }\n"
    "  }",
)


# 3) Markers MUCHO más grandes en mobile + label en font visible
patch(
    "v6k3 bigger markers on mobile",
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
    "  }",
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
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
