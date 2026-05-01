"""
v6a patches: Encuentro pipeline integrado (Capa B).

Wildcard mode delivery #1.

Changes:
  - Tabla wandering specifica de Barrowmaze (1d20 outcome) con monsters
    tipicos del modulo (skeletons, zombies, ghouls, gnolls, wights, etc).
  - dgWanderingCheck() ramificado: si dungeon=barrowmaze, usa tabla del modulo;
    si no, fallback al ACKS.monsters generico (comportamiento previo).
  - state.dungeon.activeEncounter persiste el encuentro activo:
    {name, count, hd, ac, dmg, notes, distance, surpriseParty, surpriseMonsters}
  - Banner sticky "🜍 ENCUENTRO" con info estructurada + boton "→ Combate".
  - dgEncounterToCombat() pre-carga foes en el combat panel y switchea modo.
  - dgDismissEncounter() para resolver sin combate (negociacion / huida / etc).
  - Distance roll: 1d6 × 10 ft (dungeon distance ACKS RAW).
  - Surprise rolls (1d6 each side, 1-2 sorprendidos) — informativos, no automatizan
    primer round (Marcos prefiere mesa).

Pipeline: cp v5z -> v6a, this script, validate, deploy.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6a.html")
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
    "<title>Cockpit V5z — v5z: Tiempo, hora del dia, raciones, descanso nocturno</title>",
    "<title>Cockpit V6a — v6a: Encuentro pipeline + tabla Barrowmaze + banner combate</title>",
)


# ── 2) Insertar BARROWMAZE_WANDERING table + helpers después de dgSetStartHour ──
patch(
    "barrowmaze wandering table + encounter helpers",
    "function dgSetStartHour(n) {\n"
    "  if (!state.dungeon) return;\n"
    "  var v = parseInt(n, 10);\n"
    "  if (isNaN(v) || v < 0 || v > 23) v = 9;\n"
    "  state.dungeon.startHour = v;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}",
    "function dgSetStartHour(n) {\n"
    "  if (!state.dungeon) return;\n"
    "  var v = parseInt(n, 10);\n"
    "  if (isNaN(v) || v < 0 || v > 23) v = 9;\n"
    "  state.dungeon.startHour = v;\n"
    "  saveState();\n"
    "  renderGridCrawler();\n"
    "}\n"
    "\n"
    "// === v6a: Wandering table specifica Barrowmaze (level 1-3 main areas) ===\n"
    "// 1d20 roll → entry. Coverage: skeletons / zombies / rats / gnolls / ghouls /\n"
    "// giant spider / wights / wraith. Stats ACKS-compatible.\n"
    "const BARROWMAZE_WANDERING = [\n"
    "  { range:[1,4],   name:'Skeletons',     count:'2d4', hd:1,   ac:2, dmg:'1d6',          notes:'Undead, mindless. Inmune a sleep/charm.',  xp:10 },\n"
    "  { range:[5,7],   name:'Zombies',       count:'2d4', hd:2,   ac:2, dmg:'1d8',          notes:'Lentos. Inmune a sleep/charm. Ultimo en init.', xp:20 },\n"
    "  { range:[8,10],  name:'Giant Rats',    count:'3d6', hd:'1-1', ac:1, dmg:'1d3',        notes:'Disease save vs poison o 1d6 dias enfermo.', xp:4 },\n"
    "  { range:[11,13], name:'Gnolls',        count:'1d6', hd:2,   ac:5, dmg:'2d4',          notes:'Hyena-folk raiders. Pueden parlar.',         xp:20 },\n"
    "  { range:[14,16], name:'Ghouls',        count:'1d4', hd:2,   ac:6, dmg:'1d3',          notes:'Paralisis on hit (save vs paralyze).',       xp:25 },\n"
    "  { range:[17,18], name:'Giant Spider',  count:'1d3', hd:3,   ac:6, dmg:'1d8 + veneno', notes:'Save vs poison o muerte (-2 vs grandes).',   xp:30 },\n"
    "  { range:[19,19], name:'Wights',        count:'1d4', hd:3,   ac:5, dmg:'1d6 + drain',  notes:'Energy drain (-1 level por hit).',           xp:50 },\n"
    "  { range:[20,20], name:'Wraith',        count:'1',   hd:4,   ac:5, dmg:'1d6 + drain',  notes:'Solo armas magicas/plata. Energy drain.',    xp:75 }\n"
    "];\n"
    "\n"
    "function rollDie(n) { return Math.floor(Math.random()*n) + 1; }\n"
    "function rollDiceExpr(expr) {\n"
    "  // Simple parser for 'NdM' or 'NdM-K' or 'NdM+K'\n"
    "  if (typeof expr === 'number') return expr;\n"
    "  if (typeof expr !== 'string') return 1;\n"
    "  expr = expr.replace(/\\s+/g,'');\n"
    "  const m = /^(\\d+)d(\\d+)([+-]\\d+)?$/i.exec(expr);\n"
    "  if (!m) {\n"
    "    const n = parseInt(expr, 10);\n"
    "    return isNaN(n) ? 1 : n;\n"
    "  }\n"
    "  const N = parseInt(m[1],10), M = parseInt(m[2],10), K = parseInt(m[3]||'0',10);\n"
    "  let total = 0;\n"
    "  for (let i = 0; i < N; i++) total += rollDie(M);\n"
    "  return Math.max(1, total + K);\n"
    "}\n"
    "\n"
    "function dgRollBarrowmazeEncounter() {\n"
    "  const tableRoll = rollDie(20);\n"
    "  const entry = BARROWMAZE_WANDERING.find(e => tableRoll >= e.range[0] && tableRoll <= e.range[1]);\n"
    "  if (!entry) return null;\n"
    "  const count = rollDiceExpr(entry.count);\n"
    "  // ACKS RAW dungeon distance: 1d6 × 10 ft\n"
    "  const distance = rollDie(6) * 10;\n"
    "  // Surprise: each side rolls 1d6, 1-2 = surprised\n"
    "  const surpriseParty = rollDie(6) <= 2;\n"
    "  const surpriseMonsters = rollDie(6) <= 2;\n"
    "  // Total HP for the group (rough estimate: HD × 4.5 per monster)\n"
    "  const hdNum = (typeof entry.hd === 'number') ? entry.hd : (parseInt(String(entry.hd))||1);\n"
    "  const totalHpEstimate = Math.round(count * hdNum * 4.5);\n"
    "  return {\n"
    "    name: entry.name, count, hd: entry.hd, ac: entry.ac, dmg: entry.dmg, notes: entry.notes,\n"
    "    xp: entry.xp, totalHpEstimate,\n"
    "    distance, surpriseParty, surpriseMonsters,\n"
    "    rollD20: tableRoll,\n"
    "    rolledAt: state.dungeon.turns\n"
    "  };\n"
    "}\n"
    "\n"
    "function dgEncounterToCombat() {\n"
    "  if (!state.dungeon || !state.dungeon.activeEncounter) return;\n"
    "  const e = state.dungeon.activeEncounter;\n"
    "  // Add e.count copies of monster as foes in combat panel\n"
    "  if (!state.combat) state.combat = { actors: [], current: 0, round: 0 };\n"
    "  const hdNum = (typeof e.hd === 'number') ? e.hd : (parseInt(String(e.hd))||1);\n"
    "  for (let i = 0; i < e.count; i++) {\n"
    "    state.combat.actors.push({\n"
    "      name: e.name + (e.count > 1 ? ' #'+(i+1) : ''),\n"
    "      foe: true,\n"
    "      init: null,\n"
    "      hp: Math.max(1, rollDiceExpr(hdNum + 'd8')),\n"
    "      ac: e.ac,\n"
    "      meta: 'HD '+e.hd+' DMG '+e.dmg + (e.notes ? ' · '+e.notes : '')\n"
    "    });\n"
    "  }\n"
    "  logEvent('🜍 → Combat panel: cargados '+e.count+'× '+e.name+'. Distancia '+e.distance+' ft. ' +\n"
    "    (e.surpriseParty ? 'Party SORPRENDIDA. ' : '') + (e.surpriseMonsters ? 'Monsters SORPRENDIDOS. ' : ''));\n"
    "  state.dungeon.activeEncounter = null;\n"
    "  saveState(); renderEventLog();\n"
    "  // Switch to combat mode if function exists\n"
    "  if (typeof setMode === 'function') {\n"
    "    setMode('combat');\n"
    "  } else if (typeof renderCombat === 'function') {\n"
    "    renderCombat();\n"
    "  }\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}\n"
    "\n"
    "function dgDismissEncounter() {\n"
    "  if (!state.dungeon) return;\n"
    "  if (!confirm('Resolver encuentro sin combate (parlar / huir / esquivar)?')) return;\n"
    "  state.dungeon.activeEncounter = null;\n"
    "  logEvent('🜍 Encuentro dismissed (sin combate).');\n"
    "  saveState(); renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}",
)


# ── 3) Modificar dgWanderingCheck para usar tabla Barrowmaze cuando aplique ──
patch(
    "dgWanderingCheck v6a w/ Barrowmaze table",
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
    "function dgWanderingCheck() {\n"
    "  if (!state.dungeon) return;\n"
    "  const noise = state.dungeon.wanderingNoise || 0;\n"
    "  const threshold = 1 + noise;\n"
    "  const r = rollDice('1d6');\n"
    "  const noiseStr = noise > 0 ? ' (ruido +'+noise+', umbral 1d6≤'+threshold+')' : '';\n"
    "  if (r.total <= threshold) {\n"
    "    // v6a: si Barrowmaze, usa tabla del modulo + crea activeEncounter para banner\n"
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
    "    } else {\n"
    "      // Fallback generico\n"
    "      const beasts = Object.entries(ACKS.monsters || {});\n"
    "      if (beasts.length) {\n"
    "        const [name, m] = beasts[Math.floor(Math.random()*beasts.length)];\n"
    "        logEvent('🜍 Wandering monster: '+name+' (HD '+(m.hd||'?')+', AC '+(m.ac||'?')+')', '1d6='+r.total+noiseStr);\n"
    "      }\n"
    "    }\n"
    "  } else {\n"
    "    logEvent('Wandering check: nada', '1d6='+r.total+noiseStr);\n"
    "  }\n"
    "  state.dungeon.wanderingNoise = 0;\n"
    "  state.dungeon.wanderingTimer = 2;\n"
    "  saveState(); renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}",
)


# ── 4) Banner alerts: agregar activeEncounter con info estructurada ──
patch(
    "alerts banner v6a active encounter",
    "    if (dgB.restTimer === 0) alerts.push({color:'#e67e22', emoji:'😴', msg:'Rest DUE — 5 turnos sin descanso. Penalty -1/-1 hasta descansar.', action:'dgRest()', actionLabel:'Descansar'});",
    "    // v6a: active encounter from Barrowmaze wandering table\n"
    "    if (dgB.activeEncounter) {\n"
    "      const e = dgB.activeEncounter;\n"
    "      let msg = '<b>🜍 ENCUENTRO</b>: <b>'+e.count+'× '+e.name+'</b> (HD '+e.hd+', AC '+e.ac+', DMG '+e.dmg+') a <b>'+e.distance+' ft</b>. ';\n"
    "      if (e.surpriseParty)    msg += '<span style=\"color:#ffb86b;\">⚡ Party sorprendida.</span> ';\n"
    "      if (e.surpriseMonsters) msg += '<span style=\"color:#7ee787;\">✨ Ellos sorprendidos.</span> ';\n"
    "      msg += '<i>'+e.notes+'</i>';\n"
    "      alerts.push({color:'#922b21', emoji:'🜍', msg:msg, action:'dgEncounterToCombat()', actionLabel:'→ Combate'});\n"
    "      alerts.push({color:'#5d3030', emoji:'💬', msg:'Resolver sin combate (parlar / huir / esquivar): tirá reaction (2d6+Cha) en mesa, o gestiona narrativamente.', action:'dgDismissEncounter()', actionLabel:'Dismiss'});\n"
    "    }\n"
    "    if (dgB.restTimer === 0) alerts.push({color:'#e67e22', emoji:'😴', msg:'Rest DUE — 5 turnos sin descanso. Penalty -1/-1 hasta descansar.', action:'dgRest()', actionLabel:'Descansar'});",
)


# ── 5) Boton de "Wandering check" en tracker card: cuando hay encuentro activo, ofrecer "→ Combate" en su lugar ──
# (Optional polish, dejamos los buttons donde están — el banner es prominente.)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
