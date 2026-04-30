"""
Apply v5w patches to prototipo_v5w.html (already cp from v5v).

Decisions confirmed by Marcos 2026-04-30:
  - Rest: ACKS RAW = 5 turnos actividad -> 1 turno rest. -1/-1 hasta descansar.
  - Wandering: cada 2 turnos, 1d6=1, sin slider (por ahora).
  - Noise modifier: boton "Ruido +1" suma al threshold del proximo wandering check.
  - Antorchas: tracking de inventario (torchesInPack).
  - Alertas: banner sticky arriba del grid (no popup).
  - Party como rectangulo: head (player) + tail (cell anterior). 1x2 cells = 10x20 ft.
  - Groundwork (state placeholders, NO UI todavia): formation, lightBearer, traps.

Pipeline:
  cp v5v -> v5w
  this script
  validate JS sintaxis
  cp to deploy folder
  wrangler deploy
  git commit + push

Usage: PYTHONIOENCODING=utf-8 python _apply_v5w.py
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v5w.html")

with io.open(TARGET, "r", encoding="utf-8") as f:
    html = f.read()

original_len = len(html)
patches = []


def patch(label, old, new, *, count=1):
    global html
    n = html.count(old)
    if n != count:
        raise SystemExit(f"PATCH FAIL [{label}]: expected {count} matches, found {n}.\n--- old (first 240 chars) ---\n{old[:240]}\n")
    html = html.replace(old, new)
    patches.append(label)
    print(f"  [OK] {label}: replaced {count}x")


# ── 1) title ──
patch(
    "title",
    "<title>Cockpit V5v — v5v: LoS Bresenham + tiempo + DM toggle</title>",
    "<title>Cockpit V5w — v5w: Tracker dungeon + party rect + alertas</title>",
)

# ── 2) CSS: tail color (celeste oscuro) ──
patch(
    "css tail color",
    ".grid-cell-player { background: #5dade2; box-shadow: inset 0 0 0 2px var(--bg); }",
    ".grid-cell-player { background: #5dade2; box-shadow: inset 0 0 0 2px var(--bg); }\n"
    "  .grid-cell-player-tail { background: #2980b9; box-shadow: inset 0 0 0 2px var(--bg); opacity: 0.75; }",
)

# ── 3) gridState: extender con tail, partyShape, torchesInPack, formation/lightBearer (groundwork) ──
patch(
    "gridState extension v5w",
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
    "function gridState() {\n"
    "  if (!state.dungeon) return null;\n"
    "  if (!state.dungeon.grid) {\n"
    "    state.dungeon.grid = {\n"
    "      raw: GRID_DEFAULT_MAP.slice(),\n"
    "      player: { x: 1, y: 1 },\n"
    "      tail: { x: 1, y: 1 },\n"
    "      seen: [gridKey(1, 1)],\n"
    "      steps: 0,\n"
    "      partyFtPerTurn: 200,\n"
    "      cellFt: 10,\n"
    "      dmView: false,\n"
    "      // v5w party shape (groundwork: 1x2 cells = 10x20 ft)\n"
    "      partyShape: { w: 1, h: 2 },\n"
    "      torchesInPack: 6,\n"
    "      // v5w groundwork (no UI yet): formation = PC ids front-to-back, lightBearer = PC id, traps = [{x,y,detected,triggered,desc,dc}]\n"
    "      formation: [],\n"
    "      lightBearer: null,\n"
    "      traps: []\n"
    "    };\n"
    "  } else {\n"
    "    var g = state.dungeon.grid;\n"
    "    // v5v migration\n"
    "    if (g.steps == null) g.steps = 0;\n"
    "    if (g.partyFtPerTurn == null) g.partyFtPerTurn = 200;\n"
    "    if (g.cellFt == null) g.cellFt = 10;\n"
    "    if (g.dmView == null) g.dmView = false;\n"
    "    // v5w migration\n"
    "    if (g.tail == null) g.tail = { x: g.player.x, y: g.player.y };\n"
    "    if (g.partyShape == null) g.partyShape = { w: 1, h: 2 };\n"
    "    if (g.torchesInPack == null) g.torchesInPack = 6;\n"
    "    if (g.formation == null) g.formation = [];\n"
    "    if (g.lightBearer == null) g.lightBearer = null;\n"
    "    if (g.traps == null) g.traps = [];\n"
    "  }\n"
    "  return state.dungeon.grid;\n"
    "}",
)

# ── 4) state.dungeon en loadDungeon: agregar torchTurnsMax, wanderingNoise, restTimer ──
patch(
    "state.dungeon init w/ rest+noise+max",
    "    state.dungeon = {\n"
    "      id, currentRoom: dgs[id].startRoom,\n"
    "      fogOfWar: { [dgs[id].startRoom]: 'explored' },\n"
    "      turns: 0, torchTurnsLeft: 6, wanderingTimer: 2\n"
    "    };",
    "    state.dungeon = {\n"
    "      id, currentRoom: dgs[id].startRoom,\n"
    "      fogOfWar: { [dgs[id].startRoom]: 'explored' },\n"
    "      turns: 0,\n"
    "      torchTurnsLeft: 6, torchTurnsMax: 6,\n"
    "      wanderingTimer: 2, wanderingNoise: 0,\n"
    "      restTimer: 5\n"
    "    };",
)

# ── 5) dgAdvance: decrementar restTimer + alertas extras ──
patch(
    "dgAdvance + rest+noise",
    "function dgAdvance() {\n"
    "  if (!state.dungeon) return;\n"
    "  state.dungeon.turns++;\n"
    "  state.dungeon.torchTurnsLeft = Math.max(0, state.dungeon.torchTurnsLeft - 1);\n"
    "  state.dungeon.wanderingTimer = Math.max(0, state.dungeon.wanderingTimer - 1);\n"
    "  logEvent('Dungeon turn +1 (now '+state.dungeon.turns+'). Torch: '+state.dungeon.torchTurnsLeft);\n"
    "  if (state.dungeon.wanderingTimer === 0) {\n"
    "    logEvent('⚠ Wandering check due!');\n"
    "    state.dungeon.wanderingTimer = 2;\n"
    "  }\n"
    "  if (state.dungeon.torchTurnsLeft === 0) {\n"
    "    logEvent('⚠ Antorcha agotada — encender otra (-4 ataques sin luz)');\n"
    "  }\n"
    "  saveState(); renderDungeon(); renderEventLog();\n"
    "}",
    "function dgAdvance() {\n"
    "  if (!state.dungeon) return;\n"
    "  state.dungeon.turns++;\n"
    "  state.dungeon.torchTurnsLeft = Math.max(0, state.dungeon.torchTurnsLeft - 1);\n"
    "  state.dungeon.wanderingTimer = Math.max(0, state.dungeon.wanderingTimer - 1);\n"
    "  // v5w migrations & restTimer decrement\n"
    "  if (state.dungeon.torchTurnsMax == null) state.dungeon.torchTurnsMax = 6;\n"
    "  if (state.dungeon.wanderingNoise == null) state.dungeon.wanderingNoise = 0;\n"
    "  if (state.dungeon.restTimer == null) state.dungeon.restTimer = 5;\n"
    "  state.dungeon.restTimer = Math.max(0, state.dungeon.restTimer - 1);\n"
    "  logEvent('Dungeon turn +1 (now '+state.dungeon.turns+'). Torch: '+state.dungeon.torchTurnsLeft);\n"
    "  if (state.dungeon.wanderingTimer === 0) {\n"
    "    logEvent('⚠ Wandering check due!');\n"
    "    // do not auto-reset; reset happens after dgWanderingCheck so the alert stays sticky\n"
    "  }\n"
    "  if (state.dungeon.torchTurnsLeft === 0) {\n"
    "    logEvent('⚠ Antorcha agotada — encender otra (-4 ataques sin luz)');\n"
    "  }\n"
    "  if (state.dungeon.restTimer === 0) {\n"
    "    logEvent('⚠ 5 turnos sin descanso — penalty -1 to-hit / -1 dmg hasta que descansen');\n"
    "  }\n"
    "  saveState(); renderDungeon(); renderEventLog();\n"
    "  // v5w: re-render grid panel so sticky banner updates immediately\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}",
)

# ── 6) dgRest: reset restTimer ──
patch(
    "dgRest reset restTimer",
    "function dgRest() { dgAdvance(); logEvent('😴 Rest 1 turn. Recuperar fatiga.'); renderEventLog(); }",
    "function dgRest() {\n"
    "  if (!state.dungeon) return;\n"
    "  dgAdvance();\n"
    "  state.dungeon.restTimer = 5;  // v5w: reset rest counter\n"
    "  logEvent('😴 Rest 1 turn. Recuperar fatiga. Reset rest timer a 5.');\n"
    "  saveState(); renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}",
)

# ── 7) dgWanderingCheck: usar noise modifier ──
patch(
    "dgWanderingCheck w/ noise",
    "function dgWanderingCheck() {\n"
    "  if (!state.dungeon) return;\n"
    "  const r = rollDice('1d6');\n"
    "  if (r.total === 1) {\n"
    "    const beasts = Object.entries(ACKS.monsters || {});\n"
    "    if (beasts.length) {\n"
    "      const [name, m] = beasts[Math.floor(Math.random()*beasts.length)];\n"
    "      logEvent('🜍 Wandering monster: '+name+' (HD '+(m.hd||'?')+', AC '+(m.ac||'?')+')', '1d6=1');\n"
    "    }\n"
    "  } else {\n"
    "    logEvent('Wandering check: nada', '1d6='+r.total);\n"
    "  }\n"
    "  saveState(); renderEventLog();\n"
    "}",
    "function dgWanderingCheck() {\n"
    "  if (!state.dungeon) return;\n"
    "  const noise = state.dungeon.wanderingNoise || 0;\n"
    "  const threshold = 1 + noise; // base 1d6=1, +noise per acumulado\n"
    "  const r = rollDice('1d6');\n"
    "  const noiseStr = noise > 0 ? ' (ruido +'+noise+', umbral 1d6≤'+threshold+')' : '';\n"
    "  if (r.total <= threshold) {\n"
    "    const beasts = Object.entries(ACKS.monsters || {});\n"
    "    if (beasts.length) {\n"
    "      const [name, m] = beasts[Math.floor(Math.random()*beasts.length)];\n"
    "      logEvent('🜍 Wandering monster: '+name+' (HD '+(m.hd||'?')+', AC '+(m.ac||'?')+')', '1d6='+r.total+noiseStr);\n"
    "    }\n"
    "  } else {\n"
    "    logEvent('Wandering check: nada', '1d6='+r.total+noiseStr);\n"
    "  }\n"
    "  // v5w: tras tirar, reset noise + reset wanderingTimer a 2\n"
    "  state.dungeon.wanderingNoise = 0;\n"
    "  state.dungeon.wanderingTimer = 2;\n"
    "  saveState(); renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}",
)

# ── 8) gridMove: tail follow + auto-advance turn boundary ──
patch(
    "gridMove tail+autoadvance",
    "  if (!gridIsWalkable(map[ny][nx])) return;\n"
    "  g.player = { x: nx, y: ny };\n"
    "  g.steps = (g.steps || 0) + 1;\n"
    "  const seenSet = new Set(g.seen);",
    "  if (!gridIsWalkable(map[ny][nx])) return;\n"
    "  // v5w: tail follows leader to form 1x2 party rectangle\n"
    "  g.tail = { x: g.player.x, y: g.player.y };\n"
    "  g.player = { x: nx, y: ny };\n"
    "  g.steps = (g.steps || 0) + 1;\n"
    "  // v5w: auto-advance dgAdvance() when crossing turn boundaries\n"
    "  if (state.dungeon && typeof dgAdvance === 'function') {\n"
    "    var _tps = (g.cellFt || 10) / Math.max(1, (g.partyFtPerTurn || 200));\n"
    "    var _crossed = Math.floor(g.steps * _tps) - Math.floor((g.steps - 1) * _tps);\n"
    "    for (var _i = 0; _i < _crossed; _i++) dgAdvance();\n"
    "  }\n"
    "  const seenSet = new Set(g.seen);",
)

# ── 9) Render cell loop: incluir tail ──
patch(
    "render cell loop tail",
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
    "      const isPlayer = g.player.x === x && g.player.y === y;\n"
    "      const isTail = !isPlayer && g.tail && g.tail.x === x && g.tail.y === y;\n"
    "      const wasSeen = seenSet.has(k);\n"
    "      const isVisible = visibleNow.has(k);\n"
    "      let cls = 'grid-crawler-cell ';\n"
    "      if (g.dmView) {\n"
    "        if (isPlayer) cls += 'grid-cell-player';\n"
    "        else if (isTail) cls += 'grid-cell-player-tail';\n"
    "        else if (tile === 'wall') cls += 'grid-cell-wall';\n"
    "        else if (tile === 'door') cls += 'grid-cell-door';\n"
    "        else cls += 'grid-cell-floor';\n"
    "      } else if (isPlayer) {\n"
    "        cls += 'grid-cell-player';\n"
    "      } else if (isTail) {\n"
    "        cls += 'grid-cell-player-tail';\n"
    "      } else if (!wasSeen) {\n"
    "        cls += 'grid-cell-fog';\n"
    "      } else {\n"
    "        if (tile === 'wall') cls += 'grid-cell-wall';\n"
    "        else if (tile === 'door') cls += 'grid-cell-door';\n"
    "        else cls += 'grid-cell-floor';\n"
    "        if (!isVisible) cls += ' grid-cell-dim';\n"
    "      }",
)

# ── 10) Reemplazar renderGridCrawler grid-info + tarjetas right-column por v5w (banner + tracker) ──
patch(
    "render grid-info v5w",
    "// v5v: time / exploration counter\n"
    "  var _ftRatio = (g.cellFt || 10) / Math.max(1, (g.partyFtPerTurn || 200));\n"
    "  var _turnsRaw = (g.steps || 0) * _ftRatio;\n"
    "  var _turns = Math.floor(_turnsRaw);\n"
    "  var _minutes = (_turnsRaw * 10).toFixed(1);\n"
    "  html += '<div class=\"grid-info\">Posición: <b>(' + g.player.x + ',' + g.player.y + ')</b> · Recorrido: ' + g.seen.length + ' celdas · Radio visión: 3 · ' +\n"
    "    (g.dmView ? '<span style=\"color:#5dade2;\">👁 Vista DM</span>' : '<span style=\"color:#aaa;\">👤 Vista jugadores</span>') + '</div>';\n"
    "  html += '<div class=\"grid-info\" style=\"margin-top:2px;\">⏱ Pasos: <b>' + (g.steps||0) + '</b> · Turnos (10min): <b>' + _turns + '</b> · Minutos acumulados: <b>' + _minutes + '</b></div>';",
    "// v5v/v5w: time / exploration counter (vars used both in grid-info and tracker card)\n"
    "  var _ftRatio = (g.cellFt || 10) / Math.max(1, (g.partyFtPerTurn || 200));\n"
    "  var _turnsRaw = (g.steps || 0) * _ftRatio;\n"
    "  var _turns = Math.floor(_turnsRaw);\n"
    "  var _minutes = (_turnsRaw * 10).toFixed(1);\n"
    "  html += '<div class=\"grid-info\">Posición: <b>(' + g.player.x + ',' + g.player.y + ')</b> · Recorrido: ' + g.seen.length + ' celdas · Radio visión: 3 · ' +\n"
    "    (g.dmView ? '<span style=\"color:#5dade2;\">👁 Vista DM</span>' : '<span style=\"color:#aaa;\">👤 Vista jugadores</span>') + '</div>';\n"
    "  html += '<div class=\"grid-info\" style=\"margin-top:2px;\">⏱ Pasos: <b>' + (g.steps||0) + '</b> · Turnos (10min): <b>' + _turns + '</b> · Minutos acumulados: <b>' + _minutes + '</b></div>';",
)

# Inject alerts banner BEFORE the flex container (top of map)
patch(
    "render alerts banner",
    "  let html = '<div style=\"display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start;\">';\n"
    "  // LEFT: Map\n",
    "  // v5w: alerts banner (sticky above map)\n"
    "  let html = '';\n"
    "  if (state.dungeon) {\n"
    "    var dgB = state.dungeon;\n"
    "    var alerts = [];\n"
    "    if (dgB.restTimer === 0) alerts.push({color:'#e67e22', emoji:'😴', msg:'Rest DUE — 5 turnos sin descanso. Penalty -1 to-hit / -1 dmg hasta descansar.', action:'dgRest()', actionLabel:'Descansar'});\n"
    "    if (dgB.wanderingTimer === 0) alerts.push({color:'#c0392b', emoji:'👹', msg:'Wandering check DUE — tirar 1d6' + (dgB.wanderingNoise>0 ? ' (ruido +'+dgB.wanderingNoise+', umbral ≤'+(1+dgB.wanderingNoise)+')' : ''), action:'dgWanderingCheck()', actionLabel:'Tirar 1d6'});\n"
    "    if (dgB.torchTurnsLeft === 0) alerts.push({color:'#1a1410', emoji:'🌑', msg:'Antorcha AGOTADA. Combate -4 to-hit. Encender otra de mochila.', action:'gridLightTorch()', actionLabel:'Encender'});\n"
    "    else if (dgB.torchTurnsLeft <= 2) alerts.push({color:'#d4a04a', emoji:'🔥', msg:'Antorcha en últimos '+dgB.torchTurnsLeft+' turnos — preparar otra.', action:null});\n"
    "    if (alerts.length) {\n"
    "      html += '<div style=\"display:flex;flex-direction:column;gap:6px;margin-bottom:10px;\">';\n"
    "      alerts.forEach(function(a){\n"
    "        html += '<div style=\"background:'+a.color+';color:#fff;padding:8px 12px;border-radius:4px;font-weight:600;display:flex;align-items:center;gap:8px;border:1px solid rgba(255,255,255,0.15);\">';\n"
    "        html += '<span style=\"font-size:18px;\">'+a.emoji+'</span>';\n"
    "        html += '<span style=\"flex:1;\">'+a.msg+'</span>';\n"
    "        if (a.action) html += '<button class=\"btn\" onclick=\"'+a.action+'\" style=\"min-width:auto;\">'+a.actionLabel+'</button>';\n"
    "        html += '</div>';\n"
    "      });\n"
    "      html += '</div>';\n"
    "    }\n"
    "  }\n"
    "  html += '<div style=\"display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start;\">';\n"
    "  // LEFT: Map\n",
)

# Replace the v5v "Tiempo de exploración" card by the v5w full Tracker card
patch(
    "tracker card v5w replaces v5v time card",
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
    "  html += '</div>';",
    "  // v5w: Tracker dungeon completo (tiempo + antorcha + wandering + rest)\n"
    "  var dgT = state.dungeon || {};\n"
    "  var torchMax = dgT.torchTurnsMax || 6;\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>⏱ Tracker de exploración</h3>';\n"
    "  html += '<div style=\"display:grid;grid-template-columns:auto 1fr;gap:4px 12px;font-size:13px;\">';\n"
    "  html += '<span>Pasos:</span><b>' + (g.steps||0) + '</b>';\n"
    "  html += '<span>Turnos (10 min):</span><b>' + _turns + '</b>';\n"
    "  html += '<span>Minutos acumulados:</span><b>' + _minutes + '</b>';\n"
    "  html += '</div>';\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:10px 0;\">';\n"
    "  html += '<div style=\"font-size:13px;line-height:1.8;\">';\n"
    "  html += '<div>🔥 Antorcha: <b>' + (dgT.torchTurnsLeft||0) + ' / ' + torchMax + '</b> turns &nbsp;·&nbsp; Mochila: <b>' + (g.torchesInPack||0) + '</b> antorchas</div>';\n"
    "  html += '<div>👹 Wandering: <b>' + (dgT.wanderingTimer||0) + ' / 2</b> turns &nbsp;·&nbsp; Ruido al check: <b>+' + (dgT.wanderingNoise||0) + '</b> (umbral 1d6 ≤ ' + (1 + (dgT.wanderingNoise||0)) + ')</div>';\n"
    "  html += '<div>😴 Descanso: <b>' + (dgT.restTimer != null ? dgT.restTimer : 5) + ' / 5</b> turns hasta rest required</div>';\n"
    "  html += '</div>';\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:10px 0;\">';\n"
    "  html += '<div style=\"display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:12px;\">';\n"
    "  html += '<label>Party ft/turn:</label>';\n"
    "  html += '<input type=\"number\" value=\"' + (g.partyFtPerTurn||200) + '\" min=\"30\" max=\"600\" step=\"10\" style=\"width:70px;\" onchange=\"gridSetSpeed(this.value, null)\">';\n"
    "  html += '<label>Cell ft:</label>';\n"
    "  html += '<input type=\"number\" value=\"' + (g.cellFt||10) + '\" min=\"1\" max=\"50\" step=\"1\" style=\"width:55px;\" onchange=\"gridSetSpeed(null, this.value)\">';\n"
    "  html += '<label>Antorchas mochila:</label>';\n"
    "  html += '<input type=\"number\" value=\"' + (g.torchesInPack||0) + '\" min=\"0\" max=\"99\" step=\"1\" style=\"width:55px;\" onchange=\"gridSetTorches(this.value)\">';\n"
    "  html += '</div>';\n"
    "  html += '<div style=\"font-size:11px;color:var(--ink-dim);margin-top:6px;\">ACKS exploration: party_ft_per_turn = encounter_speed × 10/3 del más lento. Default 200 ft/turn (medium).</div>';\n"
    "  html += '<div style=\"margin-top:10px;display:grid;grid-template-columns:repeat(2,1fr);gap:6px;\">';\n"
    "  html += '<button class=\"btn\" onclick=\"gridAddTurn()\">+1 Turno (actividad)</button>';\n"
    "  html += '<button class=\"btn\" onclick=\"dgRest()\">😴 Descansar 1 turno</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridLightTorch()\">🔥 Encender antorcha</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgWanderingCheck()\">🎲 Wandering check</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridAddNoise()\">🔊 Ruido +1</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetTime()\">⟲ Reset pasos</button>';\n"
    "  html += '</div>';\n"
    "  html += '</div>';",
)

# Update the legend swatches: include party tail
patch(
    "legend add tail swatch",
    "html += '<span><span style=\"display:inline-block;width:14px;height:14px;background:#5dade2;border:1px solid rgba(255,255,255,0.2);vertical-align:middle;\"></span> Party</span>';",
    "html += '<span><span style=\"display:inline-block;width:14px;height:14px;background:#5dade2;border:1px solid rgba(255,255,255,0.2);vertical-align:middle;\"></span> Party (frente)</span>';\n"
    "  html += '<span><span style=\"display:inline-block;width:14px;height:14px;background:#2980b9;opacity:0.75;border:1px solid rgba(255,255,255,0.2);vertical-align:middle;\"></span> Party (cola)</span>';",
)

# ── 11) Helpers nuevos: gridLightTorch, gridAddTurn, gridAddNoise, gridSetTorches ──
patch(
    "v5w helpers",
    "function gridToggleDM() {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  g.dmView = !g.dmView;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}",
    "function gridToggleDM() {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  g.dmView = !g.dmView;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "// v5w helpers\n"
    "function gridLightTorch() {\n"
    "  if (!state.dungeon) { alert('No hay dungeon activo'); return; }\n"
    "  const g = gridState(); if (!g) return;\n"
    "  if ((g.torchesInPack || 0) <= 0) {\n"
    "    if (!confirm('No hay antorchas en mochila. ¿Encender de todos modos (override)?')) return;\n"
    "  } else {\n"
    "    g.torchesInPack -= 1;\n"
    "  }\n"
    "  if (state.dungeon.torchTurnsMax == null) state.dungeon.torchTurnsMax = 6;\n"
    "  state.dungeon.torchTurnsLeft = state.dungeon.torchTurnsMax;\n"
    "  logEvent('🔥 Nueva antorcha encendida ('+state.dungeon.torchTurnsLeft+' turns). Mochila: '+(g.torchesInPack||0)+' restantes.');\n"
    "  saveState();\n"
    "  renderEventLog();\n"
    "  renderDungeon();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "function gridAddTurn() {\n"
    "  if (!state.dungeon) { alert('No hay dungeon activo'); return; }\n"
    "  dgAdvance();\n"
    "  logEvent('+1 turno (actividad libre).');\n"
    "  renderEventLog();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "function gridAddNoise() {\n"
    "  if (!state.dungeon) { alert('No hay dungeon activo'); return; }\n"
    "  state.dungeon.wanderingNoise = (state.dungeon.wanderingNoise || 0) + 1;\n"
    "  logEvent('🔊 Ruido +1 — wandering check threshold ahora 1d6 ≤ '+ (1 + state.dungeon.wanderingNoise) +'.');\n"
    "  saveState();\n"
    "  renderEventLog();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "function gridSetTorches(n) {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  var v = parseInt(n, 10);\n"
    "  if (isNaN(v) || v < 0) v = 0;\n"
    "  g.torchesInPack = v;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
