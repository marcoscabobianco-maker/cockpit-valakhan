"""
Apply v5v patches to prototipo_v5v.html (already cp from v5u).

Changes (decided with Marcos 2026-04-30):
  1. Replace gridRevealFrom (manhattan-only) with Bresenham raycast that blocks on walls.
     - Doors do NOT block.
     - Radius 3 (kept).
     - LoS-blocked cells stay full black (no halo).
  2. Marker color: #2e8b7d (green-teal) -> #5dade2 (celeste).
  3. gridState gets new fields: steps, partyFtPerTurn (default 200), cellFt (default 10), dmView (default false).
     With migration for pre-existing localStorage state.
  4. gridMove increments steps.
  5. renderGridCrawler:
     - DM toggle that bypasses fog when active.
     - Time/exploration counter card (steps, turns of 10min, accumulated minutes).
     - Inputs for partyFtPerTurn and cellFt (live recalc).
     - Toggle button "👤 Jugadores" / "👁 DM".
  6. New helpers: gridSetSpeed, gridResetTime, gridToggleDM.
  7. Title bumped to V5v.

Usage:
  PYTHONIOENCODING=utf-8 python _apply_v5v.py
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v5v.html")

with io.open(TARGET, "r", encoding="utf-8") as f:
    html = f.read()

original = html
patches_applied = []


def patch(label, old, new, *, count=1):
    """Apply an exact-string patch; assert it was applied `count` times."""
    global html
    n_before = html.count(old)
    if n_before != count:
        raise SystemExit(
            f"PATCH FAIL [{label}]: expected {count} matches of old string, found {n_before}.\n"
            f"--- old (first 200 chars) ---\n{old[:200]}\n"
        )
    html = html.replace(old, new)
    patches_applied.append(label)
    print(f"  [OK] {label}: replaced {count}x")


# ──────────────────────────────────────────────────────────────────────
# 1) <title>
# ──────────────────────────────────────────────────────────────────────
patch(
    "title",
    "<title>Cockpit V5u — v5u: Grid táctico (Marcos contrib)</title>",
    "<title>Cockpit V5v — v5v: LoS Bresenham + tiempo + DM toggle</title>",
)

# ──────────────────────────────────────────────────────────────────────
# 2) Color marker celeste
# ──────────────────────────────────────────────────────────────────────
patch(
    "marker color",
    ".grid-cell-player { background: #2e8b7d; box-shadow: inset 0 0 0 2px var(--bg); }",
    ".grid-cell-player { background: #5dade2; box-shadow: inset 0 0 0 2px var(--bg); }",
)

# Legend swatch also #2e8b7d
patch(
    "legend party swatch color",
    "background:#2e8b7d;border:1px solid rgba(255,255,255,0.2);vertical-align:middle;\"></span> Party",
    "background:#5dade2;border:1px solid rgba(255,255,255,0.2);vertical-align:middle;\"></span> Party",
)

# ──────────────────────────────────────────────────────────────────────
# 3) gridState: agregar steps/partyFtPerTurn/cellFt/dmView con migration
# ──────────────────────────────────────────────────────────────────────
patch(
    "gridState extension",
    "function gridState() {\n"
    "  if (!state.dungeon) return null;\n"
    "  state.dungeon.grid = state.dungeon.grid || {\n"
    "    raw: GRID_DEFAULT_MAP.slice(),\n"
    "    player: { x: 1, y: 1 },\n"
    "    seen: [gridKey(1, 1)]\n"
    "  };\n"
    "  return state.dungeon.grid;\n"
    "}",
    "function gridState() {\n"
    "  if (!state.dungeon) return null;\n"
    "  if (!state.dungeon.grid) {\n"
    "    state.dungeon.grid = {\n"
    "      raw: GRID_DEFAULT_MAP.slice(),\n"
    "      player: { x: 1, y: 1 },\n"
    "      seen: [gridKey(1, 1)],\n"
    "      steps: 0,\n"
    "      partyFtPerTurn: 200,\n"
    "      cellFt: 10,\n"
    "      dmView: false\n"
    "    };\n"
    "  } else {\n"
    "    // v5v migration for older state\n"
    "    var g = state.dungeon.grid;\n"
    "    if (g.steps == null) g.steps = 0;\n"
    "    if (g.partyFtPerTurn == null) g.partyFtPerTurn = 200;\n"
    "    if (g.cellFt == null) g.cellFt = 10;\n"
    "    if (g.dmView == null) g.dmView = false;\n"
    "  }\n"
    "  return state.dungeon.grid;\n"
    "}",
)

# ──────────────────────────────────────────────────────────────────────
# 4) gridRevealFrom: reemplazar manhattan por Bresenham + LoS
#    Insertamos una nueva función gridLineOfSight justo antes.
# ──────────────────────────────────────────────────────────────────────
patch(
    "gridRevealFrom + LoS",
    "function gridRevealFrom(x, y, radius, map, seen) {\n"
    "  const next = new Set(seen);\n"
    "  for (let dy = -radius; dy <= radius; dy++) {\n"
    "    for (let dx = -radius; dx <= radius; dx++) {\n"
    "      const nx = x + dx, ny = y + dy;\n"
    "      if (ny < 0 || ny >= map.length || nx < 0 || nx >= map[0].length) continue;\n"
    "      if (Math.abs(dx) + Math.abs(dy) <= radius) next.add(gridKey(nx, ny));\n"
    "    }\n"
    "  }\n"
    "  return next;\n"
    "}",
    "// v5v: Bresenham line-of-sight; walls block, doors do not.\n"
    "function gridLineOfSight(x0, y0, x1, y1, map) {\n"
    "  let cx = x0, cy = y0;\n"
    "  const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);\n"
    "  const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;\n"
    "  let err = dx - dy;\n"
    "  // walk strictly between origin and target; both endpoints are not tested for wall.\n"
    "  while (true) {\n"
    "    if (cx === x1 && cy === y1) return true;\n"
    "    if (!(cx === x0 && cy === y0)) {\n"
    "      const row = map[cy];\n"
    "      if (row && row[cx] === 'wall') return false;\n"
    "    }\n"
    "    const e2 = 2 * err;\n"
    "    if (e2 > -dy) { err -= dy; cx += sx; }\n"
    "    if (e2 <  dx) { err += dx; cy += sy; }\n"
    "  }\n"
    "}\n"
    "function gridRevealFrom(x, y, radius, map, seen) {\n"
    "  const next = new Set(seen);\n"
    "  for (let dy = -radius; dy <= radius; dy++) {\n"
    "    for (let dx = -radius; dx <= radius; dx++) {\n"
    "      const nx = x + dx, ny = y + dy;\n"
    "      if (ny < 0 || ny >= map.length || nx < 0 || nx >= map[0].length) continue;\n"
    "      if (Math.abs(dx) + Math.abs(dy) > radius) continue;\n"
    "      if (gridLineOfSight(x, y, nx, ny, map)) next.add(gridKey(nx, ny));\n"
    "    }\n"
    "  }\n"
    "  return next;\n"
    "}",
)

# ──────────────────────────────────────────────────────────────────────
# 5) gridMove: incrementar steps
# ──────────────────────────────────────────────────────────────────────
patch(
    "gridMove steps++",
    "  if (!gridIsWalkable(map[ny][nx])) return;\n"
    "  g.player = { x: nx, y: ny };\n"
    "  const seenSet = new Set(g.seen);",
    "  if (!gridIsWalkable(map[ny][nx])) return;\n"
    "  g.player = { x: nx, y: ny };\n"
    "  g.steps = (g.steps || 0) + 1;\n"
    "  const seenSet = new Set(g.seen);",
)

# ──────────────────────────────────────────────────────────────────────
# 6) renderGridCrawler: DM mode + counter card + speed inputs + toggle
#    a) cell loop branch on dmView
#    b) right column gets new cards before the existing Leyenda card
# ──────────────────────────────────────────────────────────────────────

# 6a) Cell rendering: branch on dmView
patch(
    "render cell loop branch dmView",
    "      const isPlayer = g.player.x === x && g.player.y === y;\n"
    "      const wasSeen = seenSet.has(k);\n"
    "      const isVisible = visibleNow.has(k);\n"
    "      let cls = 'grid-crawler-cell ';\n"
    "      if (isPlayer) cls += 'grid-cell-player';\n"
    "      else if (!wasSeen) cls += 'grid-cell-fog';\n"
    "      else {\n"
    "        if (tile === 'wall') cls += 'grid-cell-wall';\n"
    "        else if (tile === 'door') cls += 'grid-cell-door';\n"
    "        else cls += 'grid-cell-floor';\n"
    "        if (!isVisible) cls += ' grid-cell-dim';\n"
    "      }",
    "      const isPlayer = g.player.x === x && g.player.y === y;\n"
    "      const wasSeen = seenSet.has(k);\n"
    "      const isVisible = visibleNow.has(k);\n"
    "      let cls = 'grid-crawler-cell ';\n"
    "      if (g.dmView) {\n"
    "        if (isPlayer) cls += 'grid-cell-player';\n"
    "        else if (tile === 'wall') cls += 'grid-cell-wall';\n"
    "        else if (tile === 'door') cls += 'grid-cell-door';\n"
    "        else cls += 'grid-cell-floor';\n"
    "      } else if (isPlayer) {\n"
    "        cls += 'grid-cell-player';\n"
    "      } else if (!wasSeen) {\n"
    "        cls += 'grid-cell-fog';\n"
    "      } else {\n"
    "        if (tile === 'wall') cls += 'grid-cell-wall';\n"
    "        else if (tile === 'door') cls += 'grid-cell-door';\n"
    "        else cls += 'grid-cell-floor';\n"
    "        if (!isVisible) cls += ' grid-cell-dim';\n"
    "      }",
)

# 6b) grid-info: añadir tiempo
patch(
    "grid-info adds time",
    "html += '<div class=\"grid-info\">Posición: <b>(' + g.player.x + ',' + g.player.y + ')</b> · Recorrido: ' + g.seen.length + ' celdas · Radio visión: 3</div>';",
    "// v5v: time / exploration counter\n"
    "  var _ftRatio = (g.cellFt || 10) / Math.max(1, (g.partyFtPerTurn || 200));\n"
    "  var _turnsRaw = (g.steps || 0) * _ftRatio;\n"
    "  var _turns = Math.floor(_turnsRaw);\n"
    "  var _minutes = (_turnsRaw * 10).toFixed(1);\n"
    "  html += '<div class=\"grid-info\">Posición: <b>(' + g.player.x + ',' + g.player.y + ')</b> · Recorrido: ' + g.seen.length + ' celdas · Radio visión: 3 · ' +\n"
    "    (g.dmView ? '<span style=\"color:#5dade2;\">👁 Vista DM</span>' : '<span style=\"color:#aaa;\">👤 Vista jugadores</span>') + '</div>';\n"
    "  html += '<div class=\"grid-info\" style=\"margin-top:2px;\">⏱ Pasos: <b>' + (g.steps||0) + '</b> · Turnos (10min): <b>' + _turns + '</b> · Minutos acumulados: <b>' + _minutes + '</b></div>';",
)

# 6c) Right column: insert two new cards (Tiempo + Vista) BEFORE the Leyenda card.
patch(
    "insert Tiempo + Vista cards before Leyenda",
    "  // RIGHT: Editor + legend\n"
    "  html += '<div style=\"flex:1;min-width:280px;\">';\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>Leyenda</h3>';",
    "  // RIGHT: Editor + legend (v5v: + tiempo + DM toggle)\n"
    "  html += '<div style=\"flex:1;min-width:280px;\">';\n"
    "\n"
    "  // v5v: Vista DM toggle\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>Vista</h3>';\n"
    "  html += '<button class=\"btn\" onclick=\"gridToggleDM()\" style=\"font-size:14px;width:100%;\">' +\n"
    "    (g.dmView ? '👁 DM (ver todo) — click para ocultar' : '👤 Jugadores (con niebla) — click para revelar') + '</button>';\n"
    "  html += '<div style=\"font-size:11px;color:var(--ink-dim);margin-top:6px;\">' +\n"
    "    (g.dmView ? 'Modo DM: ves todo el dungeon. Marker celeste sigue visible.' : 'Modo jugadores: solo lo iluminado por LoS o lo ya recorrido.') + '</div>';\n"
    "  html += '</div>';\n"
    "\n"
    "  // v5v: Tiempo de exploración\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>⏱ Tiempo de exploración</h3>';\n"
    "  html += '<div style=\"font-size:13px;line-height:1.7;\">';\n"
    "  html += '<div>Pasos: <b>' + (g.steps||0) + '</b></div>';\n"
    "  html += '<div>Turnos (10 min): <b>' + _turns + '</b></div>';\n"
    "  html += '<div>Minutos acumulados: <b>' + _minutes + '</b></div>';\n"
    "  html += '</div>';\n"
    "  html += '<div style=\"margin-top:10px;display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:12px;\">';\n"
    "  html += '<label>Party ft/turn:</label>';\n"
    "  html += '<input type=\"number\" value=\"' + (g.partyFtPerTurn||200) + '\" min=\"30\" max=\"600\" step=\"10\" style=\"width:70px;\" onchange=\"gridSetSpeed(this.value, null)\">';\n"
    "  html += '<label>Cell ft:</label>';\n"
    "  html += '<input type=\"number\" value=\"' + (g.cellFt||10) + '\" min=\"1\" max=\"50\" step=\"1\" style=\"width:55px;\" onchange=\"gridSetSpeed(null, this.value)\">';\n"
    "  html += '</div>';\n"
    "  html += '<div style=\"font-size:11px;color:var(--ink-dim);margin-top:6px;\">ACKS exploration: party_ft_per_turn = encounter_speed × 10/3 del más lento. Default 200 ft/turn (medium).</div>';\n"
    "  html += '<div style=\"margin-top:8px;\"><button class=\"btn secondary\" onclick=\"gridResetTime()\">⟲ Reset contador</button></div>';\n"
    "  html += '</div>';\n"
    "\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>Leyenda</h3>';",
)

# ──────────────────────────────────────────────────────────────────────
# 7) New helpers: gridSetSpeed / gridResetTime / gridToggleDM
#    Insert right after gridResetMap.
# ──────────────────────────────────────────────────────────────────────
patch(
    "new helpers after gridResetMap",
    "function gridResetMap() {\n"
    "  if (!confirm('Cargar mapa default (sustituir tu mapa actual)?')) return;\n"
    "  const g = gridState(); if (!g) return;\n"
    "  g.raw = GRID_DEFAULT_MAP.slice();\n"
    "  g.player = { x: 1, y: 1 };\n"
    "  g.seen = [gridKey(1, 1)];\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}",
    "function gridResetMap() {\n"
    "  if (!confirm('Cargar mapa default (sustituir tu mapa actual)?')) return;\n"
    "  const g = gridState(); if (!g) return;\n"
    "  g.raw = GRID_DEFAULT_MAP.slice();\n"
    "  g.player = { x: 1, y: 1 };\n"
    "  g.seen = [gridKey(1, 1)];\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "// v5v helpers\n"
    "function gridSetSpeed(ftPerTurn, cellFt) {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  if (ftPerTurn !== null && ftPerTurn !== undefined && ftPerTurn !== '') {\n"
    "    var v = parseInt(ftPerTurn, 10);\n"
    "    if (v && v > 0) g.partyFtPerTurn = v;\n"
    "  }\n"
    "  if (cellFt !== null && cellFt !== undefined && cellFt !== '') {\n"
    "    var c = parseInt(cellFt, 10);\n"
    "    if (c && c > 0) g.cellFt = c;\n"
    "  }\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "function gridResetTime() {\n"
    "  if (!confirm('Resetear contador de tiempo (pasos/turnos/minutos a 0)?')) return;\n"
    "  const g = gridState(); if (!g) return;\n"
    "  g.steps = 0;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "function gridToggleDM() {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  g.dmView = !g.dmView;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}",
)


# ──────────────────────────────────────────────────────────────────────
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nApplied {len(patches_applied)} patches:")
for p in patches_applied:
    print(f"  - {p}")
print(f"\nWrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {len(original)})")
