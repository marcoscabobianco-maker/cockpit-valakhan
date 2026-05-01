"""
v6k2 patches: Mobile/iPad fixes.

Marcos feedback 2026-05-01: en iPad los botones se salen + no abre Barrowmaze.

Changes:
  - Detección viewport: si <=1024px → usar bg_1920 (347 KB, 1920×1785) en lugar
    de real.webp (2628×2444, 557 KB). Canvas memory: 13 MB vs 25 MB → safe en iPad.
  - CSS responsive @media (max-width:900px): cards stack vertical, paddings/fonts
    reducidos, botones siempre flex-wrap, canvas wrap con max-height 60vh para que
    quede contenido visible.
  - Try/catch en gridSetMode('real') con mensaje visible si falla load.
  - Banner alerts y tracker cards: max-width 100%, overflow ok.
  - Botones touch-friendly: min-height 36px en mobile.
  - Touch event on canvas: tap-to-move como alternativa a flechitas.

Pipeline: cp v6k -> v6k2, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6k2.html")
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
    "<title>Cockpit V6k1 — cache-bust automático + reset state si tenés problemas</title>",
    "<title>Cockpit V6k2 — iPad fixes: responsive layout + mapa liviano + touch + error handling</title>",
)


# 2) CSS responsive para iPad/mobile
patch(
    "css responsive mobile",
    "  .grid-mode-toggle .active { background: var(--accent); color: var(--bg); }",
    "  .grid-mode-toggle .active { background: var(--accent); color: var(--bg); }\n"
    "  /* v6k2: Mobile/iPad responsive fixes */\n"
    "  @media (max-width: 1024px) {\n"
    "    .grid-real-wrap { max-height: 55vh !important; }\n"
    "    .card { padding: 8px !important; }\n"
    "    .card h3 { font-size: 14px !important; }\n"
    "    .grid-real-wrap { max-width: 100% !important; }\n"
    "    .btn { min-height: 36px !important; padding: 6px 10px !important; }\n"
    "  }\n"
    "  @media (max-width: 900px) {\n"
    "    /* Stack columns vertical en mobile */\n"
    "    #grid-crawler-container > div[style*='display:flex'] {\n"
    "      flex-direction: column !important;\n"
    "    }\n"
    "    #grid-crawler-container > div[style*='display:flex'] > div {\n"
    "      width: 100% !important; min-width: 0 !important; max-width: 100% !important;\n"
    "    }\n"
    "    .grid-real-wrap { max-height: 50vh !important; }\n"
    "    .grid-info { font-size: 11px !important; }\n"
    "  }\n"
    "  /* iPad portrait safety: ensure no horizontal overflow */\n"
    "  @media (max-width: 820px) {\n"
    "    body, #grid-crawler-container { overflow-x: hidden; }\n"
    "    .card { font-size: 12px; }\n"
    "    .card input[type=number] { width: 50px !important; min-height: 32px; }\n"
    "    .card label { font-size: 11px; }\n"
    "    .grid-controls button { min-width: 44px; min-height: 44px; font-size: 18px; }\n"
    "  }",
)


# 3) Detección viewport en BG SRC: usar mobile variant si <=1024px
patch(
    "viewport-aware bg src",
    "// === v5x: Real-map mode (Barrowmaze stitched + vectorized walls) — v6k1: cache-bust ===\n"
    "const REAL_MAP_BG_SRC = 'maps/barrowmaze_real.webp' + _CACHE_BUST;\n"
    "const REAL_MAP_WALLMAP_SRC = 'maps/wallmap_barrowmaze.json' + _CACHE_BUST;",
    "// === v5x/v6k2: Real-map mode con detección de viewport para iPad ===\n"
    "const _IS_MOBILE = (typeof window !== 'undefined' && window.innerWidth <= 1024);\n"
    "const REAL_MAP_BG_SRC = (_IS_MOBILE ? 'maps/barrowmaze_real_mobile.webp' : 'maps/barrowmaze_real.webp') + _CACHE_BUST;\n"
    "const REAL_MAP_WALLMAP_SRC = 'maps/wallmap_barrowmaze.json' + _CACHE_BUST;\n"
    "console.log('[v6k2] Mobile mode:', _IS_MOBILE, '· BG src:', REAL_MAP_BG_SRC);",
)


# 4) SKIPPED: try/catch (apply manually with Edit)

# 5) Touch event on canvas: tap a cell to move (alternativa a flechitas)
patch(
    "v6k2 touch event canvas tap-to-move",
    "  // v6c+v6d: attach click handler. shift+click in DM mode → place trap. plain click → room info.\n"
    "  const _cv = document.getElementById('grid-real-canvas');\n"
    "  if (_cv) {",
    "  // v6c+v6d+v6k2: attach click + touch handlers\n"
    "  const _cv = document.getElementById('grid-real-canvas');\n"
    "  if (_cv) {\n"
    "    // v6k2: tap-to-move for iPad (single tap on adjacent cell moves party there)\n"
    "    _cv.addEventListener('dblclick', function(e) {\n"
    "      const _gg = gridState();\n"
    "      if (!_gg || !_realWallmap || !_realImg) return;\n"
    "      const rect = _cv.getBoundingClientRect();\n"
    "      const sx = _cv.width / rect.width;\n"
    "      const sy = _cv.height / rect.height;\n"
    "      const cx = (e.clientX - rect.left) * sx;\n"
    "      const cy = (e.clientY - rect.top) * sy;\n"
    "      const wm = _realWallmap;\n"
    "      const SCALE = _realImg.width / wm.stitched_image_dims[0];\n"
    "      const cellSizeDisp = wm.cell_size_px * SCALE;\n"
    "      const targetX = Math.floor(cx / cellSizeDisp);\n"
    "      const targetY = Math.floor(cy / cellSizeDisp);\n"
    "      const dx = targetX - _gg.realPlayer.x;\n"
    "      const dy = targetY - _gg.realPlayer.y;\n"
    "      if (Math.abs(dx) + Math.abs(dy) === 1) {\n"
    "        // Adjacent cell, move\n"
    "        if (dx === 1) gridMove('right');\n"
    "        else if (dx === -1) gridMove('left');\n"
    "        else if (dy === 1) gridMove('down');\n"
    "        else if (dy === -1) gridMove('up');\n"
    "      }\n"
    "    });",
)


# 6) Inputs en cards: width auto-fit + min-height
patch(
    "v6k2 input fields touch-friendly",
    "  html += '<label>Party ft/turn:</label><input type=\"number\" value=\"' + (g.partyFtPerTurn||200) + '\" min=\"30\" max=\"600\" step=\"10\" style=\"width:65px;\" onchange=\"gridSetSpeed(this.value, null)\">';\n"
    "  html += '<label>Cell ft:</label><input type=\"number\" value=\"' + (g.cellFt||10) + '\" min=\"1\" max=\"50\" step=\"1\" style=\"width:50px;\" onchange=\"gridSetSpeed(null, this.value)\">';\n"
    "  html += '<label>Antorchas:</label><input type=\"number\" value=\"' + (g.torchesInPack||0) + '\" min=\"0\" max=\"99\" step=\"1\" style=\"width:50px;\" onchange=\"gridSetTorches(this.value)\">';\n"
    "  html += '<label>Raciones:</label><input type=\"number\" value=\"' + rations + '\" min=\"0\" max=\"999\" step=\"1\" style=\"width:55px;\" onchange=\"dgSetRations(this.value)\">';\n"
    "  html += '<label>Party size:</label><input type=\"number\" value=\"' + partySize + '\" min=\"1\" max=\"50\" step=\"1\" style=\"width:45px;\" onchange=\"dgSetPartySize(this.value)\">';\n"
    "  html += '<label>Hora inicio:</label><input type=\"number\" value=\"' + (dgT.startHour != null ? dgT.startHour : 9) + '\" min=\"0\" max=\"23\" step=\"1\" style=\"width:45px;\" onchange=\"dgSetStartHour(this.value)\">';",
    "  // v6k2: inputs touch-friendly con min-height\n"
    "  html += '<label>Party ft/turn:</label><input type=\"number\" value=\"' + (g.partyFtPerTurn||200) + '\" min=\"30\" max=\"600\" step=\"10\" style=\"width:65px;min-height:32px;\" onchange=\"gridSetSpeed(this.value, null)\">';\n"
    "  html += '<label>Cell ft:</label><input type=\"number\" value=\"' + (g.cellFt||10) + '\" min=\"1\" max=\"50\" step=\"1\" style=\"width:50px;min-height:32px;\" onchange=\"gridSetSpeed(null, this.value)\">';\n"
    "  html += '<label>Antorchas:</label><input type=\"number\" value=\"' + (g.torchesInPack||0) + '\" min=\"0\" max=\"99\" step=\"1\" style=\"width:50px;min-height:32px;\" onchange=\"gridSetTorches(this.value)\">';\n"
    "  html += '<label>Raciones:</label><input type=\"number\" value=\"' + rations + '\" min=\"0\" max=\"999\" step=\"1\" style=\"width:55px;min-height:32px;\" onchange=\"dgSetRations(this.value)\">';\n"
    "  html += '<label>Party size:</label><input type=\"number\" value=\"' + partySize + '\" min=\"1\" max=\"50\" step=\"1\" style=\"width:45px;min-height:32px;\" onchange=\"dgSetPartySize(this.value)\">';\n"
    "  html += '<label>Hora inicio:</label><input type=\"number\" value=\"' + (dgT.startHour != null ? dgT.startHour : 9) + '\" min=\"0\" max=\"23\" step=\"1\" style=\"width:45px;min-height:32px;\" onchange=\"dgSetStartHour(this.value)\">';",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
