"""
v6g patches: Saves automatizados ACKS + Mortal Wounds inline.

Wildcard mode delivery #7.

Changes:
  - ACKS_SAVES_L1 table por categoria de clase (Fighter / Mage / Cleric / Thief /
    Dwarf / Elf / Halfling). Targets d20 ≥ X para save success.
  - _classifyPC(class_string) → categoria base ACKS.
  - dgRollSave(pcId, saveType): tira 1d20, compara contra target del PC, loguea.
  - dgRollSaveAll(saveType, position?): tira save para PCs en posicion (default: vanguardia).
  - Tabla Mortal Wounds simplificada (1d20 + level + ConMod):
    1-9 dead, 10-13 out 1d3w, 14-15 serious -1, 16-17 serious 1d6d, 18 light 1d6h,
    19+ superficial.
  - dgRollMortalWound(pcId): tira tabla, marca PC con condition + log.
  - Hook: cuando dgPCHpDelta lleva HP a 0 → auto-trigger Mortal Wound roll.
  - Botón en trap-triggered banner: "Tirar saves vanguardia".

Pipeline: cp v6f -> v6g, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6g.html")
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
    "<title>Cockpit V6f — v6f: Arden Vul multi-level viewer (27 levels, 1293 rooms OCR)</title>",
    "<title>Cockpit V6g — v6g: Saves automatizados ACKS + Mortal Wounds inline</title>",
)


# ── 2) Helpers saves + MW. Insertar después de _renderPartyCard ──
patch(
    "v6g saves+MW helpers",
    "  html += '<div style=\"font-size:10px;color:var(--ink-dim);margin-top:6px;line-height:1.4;\">PCs muertos/missing no se muestran. Botones: <b>−1/+1</b> ajuste manual, <b>−1d6</b> tirada de daño, <b>select</b> posición, <b>🔥</b> portador de luz (toggle).</div>';\n"
    "  html += '</div>';\n"
    "  return html;\n"
    "}",
    "  html += '<div style=\"font-size:10px;color:var(--ink-dim);margin-top:6px;line-height:1.4;\">PCs muertos/missing no se muestran. Botones: <b>−1/+1</b> ajuste manual, <b>−1d6</b> tirada de daño, <b>select</b> posición, <b>🔥</b> portador de luz (toggle).</div>';\n"
    "  html += '</div>';\n"
    "  return html;\n"
    "}\n"
    "\n"
    "// === v6g: ACKS Saves automatizados + Mortal Wounds inline ===\n"
    "// Saves L1 por categoria de clase. Target = d20 >= X.\n"
    "// Categorias: P/P (Petrification & Paralysis), B (Breath), P/D (Poison & Death),\n"
    "//             R/R/W (Rods/Staves/Wands), S/S/S (Spells/Staves/Spells)\n"
    "const ACKS_SAVES_L1 = {\n"
    "  fighter:  { P:15, B:17, D:14, R:12, S:16 },\n"
    "  mage:     { P:13, B:16, D:11, R:14, S:12 },\n"
    "  cleric:   { P:11, B:16, D:12, R:14, S:13 },\n"
    "  thief:    { P:13, B:16, D:13, R:14, S:14 },\n"
    "  dwarf:    { P:11, B:13, D:12, R:12, S:14 },\n"
    "  elf:      { P:13, B:16, D:13, R:14, S:15 },\n"
    "  halfling: { P:13, B:13, D:13, R:12, S:14 }\n"
    "};\n"
    "// Save type aliases (lowercase short → table key)\n"
    "const SAVE_TYPE_MAP = {\n"
    "  petrify:'P', petrification:'P', paralyze:'P', paralysis:'P', petrification_paralysis:'P', 'p/p':'P', p:'P',\n"
    "  breath:'B', breath_attack:'B', b:'B',\n"
    "  poison:'D', death:'D', poison_death:'D', 'p/d':'D', d:'D',\n"
    "  rod:'R', staff:'R', wand:'R', 'r/r/w':'R', r:'R',\n"
    "  spell:'S', spells:'S', 's/s/s':'S', s:'S'\n"
    "};\n"
    "function _classifyPC(pcClass) {\n"
    "  const c = String(pcClass||'').toLowerCase();\n"
    "  if (c.includes('mage') || c.includes('warlock') || c.includes('magic-user') || c.includes('wizard')) return 'mage';\n"
    "  if (c.includes('cleric') || c.includes('crusader') || c.includes('shaman') || c.includes('druid')) return 'cleric';\n"
    "  if (c.includes('thief') || c.includes('assassin') || c.includes('explorer') || c.includes('ranger')) return 'thief';\n"
    "  if (c.includes('dwarf') || c.includes('vaultguard')) return 'dwarf';\n"
    "  if (c.includes('elf') || c.includes('elven')) return 'elf';\n"
    "  if (c.includes('halfling')) return 'halfling';\n"
    "  // default fighter (Tank, Archer, generic Fighter, Crusader-like, etc)\n"
    "  return 'fighter';\n"
    "}\n"
    "function _saveTargetFor(pcId, saveType) {\n"
    "  const pcs = _getPCList();\n"
    "  const pc = pcs.find(p => p.id === pcId);\n"
    "  if (!pc) return null;\n"
    "  const cat = _classifyPC(pc.class);\n"
    "  const tbl = ACKS_SAVES_L1[cat];\n"
    "  if (!tbl) return null;\n"
    "  const key = SAVE_TYPE_MAP[String(saveType).toLowerCase()] || saveType.toUpperCase()[0];\n"
    "  const base = tbl[key];\n"
    "  if (base == null) return null;\n"
    "  // Level adjustment: every 4 levels, save targets improve by 2 (lower target)\n"
    "  const lvl = pc.level || 1;\n"
    "  const adj = Math.floor((lvl - 1) / 4) * 2;\n"
    "  return { target: Math.max(2, base - adj), category: cat, key };\n"
    "}\n"
    "function dgRollSave(pcId, saveType) {\n"
    "  const info = _saveTargetFor(pcId, saveType);\n"
    "  if (!info) { logEvent('⚠ Sin tabla de save para '+_getPCName(pcId)+' / '+saveType); renderEventLog(); return null; }\n"
    "  const r = rollDie(20);\n"
    "  const success = r >= info.target;\n"
    "  const sign = success ? '✓' : '✗';\n"
    "  const color = success ? 'success' : 'fail';\n"
    "  logEvent(sign+' Save '+info.key+' · '+_getPCName(pcId)+' ('+info.category+') · 1d20='+r+' vs '+info.target+' → '+(success ? 'PASA' : 'FALLA'));\n"
    "  renderEventLog();\n"
    "  return { pcId, success, roll: r, target: info.target, category: info.category };\n"
    "}\n"
    "function dgRollSaveAll(saveType, positionFilter) {\n"
    "  const pcs = _getPCList().filter(p => p.alive !== false);\n"
    "  const results = [];\n"
    "  let lines = ['🎲 Save '+saveType+' — Tiradas:'];\n"
    "  for (const pc of pcs) {\n"
    "    if (positionFilter && state.dungeon && state.dungeon.partyState) {\n"
    "      const ps = state.dungeon.partyState[pc.id];\n"
    "      if (!ps || ps.position !== positionFilter) continue;\n"
    "    }\n"
    "    const info = _saveTargetFor(pc.id, saveType);\n"
    "    if (!info) continue;\n"
    "    const r = rollDie(20);\n"
    "    const success = r >= info.target;\n"
    "    results.push({ pcId: pc.id, name: pc.name, success, roll: r, target: info.target });\n"
    "    lines.push((success ? '  ✓ ' : '  ✗ ') + pc.name + ' (' + info.category + '): 1d20='+r+' vs '+info.target+' → '+(success ? 'PASA' : 'FALLA'));\n"
    "  }\n"
    "  if (!results.length) { alert('No hay PCs alcanzados por la save (filtro position='+positionFilter+').'); return; }\n"
    "  for (const l of lines) logEvent(l);\n"
    "  renderEventLog();\n"
    "  alert(lines.join('\\n'));\n"
    "  return results;\n"
    "}\n"
    "function dgPromptSaveAll() {\n"
    "  const t = prompt('Tipo de save (P=petrify, B=breath, D=poison, R=rod/staff/wand, S=spells):', 'B');\n"
    "  if (!t) return;\n"
    "  const pos = prompt('Posición a tirar (vanguard / middle / rear) o vacío para todos:', 'vanguard');\n"
    "  dgRollSaveAll(t, pos || null);\n"
    "}\n"
    "\n"
    "// Mortal Wounds simplified table (1d20 + level + ConMod)\n"
    "const MORTAL_WOUNDS = [\n"
    "  { range:[Number.NEGATIVE_INFINITY, 9], result:'☠ MUERTO', desc:'Death. The PC is dead.', recover:null, color:'#000' },\n"
    "  { range:[10,11], result:'☠ Inconsciente — 1d3 semanas', desc:'Catastrophic wound. Bedrest 1d3 weeks. Recovers to 1 HP.', recover:'1d3 weeks', color:'#922b21' },\n"
    "  { range:[12,13], result:'⚠ Wounded grave — 1d3 semanas', desc:'Serious wound, possible permanent disability. Recovers in 1d3 weeks.', recover:'1d3 weeks', color:'#c0392b' },\n"
    "  { range:[14,15], result:'⚠ Wounded -1 — 1d3 semanas', desc:'Serious wound: -1 to-hit/-1 dmg until full rest. 1d3 weeks recovery.', recover:'1d3 weeks', color:'#e67e22' },\n"
    "  { range:[16,17], result:'➖ Wound — 1d6 días', desc:'Recovers fully in 1d6 days bedrest.', recover:'1d6 days', color:'#f39c12' },\n"
    "  { range:[18,18], result:'✱ Light wound — 1d6 horas', desc:'Light wound. Full recovery in 1d6 hours of rest.', recover:'1d6 hours', color:'#f1c40f' },\n"
    "  { range:[19,Number.POSITIVE_INFINITY], result:'✓ Superficial', desc:'Mostly cosmetic. Recovers immediately to 1 HP.', recover:'immediate', color:'#7ee787' }\n"
    "];\n"
    "function dgRollMortalWound(pcId) {\n"
    "  const pcs = _getPCList();\n"
    "  const pc = pcs.find(p => p.id === pcId);\n"
    "  if (!pc) return;\n"
    "  // ACKS: roll 1d20 + level + ConMod (we don't have Con mod, default 0)\n"
    "  const r = rollDie(20);\n"
    "  const lvl = pc.level || 1;\n"
    "  const conMod = 0; // TODO: read from pc.attrs if available\n"
    "  const total = r + lvl + conMod;\n"
    "  const entry = MORTAL_WOUNDS.find(e => total >= e.range[0] && total <= e.range[1]);\n"
    "  const ps = state.dungeon && state.dungeon.partyState && state.dungeon.partyState[pcId];\n"
    "  if (ps) {\n"
    "    if (!ps.conditions) ps.conditions = [];\n"
    "    ps.conditions.push({ type:'mortal_wound', detail: entry.result, recover: entry.recover, at: state.dungeon.turns||0 });\n"
    "    if (entry.range[0] <= 9) {\n"
    "      // dead\n"
    "      const idx = pcs.findIndex(p => p.id === pcId);\n"
    "      // We don't mutate CAMPAIGNS.pcs, just mark in partyState\n"
    "      ps.dead = true;\n"
    "    }\n"
    "  }\n"
    "  saveState();\n"
    "  logEvent('💀 Mortal Wound: '+pc.name+' · 1d20='+r+' +lvl '+lvl+' +Con '+conMod+' = '+total+' → '+entry.result);\n"
    "  renderEventLog();\n"
    "  // Show modal with description\n"
    "  let modal = '<div id=\"_dg-mw-modal\" style=\"position:fixed;inset:0;background:rgba(0,0,0,0.85);display:flex;align-items:center;justify-content:center;z-index:9999;\" onclick=\"if(event.target===this)this.remove()\">';\n"
    "  modal += '<div style=\"background:var(--bg-2);max-width:480px;width:90%;padding:20px;border-radius:8px;border:3px solid '+entry.color+';\">';\n"
    "  modal += '<h2 style=\"margin-top:0;color:'+entry.color+';\">💀 Mortal Wound — '+escapeHTML(pc.name)+'</h2>';\n"
    "  modal += '<div style=\"font-size:13px;line-height:1.6;\">';\n"
    "  modal += '<div><b>Tirada</b>: 1d20=<b>'+r+'</b> + lvl '+lvl+' + Con '+conMod+' = <b>'+total+'</b></div>';\n"
    "  modal += '<div style=\"margin:8px 0;font-size:18px;font-weight:bold;color:'+entry.color+';\">'+entry.result+'</div>';\n"
    "  modal += '<div style=\"margin:8px 0;\">'+escapeHTML(entry.desc)+'</div>';\n"
    "  if (entry.recover && entry.recover !== 'immediate') modal += '<div style=\"margin:8px 0;font-style:italic;color:var(--ink-dim);\">⏱ Recovery: '+entry.recover+'</div>';\n"
    "  modal += '</div>';\n"
    "  modal += '<div style=\"margin-top:12px;\"><button class=\"btn\" onclick=\"document.getElementById(\\'_dg-mw-modal\\').remove()\">Cerrar</button></div>';\n"
    "  modal += '</div></div>';\n"
    "  const existing = document.getElementById('_dg-mw-modal');\n"
    "  if (existing) existing.remove();\n"
    "  const tmp = document.createElement('div');\n"
    "  tmp.innerHTML = modal;\n"
    "  document.body.appendChild(tmp.firstChild);\n"
    "}",
)


# ── 3) Hook en dgPCHpDelta para auto-trigger Mortal Wound ──
patch(
    "v6g auto MW on hp 0",
    "  if (delta < 0 && ps.hp === 0 && before > 0) {\n"
    "    logEvent('💀 '+_getPCName(pcId)+' a 0 HP — Mortal Wound table required (consultar /tools/ ACKS Assistant).');\n"
    "  } else if (delta < 0) {",
    "  if (delta < 0 && ps.hp === 0 && before > 0) {\n"
    "    logEvent('💀 '+_getPCName(pcId)+' a 0 HP — tirando Mortal Wound...');\n"
    "    if (typeof dgRollMortalWound === 'function') setTimeout(() => dgRollMortalWound(pcId), 100);\n"
    "  } else if (delta < 0) {",
)


# ── 4) Banner trap-triggered: agregar boton "Saves all" ──
patch(
    "v6g trap banner saves button",
    "      for (const t of triggered) {\n"
    "        alerts.push({color:'#c0392b', emoji:'💥', msg:'<b>TRAMPA DISPARADA</b> en cell ('+t.x+','+t.y+'): '+escapeHTML(t.desc)+'. <b>Save vs '+escapeHTML(t.saveType||'?')+'</b>. Aplicar daño con −1d6 sobre PCs vanguardia o usar el roster.', action:'dgResolveTrap('+t.x+','+t.y+')', actionLabel:'Resolver'});\n"
    "      }",
    "      for (const t of triggered) {\n"
    "        const _saveLetter = (t.saveType||'B').toString().toUpperCase()[0];\n"
    "        alerts.push({color:'#c0392b', emoji:'💥', msg:'<b>TRAMPA DISPARADA</b> en cell ('+t.x+','+t.y+'): '+escapeHTML(t.desc)+'. <b>Save vs '+escapeHTML(t.saveType||'?')+'</b>. Auto-tirar saves con boton, o aplicar daño manual con roster.', action:'dgResolveTrap('+t.x+','+t.y+')', actionLabel:'Resolver'});\n"
    "        alerts.push({color:'#7d2828', emoji:'🎲', msg:'Tirar saves automáticos para PCs en vanguardia: 1d20 vs save '+_saveLetter+' del PC (segun clase + level).', action:'dgRollSaveAll(\\''+_saveLetter+'\\', \\'vanguard\\')', actionLabel:'Saves vanguardia'});\n"
    "      }",
)


# ── 5) Boton "Saves todos" en quick refs card ──
patch(
    "v6g saves button in quick refs",
    "  html += '<a class=\"btn\" href=\"/tools/\" target=\"_blank\" rel=\"noopener\" style=\"display:inline-block;text-decoration:none;width:100%;text-align:center;\">🛠 Abrir ACKS Assistant (spells, bestiary, treasure, mortal wounds…)</a>';",
    "  html += '<a class=\"btn\" href=\"/tools/\" target=\"_blank\" rel=\"noopener\" style=\"display:inline-block;text-decoration:none;width:100%;text-align:center;\">🛠 Abrir ACKS Assistant (spells, bestiary, treasure, mortal wounds…)</a>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgPromptSaveAll()\" style=\"width:100%;margin-top:6px;\">🎲 Tirar saves automáticos (todos / vanguardia)</button>';",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
