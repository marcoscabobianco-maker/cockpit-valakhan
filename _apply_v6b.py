"""
v6b patches: PC roster + formacion + lightBearer integrados al grid táctico.

Wildcard mode delivery #2 (acumulativo sobre v6a).

Changes:
  - dgInitParty(): inicializa state.dungeon.partyState desde CAMPAIGNS.pcs
    (lee novatos_ravenloft.json automatico). Parsea "9/9" -> {hp:9, hpMax:9}.
  - dgPCHpDelta(pcId, delta): suma/resta HP, log + alerta si llega a 0 (mortal wound).
  - dgPCDamage(pcId, expr): tira dado (e.g. '1d6') y aplica.
  - dgSetPCPosition(pcId, pos): vanguardia | middle | rear.
  - dgSetLightBearer(pcId): toggle portador de luz.
  - Card "👥 Party (N alive)" en el panel derecho del grid real:
    cada PC con HP bar coloreada (verde/amarillo/rojo segun %), AC, clase/level,
    botones rapidos -1/+1/-1d6 HP, select de posición, toggle lightBearer.

Pipeline: cp v6a -> v6b, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6b.html")
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
    "<title>Cockpit V6a — v6a: Encuentro pipeline + tabla Barrowmaze + banner combate</title>",
    "<title>Cockpit V6b — v6b: PC roster (11 novatos) + formación + lightBearer</title>",
)


# ── 2) Helpers party state + render ──
patch(
    "v6b party state helpers",
    "function dgDismissEncounter() {\n"
    "  if (!state.dungeon) return;\n"
    "  if (!confirm('Resolver encuentro sin combate (parlar / huir / esquivar)?')) return;\n"
    "  state.dungeon.activeEncounter = null;\n"
    "  logEvent('🜍 Encuentro dismissed (sin combate).');\n"
    "  saveState(); renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}",
    "function dgDismissEncounter() {\n"
    "  if (!state.dungeon) return;\n"
    "  if (!confirm('Resolver encuentro sin combate (parlar / huir / esquivar)?')) return;\n"
    "  state.dungeon.activeEncounter = null;\n"
    "  logEvent('🜍 Encuentro dismissed (sin combate).');\n"
    "  saveState(); renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}\n"
    "\n"
    "// === v6b: PC roster + formacion + lightBearer ===\n"
    "function _parseHpString(s) {\n"
    "  if (typeof s === 'number') return { curr: s, max: s };\n"
    "  if (typeof s !== 'string') return { curr: 0, max: 0 };\n"
    "  if (s.includes('/')) {\n"
    "    const parts = s.split('/').map(p => parseInt(p.trim(), 10));\n"
    "    return { curr: parts[0]||0, max: parts[1] || parts[0] || 0 };\n"
    "  }\n"
    "  const n = parseInt(s, 10);\n"
    "  return isNaN(n) ? { curr:0, max:0 } : { curr:n, max:n };\n"
    "}\n"
    "function _getPCList() {\n"
    "  if (typeof CAMPAIGNS !== 'undefined' && CAMPAIGNS) {\n"
    "    if (Array.isArray(CAMPAIGNS.pcs)) return CAMPAIGNS.pcs;\n"
    "    for (const k of Object.keys(CAMPAIGNS)) {\n"
    "      const v = CAMPAIGNS[k];\n"
    "      if (v && Array.isArray(v.pcs)) return v.pcs;\n"
    "    }\n"
    "  }\n"
    "  return [];\n"
    "}\n"
    "function dgInitParty() {\n"
    "  if (!state.dungeon) return;\n"
    "  if (!state.dungeon.partyState) state.dungeon.partyState = {};\n"
    "  const pcs = _getPCList();\n"
    "  for (const pc of pcs) {\n"
    "    if (!state.dungeon.partyState[pc.id]) {\n"
    "      const hp = _parseHpString(pc.hp);\n"
    "      state.dungeon.partyState[pc.id] = {\n"
    "        hp: hp.curr,\n"
    "        hpMax: hp.max,\n"
    "        ac: pc.ac || 0,\n"
    "        conditions: [],\n"
    "        position: 'middle'\n"
    "      };\n"
    "    }\n"
    "  }\n"
    "}\n"
    "function _getPCName(pcId) {\n"
    "  const pcs = _getPCList();\n"
    "  const pc = pcs.find(p => p.id === pcId);\n"
    "  return pc ? pc.name : pcId;\n"
    "}\n"
    "function dgPCHpDelta(pcId, delta) {\n"
    "  if (!state.dungeon) return;\n"
    "  if (!state.dungeon.partyState) state.dungeon.partyState = {};\n"
    "  let ps = state.dungeon.partyState[pcId];\n"
    "  if (!ps) { dgInitParty(); ps = state.dungeon.partyState[pcId]; if (!ps) return; }\n"
    "  const before = ps.hp;\n"
    "  ps.hp = Math.max(0, Math.min(ps.hpMax, ps.hp + delta));\n"
    "  if (delta < 0 && ps.hp === 0 && before > 0) {\n"
    "    logEvent('💀 '+_getPCName(pcId)+' a 0 HP — Mortal Wound table required (consultar /tools/ ACKS Assistant).');\n"
    "  } else if (delta < 0) {\n"
    "    logEvent('🗡 '+_getPCName(pcId)+': '+before+' → '+ps.hp+' HP ('+delta+').');\n"
    "  } else if (delta > 0) {\n"
    "    logEvent('💚 '+_getPCName(pcId)+': '+before+' → '+ps.hp+' HP (+'+delta+').');\n"
    "  }\n"
    "  saveState(); renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}\n"
    "function dgPCDamage(pcId, expr) {\n"
    "  const dmg = (typeof rollDiceExpr === 'function') ? rollDiceExpr(expr) : 1;\n"
    "  dgPCHpDelta(pcId, -dmg);\n"
    "  logEvent('🎲 '+_getPCName(pcId)+' recibió '+dmg+' damage ('+expr+').');\n"
    "  renderEventLog();\n"
    "}\n"
    "function dgSetPCPosition(pcId, position) {\n"
    "  if (!state.dungeon) return;\n"
    "  if (!state.dungeon.partyState) state.dungeon.partyState = {};\n"
    "  let ps = state.dungeon.partyState[pcId];\n"
    "  if (!ps) { dgInitParty(); ps = state.dungeon.partyState[pcId]; if (!ps) return; }\n"
    "  ps.position = position;\n"
    "  logEvent('🛡 '+_getPCName(pcId)+' → '+position);\n"
    "  saveState(); renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}\n"
    "function dgSetLightBearer(pcId) {\n"
    "  if (!state.dungeon) return;\n"
    "  const g = gridState(); if (!g) return;\n"
    "  if (g.lightBearer === pcId) {\n"
    "    g.lightBearer = null;\n"
    "    logEvent('🔥 '+_getPCName(pcId)+' soltó la antorcha.');\n"
    "  } else {\n"
    "    g.lightBearer = pcId;\n"
    "    logEvent('🔥 '+_getPCName(pcId)+' lleva la antorcha.');\n"
    "  }\n"
    "  saveState(); renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "}\n"
    "function _renderPartyCard() {\n"
    "  const pcs = _getPCList();\n"
    "  if (!pcs.length) return '';\n"
    "  dgInitParty();\n"
    "  const partyState = (state.dungeon && state.dungeon.partyState) || {};\n"
    "  const lightBearer = (gridState() && gridState().lightBearer) || null;\n"
    "  const alive = pcs.filter(p => p.alive !== false);\n"
    "  let html = '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>👥 Party ('+alive.length+' novatos)</h3>';\n"
    "  // Group by position for visual formation\n"
    "  const byPos = { vanguard: [], middle: [], rear: [] };\n"
    "  for (const pc of alive) {\n"
    "    const ps = partyState[pc.id] || { hp:0, hpMax:0, ac:pc.ac||0, position:'middle' };\n"
    "    const pos = ps.position || 'middle';\n"
    "    byPos[pos] = byPos[pos] || [];\n"
    "    byPos[pos].push({ pc, ps });\n"
    "  }\n"
    "  const sections = [\n"
    "    ['vanguard', '⚔ Vanguardia (frente)', '#e67e22'],\n"
    "    ['middle',   '· Medio',                '#aaa'],\n"
    "    ['rear',     '← Retaguardia',          '#5dade2']\n"
    "  ];\n"
    "  for (const [posKey, label, color] of sections) {\n"
    "    const list = byPos[posKey] || [];\n"
    "    if (!list.length) continue;\n"
    "    html += '<div style=\"font-size:11px;color:'+color+';font-weight:600;margin:8px 0 4px;border-bottom:1px solid '+color+'33;\">'+label+' ('+list.length+')</div>';\n"
    "    for (const {pc, ps} of list) {\n"
    "      const hpPct = ps.hpMax > 0 ? (ps.hp / ps.hpMax) * 100 : 0;\n"
    "      const hpColor = hpPct > 60 ? '#7ee787' : hpPct > 30 ? '#f1c40f' : (hpPct > 0 ? '#e74c3c' : '#444');\n"
    "      const isLight = lightBearer === pc.id;\n"
    "      html += '<div style=\"background:rgba(0,0,0,0.2);padding:6px 8px;border-radius:4px;margin:4px 0;border-left:3px solid '+hpColor+';\">';\n"
    "      html += '<div style=\"display:flex;align-items:center;gap:6px;font-size:12px;\">';\n"
    "      html += '<b style=\"flex:1;\">'+(isLight?'🔥 ':'')+pc.name+'</b>';\n"
    "      html += '<span style=\"font-size:10px;color:var(--ink-dim);\">'+(pc.class||'?')+' L'+(pc.level||1)+'</span>';\n"
    "      html += '</div>';\n"
    "      html += '<div style=\"display:flex;align-items:center;gap:6px;margin-top:3px;\">';\n"
    "      html += '<div style=\"flex:1;background:rgba(0,0,0,0.4);border-radius:3px;height:14px;overflow:hidden;border:1px solid var(--border);position:relative;\">';\n"
    "      html += '<div style=\"width:'+hpPct+'%;height:100%;background:'+hpColor+';transition:width 0.2s;\"></div>';\n"
    "      html += '<div style=\"position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:600;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,0.7);\">HP '+ps.hp+'/'+ps.hpMax+'</div>';\n"
    "      html += '</div>';\n"
    "      html += '<span style=\"font-size:11px;color:var(--ink-dim);min-width:36px;text-align:right;\">AC '+(ps.ac||0)+'</span>';\n"
    "      html += '</div>';\n"
    "      html += '<div style=\"display:flex;gap:3px;margin-top:4px;flex-wrap:wrap;align-items:center;\">';\n"
    "      html += '<button class=\"btn secondary\" style=\"padding:2px 6px;font-size:10px;min-height:22px;\" onclick=\"dgPCHpDelta(\\''+pc.id+'\\', -1)\">−1</button>';\n"
    "      html += '<button class=\"btn secondary\" style=\"padding:2px 6px;font-size:10px;min-height:22px;\" onclick=\"dgPCHpDelta(\\''+pc.id+'\\', 1)\">+1</button>';\n"
    "      html += '<button class=\"btn secondary\" style=\"padding:2px 6px;font-size:10px;min-height:22px;\" onclick=\"dgPCDamage(\\''+pc.id+'\\', \\'1d6\\')\">−1d6</button>';\n"
    "      html += '<select onchange=\"dgSetPCPosition(\\''+pc.id+'\\', this.value)\" style=\"font-size:10px;padding:1px 2px;height:22px;\">';\n"
    "      html += '<option value=\"vanguard\"'+(ps.position==='vanguard'?' selected':'')+'>⚔ Vang</option>';\n"
    "      html += '<option value=\"middle\"'+(ps.position==='middle'?' selected':'')+'>· Med</option>';\n"
    "      html += '<option value=\"rear\"'+(ps.position==='rear'?' selected':'')+'>← Ret</option>';\n"
    "      html += '</select>';\n"
    "      html += '<button class=\"btn secondary\" style=\"padding:2px 6px;font-size:10px;min-height:22px;'+(isLight?'background:#d4a04a;color:#000;font-weight:bold;':'')+'\" onclick=\"dgSetLightBearer(\\''+pc.id+'\\')\" title=\"Marcar como portador de luz\">🔥</button>';\n"
    "      html += '</div>';\n"
    "      html += '</div>';\n"
    "    }\n"
    "  }\n"
    "  html += '<div style=\"font-size:10px;color:var(--ink-dim);margin-top:6px;line-height:1.4;\">PCs muertos/missing no se muestran. Botones: <b>−1/+1</b> ajuste manual, <b>−1d6</b> tirada de daño, <b>select</b> posición, <b>🔥</b> portador de luz (toggle).</div>';\n"
    "  html += '</div>';\n"
    "  return html;\n"
    "}",
)


# ── 3) Insertar la party card en el panel derecho del modo real, después de Posición real ──
patch(
    "render party card in real-mode right panel",
    "  // Real-mode controls\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\"><h3>Posición real</h3>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetReal74A()\" style=\"width:100%;\">⟲ Reset a Sala 74A</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetSeenReal()\" style=\"width:100%;margin-top:6px;\">⟲ Reset niebla</button>';\n"
    "  html += '</div>';",
    "  // Real-mode controls\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\"><h3>Posición real</h3>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetReal74A()\" style=\"width:100%;\">⟲ Reset a Sala 74A</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetSeenReal()\" style=\"width:100%;margin-top:6px;\">⟲ Reset niebla</button>';\n"
    "  html += '</div>';\n"
    "  // v6b: Party roster card (PCs con HP/AC/posicion/lightBearer)\n"
    "  html += _renderPartyCard();",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
