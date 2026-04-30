"""
v5z patches: recuperar y mejorar el tracking visual de tiempo + recursos.

Decisions confirmed by Marcos 2026-04-30 after v5y:
  - El tracker estaba mas visible en v5w/v5x; v5y lo achico. Recuperar prominencia.
  - Agregar HORA DEL DIA in-game (cada turn = 10 min). Default start = 09:00 AM.
  - Descanso NOCTURNO (long rest equivalente ACKS): boton aparte del rest cada 5 turnos.
    Avanza 48 turnos (8h), incrementa dia, recupera 1d3 HP por PC, consume raciones.
  - Tracker visual con progress bars (antorcha, wandering, rest, raciones).
  - Banner alertas atardecer (17:00+) y noche (20:00+) — riesgo en Forbidden Marsh
    al volver al pueblo de Helix.
  - Inventario raciones (default 11 PCs x 7 dias = 77 raciones).

Pipeline: cp v5y -> v5z, this script, validate, deploy.
Usage: PYTHONIOENCODING=utf-8 python _apply_v5z.py
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v5z.html")
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
    "<title>Cockpit V5y — v5y: Grid Barrowmaze focus (DM prominent + perf)</title>",
    "<title>Cockpit V5z — v5z: Tiempo, hora del dia, raciones, descanso nocturno</title>",
)

# ── 2) State init: agregar dayInDungeon, startHour, rations, partySize ──
patch(
    "state.dungeon init time+rations",
    "    state.dungeon = {\n"
    "      id, currentRoom: dgs[id].startRoom,\n"
    "      fogOfWar: { [dgs[id].startRoom]: 'explored' },\n"
    "      turns: 0,\n"
    "      torchTurnsLeft: 6, torchTurnsMax: 6,\n"
    "      wanderingTimer: 2, wanderingNoise: 0,\n"
    "      restTimer: 5\n"
    "    };",
    "    state.dungeon = {\n"
    "      id, currentRoom: dgs[id].startRoom,\n"
    "      fogOfWar: { [dgs[id].startRoom]: 'explored' },\n"
    "      turns: 0,\n"
    "      torchTurnsLeft: 6, torchTurnsMax: 6,\n"
    "      wanderingTimer: 2, wanderingNoise: 0,\n"
    "      restTimer: 5,\n"
    "      // v5z: in-game time + rations\n"
    "      dayInDungeon: 1,\n"
    "      startHour: 9,            // 9 AM default; first turn marks 09:10\n"
    "      partySize: 11,           // novatos_ravenloft\n"
    "      rationsTotal: 77         // 11 PCs x 7 days default\n"
    "    };",
)

# ── 3) dgAdvance: migrar campos nuevos ──
patch(
    "dgAdvance v5z migrations",
    "  // v5w migrations & restTimer decrement\n"
    "  if (state.dungeon.torchTurnsMax == null) state.dungeon.torchTurnsMax = 6;\n"
    "  if (state.dungeon.wanderingNoise == null) state.dungeon.wanderingNoise = 0;\n"
    "  if (state.dungeon.restTimer == null) state.dungeon.restTimer = 5;\n"
    "  state.dungeon.restTimer = Math.max(0, state.dungeon.restTimer - 1);",
    "  // v5w migrations & restTimer decrement\n"
    "  if (state.dungeon.torchTurnsMax == null) state.dungeon.torchTurnsMax = 6;\n"
    "  if (state.dungeon.wanderingNoise == null) state.dungeon.wanderingNoise = 0;\n"
    "  if (state.dungeon.restTimer == null) state.dungeon.restTimer = 5;\n"
    "  // v5z migrations\n"
    "  if (state.dungeon.dayInDungeon == null) state.dungeon.dayInDungeon = 1;\n"
    "  if (state.dungeon.startHour == null) state.dungeon.startHour = 9;\n"
    "  if (state.dungeon.partySize == null) state.dungeon.partySize = 11;\n"
    "  if (state.dungeon.rationsTotal == null) state.dungeon.rationsTotal = 77;\n"
    "  state.dungeon.restTimer = Math.max(0, state.dungeon.restTimer - 1);",
)

# ── 4) Helpers: time, progress bar, long rest. Insertar después de gridSetTorches ──
patch(
    "v5z helpers (time / progress / longRest)",
    "function gridSetTorches(n) {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  var v = parseInt(n, 10);\n"
    "  if (isNaN(v) || v < 0) v = 0;\n"
    "  g.torchesInPack = v;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}",
    "function gridSetTorches(n) {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  var v = parseInt(n, 10);\n"
    "  if (isNaN(v) || v < 0) v = 0;\n"
    "  g.torchesInPack = v;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "\n"
    "// === v5z: in-game time + long rest + rations ===\n"
    "function dgGetTimeInfo() {\n"
    "  const dg = state.dungeon || {};\n"
    "  const totalMin = (dg.turns || 0) * 10;\n"
    "  const startMin = (dg.startHour != null ? dg.startHour : 9) * 60;\n"
    "  const minIntoEpoch = startMin + totalMin;\n"
    "  const dayOffset = Math.floor(minIntoEpoch / (24*60));\n"
    "  const day = (dg.dayInDungeon || 1) + dayOffset;\n"
    "  const minToday = ((minIntoEpoch % (24*60)) + (24*60)) % (24*60);\n"
    "  const hour = Math.floor(minToday / 60);\n"
    "  const minute = minToday % 60;\n"
    "  let period, icon, color;\n"
    "  if (hour >= 5 && hour < 12) { period = 'mañana'; icon = '☀'; color = '#f1c40f'; }\n"
    "  else if (hour >= 12 && hour < 17) { period = 'tarde'; icon = '🌤'; color = '#e8c49a'; }\n"
    "  else if (hour >= 17 && hour < 20) { period = 'atardecer'; icon = '🌅'; color = '#e67e22'; }\n"
    "  else if (hour >= 20 || hour < 5) { period = 'noche'; icon = '🌙'; color = '#5dade2'; }\n"
    "  return { day, hour, minute, period, icon, color, totalMin, hhmm: String(hour).padStart(2,'0')+':'+String(minute).padStart(2,'0') };\n"
    "}\n"
    "function dgProgressBar(current, max, color, emoji, label, sublabel) {\n"
    "  const pct = max > 0 ? Math.max(0, Math.min(100, (current / max) * 100)) : 0;\n"
    "  let html = '<div style=\"display:flex;align-items:center;gap:8px;margin:6px 0;\">';\n"
    "  html += '<span style=\"width:24px;font-size:18px;text-align:center;\">' + emoji + '</span>';\n"
    "  html += '<div style=\"flex:1;background:rgba(0,0,0,0.35);border-radius:4px;height:18px;overflow:hidden;border:1px solid var(--border);position:relative;\">';\n"
    "  html += '<div style=\"width:'+pct+'%;height:100%;background:'+color+';transition:width 0.25s;\"></div>';\n"
    "  html += '<div style=\"position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,0.7);\">'+label+'</div>';\n"
    "  html += '</div>';\n"
    "  html += '<span style=\"min-width:60px;font-weight:600;font-size:13px;text-align:right;\">'+current+' / '+max+'</span>';\n"
    "  html += '</div>';\n"
    "  if (sublabel) html += '<div style=\"font-size:11px;color:var(--ink-dim);margin-left:32px;margin-top:-4px;margin-bottom:4px;\">'+sublabel+'</div>';\n"
    "  return html;\n"
    "}\n"
    "function dgLongRest() {\n"
    "  if (!state.dungeon) { alert('No hay dungeon activo'); return; }\n"
    "  const dg = state.dungeon;\n"
    "  const partySize = dg.partySize || 11;\n"
    "  const consumed = partySize;\n"
    "  if ((dg.rationsTotal || 0) < consumed) {\n"
    "    if (!confirm('No hay suficientes raciones ('+(dg.rationsTotal||0)+'/'+consumed+'). ¿Descansar igual? PCs hambrientos al día siguiente.')) return;\n"
    "  } else {\n"
    "    if (!confirm('Descanso nocturno (8h, +48 turnos in-game)? Consume '+consumed+' raciones (1/PC), recupera 1d3 HP por PC, resetea torch / wandering / rest counters.')) return;\n"
    "  }\n"
    "  // Advance 48 turns of time, but suppress dgAdvance side effects (no wandering during safe camp)\n"
    "  dg.turns = (dg.turns || 0) + 48;\n"
    "  dg.dayInDungeon = (dg.dayInDungeon || 1) + 1;\n"
    "  // Reset cycles\n"
    "  dg.restTimer = 5;\n"
    "  dg.wanderingTimer = 2;\n"
    "  dg.wanderingNoise = 0;\n"
    "  dg.torchTurnsLeft = 0;          // torch out — must light another in the morning\n"
    "  // Consume rations\n"
    "  dg.rationsTotal = Math.max(0, (dg.rationsTotal || 0) - consumed);\n"
    "  // Roll 1d3 HP per PC\n"
    "  let healed = 0;\n"
    "  for (let i = 0; i < partySize; i++) healed += (1 + Math.floor(Math.random()*3));\n"
    "  logEvent('🌙 Descanso nocturno: 8h pasaron. Día '+dg.dayInDungeon+'. Recuperación total ~'+healed+' HP ('+partySize+' PCs × 1d3). Raciones restantes: '+dg.rationsTotal);\n"
    "  if (dg.rationsTotal <= 0) logEvent('⚠ SIN RACIONES — los PCs hambrientos al despertar (penalty -1 to-hit/-1 dmg adicional hasta comer).');\n"
    "  saveState(); renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "  alert('Descanso nocturno completado.\\nDía '+dg.dayInDungeon+', '+String(dg.startHour||9).padStart(2,'0')+':00.\\nHealed ~'+healed+' HP, raciones: '+dg.rationsTotal+'.');\n"
    "}\n"
    "function dgSetRations(n) {\n"
    "  if (!state.dungeon) return;\n"
    "  var v = parseInt(n, 10);\n"
    "  if (isNaN(v) || v < 0) v = 0;\n"
    "  state.dungeon.rationsTotal = v;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "function dgSetPartySize(n) {\n"
    "  if (!state.dungeon) return;\n"
    "  var v = parseInt(n, 10);\n"
    "  if (isNaN(v) || v < 1) v = 1;\n"
    "  state.dungeon.partySize = v;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "function dgSetStartHour(n) {\n"
    "  if (!state.dungeon) return;\n"
    "  var v = parseInt(n, 10);\n"
    "  if (isNaN(v) || v < 0 || v > 23) v = 9;\n"
    "  state.dungeon.startHour = v;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}",
)

# ── 5) Reemplazar el tracker card v5y con uno visual v5z ──
patch(
    "tracker card v5z visual",
    "  // Tracker card\n"
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
    "  html += '<div>🔥 Antorcha: <b>' + (dgT.torchTurnsLeft||0) + ' / ' + torchMax + '</b> turns &nbsp;·&nbsp; Mochila: <b>' + (g.torchesInPack||0) + '</b></div>';\n"
    "  html += '<div>👹 Wandering: <b>' + (dgT.wanderingTimer||0) + ' / 2</b> turns &nbsp;·&nbsp; Ruido: <b>+' + (dgT.wanderingNoise||0) + '</b> (umbral 1d6 ≤ ' + (1 + (dgT.wanderingNoise||0)) + ')</div>';\n"
    "  html += '<div>😴 Descanso: <b>' + (dgT.restTimer != null ? dgT.restTimer : 5) + ' / 5</b> turns hasta rest</div>';\n"
    "  html += '</div>';\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:10px 0;\">';\n"
    "  html += '<div style=\"display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:12px;\">';\n"
    "  html += '<label>Party ft/turn:</label><input type=\"number\" value=\"' + (g.partyFtPerTurn||200) + '\" min=\"30\" max=\"600\" step=\"10\" style=\"width:70px;\" onchange=\"gridSetSpeed(this.value, null)\">';\n"
    "  html += '<label>Cell ft:</label><input type=\"number\" value=\"' + (g.cellFt||10) + '\" min=\"1\" max=\"50\" step=\"1\" style=\"width:55px;\" onchange=\"gridSetSpeed(null, this.value)\">';\n"
    "  html += '<label>Antorchas:</label><input type=\"number\" value=\"' + (g.torchesInPack||0) + '\" min=\"0\" max=\"99\" step=\"1\" style=\"width:55px;\" onchange=\"gridSetTorches(this.value)\">';\n"
    "  html += '</div>';\n"
    "  html += '<div style=\"margin-top:10px;display:grid;grid-template-columns:repeat(2,1fr);gap:6px;\">';\n"
    "  html += '<button class=\"btn\" onclick=\"gridAddTurn()\">+1 Turno (actividad)</button>';\n"
    "  html += '<button class=\"btn\" onclick=\"dgRest()\">😴 Descansar 1 turno</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridLightTorch()\">🔥 Encender antorcha</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgWanderingCheck()\">🎲 Wandering check</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridAddNoise()\">🔊 Ruido +1</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetTime()\">⟲ Reset pasos</button>';\n"
    "  html += '</div>';\n"
    "  html += '</div>';",
    "  // v5z: Tracker visual con time-of-day + progress bars + raciones + long rest\n"
    "  var dgT = state.dungeon || {};\n"
    "  var torchMax = dgT.torchTurnsMax || 6;\n"
    "  var partySize = dgT.partySize || 11;\n"
    "  var rations = dgT.rationsTotal != null ? dgT.rationsTotal : (partySize * 7);\n"
    "  var ti = dgGetTimeInfo();\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>⏱ Tracker de exploración</h3>';\n"
    "  // PROMINENT TIME DISPLAY\n"
    "  html += '<div id=\"grid-real-timebox\" style=\"background:linear-gradient(135deg,'+ti.color+'22,'+ti.color+'11);border:1px solid '+ti.color+'66;padding:12px;border-radius:6px;margin-bottom:12px;text-align:center;\">';\n"
    "  html += '<div style=\"font-size:28px;font-weight:bold;line-height:1;\">'+ti.icon+' <span id=\"grid-real-hhmm\">'+ti.hhmm+'</span></div>';\n"
    "  html += '<div style=\"font-size:13px;color:var(--ink-dim);margin-top:6px;\">Día <b id=\"grid-real-day\">'+ti.day+'</b> · <span id=\"grid-real-period\" style=\"color:'+ti.color+';font-weight:600;\">'+ti.period+'</span> · '+(g.steps||0)+' pasos · '+_turns+' turnos · '+_minutes+' min</div>';\n"
    "  html += '</div>';\n"
    "  // PROGRESS BARS\n"
    "  html += dgProgressBar((dgT.torchTurnsLeft||0), torchMax, '#d4a04a', '🔥', 'Antorcha actual', 'Mochila: <b>'+(g.torchesInPack||0)+'</b> antorchas más');\n"
    "  html += dgProgressBar(2 - (dgT.wanderingTimer||0), 2, '#c0392b', '👹', 'Hasta wandering check', ((dgT.wanderingNoise||0) > 0 ? '+'+ (dgT.wanderingNoise||0) +' ruido (umbral 1d6 ≤ '+ (1 + (dgT.wanderingNoise||0)) +')' : 'Umbral normal: 1d6 = 1'));\n"
    "  html += dgProgressBar(5 - (dgT.restTimer != null ? dgT.restTimer : 5), 5, '#e67e22', '😴', 'Hasta descanso forzado', 'ACKS: cada 5 turnos rest 1 turn o -1/-1');\n"
    "  var maxRations = partySize * 7;\n"
    "  var daysFood = partySize > 0 ? Math.floor(rations / partySize) : 0;\n"
    "  html += dgProgressBar(rations, maxRations, '#7ee787', '🍞', 'Raciones', daysFood + ' días de comida (party de '+partySize+' PCs)');\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:10px 0;\">';\n"
    "  // Inputs configurables\n"
    "  html += '<div style=\"display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:12px;\">';\n"
    "  html += '<label>Party ft/turn:</label><input type=\"number\" value=\"' + (g.partyFtPerTurn||200) + '\" min=\"30\" max=\"600\" step=\"10\" style=\"width:65px;\" onchange=\"gridSetSpeed(this.value, null)\">';\n"
    "  html += '<label>Cell ft:</label><input type=\"number\" value=\"' + (g.cellFt||10) + '\" min=\"1\" max=\"50\" step=\"1\" style=\"width:50px;\" onchange=\"gridSetSpeed(null, this.value)\">';\n"
    "  html += '<label>Antorchas:</label><input type=\"number\" value=\"' + (g.torchesInPack||0) + '\" min=\"0\" max=\"99\" step=\"1\" style=\"width:50px;\" onchange=\"gridSetTorches(this.value)\">';\n"
    "  html += '<label>Raciones:</label><input type=\"number\" value=\"' + rations + '\" min=\"0\" max=\"999\" step=\"1\" style=\"width:55px;\" onchange=\"dgSetRations(this.value)\">';\n"
    "  html += '<label>Party size:</label><input type=\"number\" value=\"' + partySize + '\" min=\"1\" max=\"50\" step=\"1\" style=\"width:45px;\" onchange=\"dgSetPartySize(this.value)\">';\n"
    "  html += '<label>Hora inicio:</label><input type=\"number\" value=\"' + (dgT.startHour != null ? dgT.startHour : 9) + '\" min=\"0\" max=\"23\" step=\"1\" style=\"width:45px;\" onchange=\"dgSetStartHour(this.value)\">';\n"
    "  html += '</div>';\n"
    "  html += '<div style=\"margin-top:10px;display:grid;grid-template-columns:repeat(2,1fr);gap:6px;\">';\n"
    "  html += '<button class=\"btn\" onclick=\"gridAddTurn()\">+1 Turno (actividad)</button>';\n"
    "  html += '<button class=\"btn\" onclick=\"dgRest()\">😴 Descansar 1 turno</button>';\n"
    "  html += '<button class=\"btn\" style=\"background:#1a1a3a;color:#5dade2;\" onclick=\"dgLongRest()\">🌙 Descanso nocturno (8h)</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridLightTorch()\">🔥 Encender antorcha</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgWanderingCheck()\">🎲 Wandering check</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridAddNoise()\">🔊 Ruido +1</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetTime()\">⟲ Reset pasos</button>';\n"
    "  html += '<span></span>';\n"
    "  html += '</div>';\n"
    "  html += '</div>';",
)

# ── 6) Banner alerts agregar atardecer/noche/raciones ──
patch(
    "alerts banner v5z dusk/night/rations",
    "    if (dgB.restTimer === 0) alerts.push({color:'#e67e22', emoji:'😴', msg:'Rest DUE — 5 turnos sin descanso. Penalty -1/-1 hasta descansar.', action:'dgRest()', actionLabel:'Descansar'});\n"
    "    if (dgB.wanderingTimer === 0) alerts.push({color:'#c0392b', emoji:'👹', msg:'Wandering check DUE — tirar 1d6' + (dgB.wanderingNoise>0 ? ' (ruido +'+dgB.wanderingNoise+', umbral ≤'+(1+dgB.wanderingNoise)+')' : ''), action:'dgWanderingCheck()', actionLabel:'Tirar 1d6'});\n"
    "    if (dgB.torchTurnsLeft === 0) alerts.push({color:'#1a1410', emoji:'🌑', msg:'Antorcha AGOTADA. Combate -4 to-hit. Encender otra de mochila.', action:'gridLightTorch()', actionLabel:'Encender'});\n"
    "    else if (dgB.torchTurnsLeft <= 2) alerts.push({color:'#d4a04a', emoji:'🔥', msg:'Antorcha en últimos '+dgB.torchTurnsLeft+' turnos — preparar otra.', action:null});",
    "    if (dgB.restTimer === 0) alerts.push({color:'#e67e22', emoji:'😴', msg:'Rest DUE — 5 turnos sin descanso. Penalty -1/-1 hasta descansar.', action:'dgRest()', actionLabel:'Descansar'});\n"
    "    if (dgB.wanderingTimer === 0) alerts.push({color:'#c0392b', emoji:'👹', msg:'Wandering check DUE — tirar 1d6' + (dgB.wanderingNoise>0 ? ' (ruido +'+dgB.wanderingNoise+', umbral ≤'+(1+dgB.wanderingNoise)+')' : ''), action:'dgWanderingCheck()', actionLabel:'Tirar 1d6'});\n"
    "    if (dgB.torchTurnsLeft === 0) alerts.push({color:'#1a1410', emoji:'🌑', msg:'Antorcha AGOTADA. Combate -4 to-hit. Encender otra de mochila.', action:'gridLightTorch()', actionLabel:'Encender'});\n"
    "    else if (dgB.torchTurnsLeft <= 2) alerts.push({color:'#d4a04a', emoji:'🔥', msg:'Antorcha en últimos '+dgB.torchTurnsLeft+' turnos — preparar otra.', action:null});\n"
    "    // v5z: time-of-day alerts (Forbidden Marsh = peligro al volver a Helix)\n"
    "    var _tiBan = dgGetTimeInfo();\n"
    "    if (_tiBan.hour >= 17 && _tiBan.hour < 20) alerts.push({color:'#d35400', emoji:'🌅', msg:'Atardecer ('+_tiBan.hhmm+'). Si querés volver a Helix, pasar el Forbidden Marsh de noche es peligroso. Considerá Descanso nocturno acá o iniciar regreso ya.', action:'dgLongRest()', actionLabel:'🌙 Acampar 8h'});\n"
    "    else if (_tiBan.hour >= 20 || _tiBan.hour < 5) alerts.push({color:'#1a1a3a', emoji:'🌙', msg:'NOCHE ('+_tiBan.hhmm+'). Forbidden Marsh letal a esta hora. Descanso nocturno recomendado en zona segura del dungeon.', action:'dgLongRest()', actionLabel:'🌙 Acampar 8h'});\n"
    "    // Raciones bajas\n"
    "    var _ps = dgB.partySize || 11;\n"
    "    var _r = dgB.rationsTotal != null ? dgB.rationsTotal : 77;\n"
    "    if (_r < _ps) alerts.push({color:'#922b21', emoji:'🍞', msg:'Sin raciones suficientes para 1 día más ('+_r+' < '+_ps+'). Volver al pueblo o conseguir comida.', action:null});",
)

# ── 7) updateRealQuickStats: incluir time display refresh ──
patch(
    "updateRealQuickStats v5z time",
    "function updateRealQuickStats() {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  var elPos = document.getElementById('grid-real-pos'); if (elPos) elPos.textContent = '(' + g.realPlayer.x + ',' + g.realPlayer.y + ')';\n"
    "  var elSeen = document.getElementById('grid-real-seen'); if (elSeen) elSeen.textContent = (g.realSeen||[]).length;\n"
    "  var elSteps = document.getElementById('grid-real-steps'); if (elSteps) elSteps.textContent = (g.steps||0);\n"
    "  var ftRatio = (g.cellFt || 10) / Math.max(1, (g.partyFtPerTurn || 200));\n"
    "  var turnsRaw = (g.steps || 0) * ftRatio;\n"
    "  var elTurns = document.getElementById('grid-real-turns'); if (elTurns) elTurns.textContent = Math.floor(turnsRaw);\n"
    "  var elMins = document.getElementById('grid-real-mins'); if (elMins) elMins.textContent = (turnsRaw * 10).toFixed(1);\n"
    "  var elDmLabel = document.getElementById('grid-real-dm-label');\n"
    "  if (elDmLabel) elDmLabel.innerHTML = g.dmView ? '<span style=\"color:#5dade2;\">👁 Vista DM</span>' : '<span style=\"color:#aaa;\">👤 Vista jugadores</span>';\n"
    "}",
    "function updateRealQuickStats() {\n"
    "  const g = gridState(); if (!g) return;\n"
    "  var elPos = document.getElementById('grid-real-pos'); if (elPos) elPos.textContent = '(' + g.realPlayer.x + ',' + g.realPlayer.y + ')';\n"
    "  var elSeen = document.getElementById('grid-real-seen'); if (elSeen) elSeen.textContent = (g.realSeen||[]).length;\n"
    "  var elSteps = document.getElementById('grid-real-steps'); if (elSteps) elSteps.textContent = (g.steps||0);\n"
    "  var ftRatio = (g.cellFt || 10) / Math.max(1, (g.partyFtPerTurn || 200));\n"
    "  var turnsRaw = (g.steps || 0) * ftRatio;\n"
    "  var elTurns = document.getElementById('grid-real-turns'); if (elTurns) elTurns.textContent = Math.floor(turnsRaw);\n"
    "  var elMins = document.getElementById('grid-real-mins'); if (elMins) elMins.textContent = (turnsRaw * 10).toFixed(1);\n"
    "  var elDmLabel = document.getElementById('grid-real-dm-label');\n"
    "  if (elDmLabel) elDmLabel.innerHTML = g.dmView ? '<span style=\"color:#5dade2;\">👁 Vista DM</span>' : '<span style=\"color:#aaa;\">👤 Vista jugadores</span>';\n"
    "  // v5z: refresh time-of-day display\n"
    "  if (typeof dgGetTimeInfo === 'function' && state.dungeon) {\n"
    "    var ti = dgGetTimeInfo();\n"
    "    var elH = document.getElementById('grid-real-hhmm'); if (elH) elH.textContent = ti.hhmm;\n"
    "    var elD = document.getElementById('grid-real-day'); if (elD) elD.textContent = ti.day;\n"
    "    var elP = document.getElementById('grid-real-period'); if (elP) { elP.textContent = ti.period; elP.style.color = ti.color; }\n"
    "  }\n"
    "}",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
