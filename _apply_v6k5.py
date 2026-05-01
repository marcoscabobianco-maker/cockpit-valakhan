# V6k5: iOS PWA standalone fullscreen + toggle markers + titulo dinamico
#
# Cambios:
# 1. Title: "Cockpit v6k5 | Valakhan ATEM Farol Club"
# 2. CSS: --safe-bottom var, html/body 100dvh, main resta safe-bottom,
#    .mode-view padding-bottom += safe-bottom, modal detail 92dvh
# 3. JS: titulo dinamico desde _COCKPIT_VERSION
# 4. JS: variable _markersHidden + funcion toggleMarkers()
# 5. JS: respetar _markersHidden en redrawGridRealCanvas
# 6. HTML: boton flotante "Ocultar/Mostrar markers" en grid-real-wrap

import re
import sys

src_path = 'prototipo_v6k4.html'
dst_path = 'prototipo_v6k5.html'

with open(src_path, encoding='utf-8') as f:
    src = f.read()

def patch(s, old, new, expected=1):
    n = s.count(old)
    if n != expected:
        print(f'PATCH FAILED: expected {expected} hits, got {n}', file=sys.stderr)
        print(f'OLD: {old[:160]!r}', file=sys.stderr)
        sys.exit(1)
    return s.replace(old, new, expected)

# 1. Title
src = patch(src,
    '<title>Cockpit V6k4 — iPad markers HIPER-visibles (radio 22, doble border) + diagnóstico</title>',
    '<title>Cockpit v6k5 · Valakhan ATEM Farol Club</title>'
)

# 2. Add --safe-bottom var
src = patch(src,
    '  --safe-top: env(safe-area-inset-top, 0px);\n}',
    '  --safe-top: env(safe-area-inset-top, 0px);\n  --safe-bottom: env(safe-area-inset-bottom, 0px);\n}'
)

# 3. html/body: 100vh -> 100dvh
src = patch(src,
    "  font-family: 'Georgia', serif; height: 100vh; width: 100vw;",
    "  font-family: 'Georgia', serif; height: 100dvh; width: 100vw;"
)

# 4. main: respetar safe-bottom y usar dvh
src = patch(src,
    'main {\n  height: calc(100vh - 130px);\n  overflow: hidden;\n  position: relative;\n}',
    'main {\n  height: calc(100dvh - 130px - var(--safe-bottom));\n  overflow: hidden;\n  position: relative;\n}'
)

# 5. .mode-view: padding inferior += safe-bottom
src = patch(src,
    '.mode-view {\n  display: none;\n  position: absolute;\n  inset: 0;\n  overflow: auto;\n  padding: 12px;\n}',
    '.mode-view {\n  display: none;\n  position: absolute;\n  inset: 0;\n  overflow: auto;\n  padding: 12px 12px calc(12px + var(--safe-bottom)) 12px;\n}'
)

# 6. session-list & sibling: dvh + safe-bottom (2 hits esperados)
src = patch(src,
    'max-height: calc(100vh - 200px);',
    'max-height: calc(100dvh - 200px - var(--safe-bottom));',
    expected=2
)

# 7. detail-content modal: 92vh -> 92dvh
src = patch(src,
    'max-width: 700px; width: 100%; max-height: 92vh;',
    'max-width: 700px; width: 100%; max-height: 92dvh;'
)

# 8. Inyectar script de titulo dinamico justo despues del <title>
old_title = '<title>Cockpit v6k5 · Valakhan ATEM Farol Club</title>'
inject_title_js = old_title + '\n<script>\n  // V6k5: titulo dinamico (se actualiza con _COCKPIT_VERSION en cada release)\n  const _COCKPIT_VERSION = "v6k5";\n  document.title = "Cockpit " + _COCKPIT_VERSION + " · Valakhan ATEM Farol Club";\n</script>'
src = patch(src, old_title, inject_title_js)

# 9. Inyectar variable _markersHidden + toggleMarkers() despues de _roomCoordsCache decl
src = patch(src,
    'let _roomCoordsCache = null;',
    'let _roomCoordsCache = null;\n// V6k5: toggle markers ON/OFF (en iPad los markers son grandes y tapan el grid)\nlet _markersHidden = false;\nfunction toggleMarkers() {\n  _markersHidden = !_markersHidden;\n  const btn = document.getElementById(\'toggle-markers-btn\');\n  if (btn) {\n    btn.textContent = _markersHidden ? \'🜍 Mostrar markers\' : \'🜍 Ocultar markers\';\n    btn.style.background = _markersHidden ? \'rgba(60,40,20,0.85)\' : \'rgba(0,0,0,0.85)\';\n    btn.style.color = _markersHidden ? \'#a8967a\' : \'#f5b342\';\n    btn.style.borderColor = _markersHidden ? \'#a8967a\' : \'#f5b342\';\n  }\n  if (typeof redrawGridRealCanvas === \'function\') redrawGridRealCanvas();\n  if (typeof redrawArden === \'function\') { try { redrawArden(); } catch(e){} }\n}'
)

# 10. Respetar _markersHidden en el bloque de dibujo de markers
src = patch(src,
    '  // v6k4: room markers HIPER-visibles para iPad (sin shadowBlur que falla en iOS Safari)\n  let _markersDrawn = 0;\n  if (_roomCoordsCache && _roomCoordsCache.room_coords) {',
    '  // v6k4: room markers HIPER-visibles para iPad (sin shadowBlur que falla en iOS Safari)\n  // v6k5: respeta toggle _markersHidden (boton flotante en grid-real-wrap)\n  let _markersDrawn = 0;\n  if (_roomCoordsCache && _roomCoordsCache.room_coords && !_markersHidden) {'
)

# 11. Inyectar boton "Ocultar markers" dentro del grid-real-wrap (position:absolute,
#     queda fijo en la esquina del wrap, no scrollea con el canvas)
src = patch(src,
    "  html += '<div class=\"grid-real-wrap\" id=\"grid-real-wrap\">';\n  html += '<canvas id=\"grid-real-canvas\" class=\"grid-real-canvas\" width=\"'+img.width+'\" height=\"'+img.height+'\"></canvas>';",
    "  html += '<div class=\"grid-real-wrap\" id=\"grid-real-wrap\">';\n  // V6k5: boton toggle markers (iPad usability — markers grandes tapan el grid)\n  html += '<button id=\"toggle-markers-btn\" onclick=\"toggleMarkers()\" style=\"position:absolute;top:8px;right:8px;z-index:10;background:rgba(0,0,0,0.85);color:#f5b342;border:2px solid #f5b342;padding:8px 12px;border-radius:6px;font-weight:bold;cursor:pointer;min-height:44px;font-size:14px;-webkit-tap-highlight-color:rgba(245,179,66,0.3);box-shadow:0 2px 8px rgba(0,0,0,0.5);\">🜍 Ocultar markers</button>';\n  html += '<canvas id=\"grid-real-canvas\" class=\"grid-real-canvas\" width=\"'+img.width+'\" height=\"'+img.height+'\"></canvas>';"
)

with open(dst_path, 'w', encoding='utf-8') as f:
    f.write(src)

print(f'OK: wrote {dst_path} ({len(src):,} chars)')
