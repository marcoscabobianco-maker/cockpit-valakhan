"""
v6h patches: Search & Listen integrados al grid con tirada por clase ACKS.

Wildcard mode delivery #8 (final).

Changes:
  - dgSearchRoom(): tira 1d6 vs threshold según clase del PC vanguardia.
    Threshold: thief/explorer 1-2 (find traps + secret doors), elf/demi 1-2,
    otros 1. Consume 1 turn (calls dgAdvance).
  - dgListenAtDoor(): tira 1d6 vs threshold según clase del PC adelante.
    Threshold: thief 1-3, demi-human (dwarf/elf/halfling) 1-2, humano 1.
    NO consume turn (1 round = 10 sec).
  - Botón "🔍 Search room (1t)" y "👂 Listen at door (1r)" en tracker card.
  - Resultado loguea + alerta breve en pantalla.
  - Si vanguardia hay thief, mejor threshold automáticamente.

Pipeline: cp v6g -> v6h, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6h.html")
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
    "<title>Cockpit V6g — v6g: Saves automatizados ACKS + Mortal Wounds inline</title>",
    "<title>Cockpit V6h — v6h: Search/Listen integrados (tirada por clase ACKS)</title>",
)


# ── 2) Helpers Search & Listen. Insertar después de dgPromptSaveAll ──
patch(
    "v6h search+listen helpers",
    "function dgPromptSaveAll() {\n"
    "  const t = prompt('Tipo de save (P=petrify, B=breath, D=poison, R=rod/staff/wand, S=spells):', 'B');\n"
    "  if (!t) return;\n"
    "  const pos = prompt('Posición a tirar (vanguard / middle / rear) o vacío para todos:', 'vanguard');\n"
    "  dgRollSaveAll(t, pos || null);\n"
    "}",
    "function dgPromptSaveAll() {\n"
    "  const t = prompt('Tipo de save (P=petrify, B=breath, D=poison, R=rod/staff/wand, S=spells):', 'B');\n"
    "  if (!t) return;\n"
    "  const pos = prompt('Posición a tirar (vanguard / middle / rear) o vacío para todos:', 'vanguard');\n"
    "  dgRollSaveAll(t, pos || null);\n"
    "}\n"
    "\n"
    "// === v6h: Search & Listen con tirada por clase ACKS ===\n"
    "function _bestPcAtPosition(position) {\n"
    "  const pcs = _getPCList().filter(p => p.alive !== false);\n"
    "  const partyState = (state.dungeon && state.dungeon.partyState) || {};\n"
    "  return pcs.find(p => {\n"
    "    const ps = partyState[p.id];\n"
    "    return ps && ps.position === position;\n"
    "  }) || pcs[0];  // fallback al primer PC alive\n"
    "}\n"
    "function _searchThreshold(pc) {\n"
    "  if (!pc) return 1;\n"
    "  const c = String(pc.class||'').toLowerCase();\n"
    "  // ACKS: find secret door 1-2 elf, 1 otros · find trap 1-2 thief+det skill, 1 otros\n"
    "  // Combinado pragmatico: 1-2 thief/explorer/elf/demi-human, 1 humano\n"
    "  if (c.includes('thief') || c.includes('assassin') || c.includes('explorer') || c.includes('ranger') ||\n"
    "      c.includes('elf') || c.includes('dwarf') || c.includes('halfling') || c.includes('vaultguard')) return 2;\n"
    "  return 1;\n"
    "}\n"
    "function _listenThreshold(pc) {\n"
    "  if (!pc) return 1;\n"
    "  const c = String(pc.class||'').toLowerCase();\n"
    "  // ACKS: hear noise 1-3 thief/assassin, 1-2 dwarf/elf/halfling, 1 humano\n"
    "  if (c.includes('thief') || c.includes('assassin')) return 3;\n"
    "  if (c.includes('elf') || c.includes('dwarf') || c.includes('halfling') || c.includes('vaultguard') || c.includes('explorer') || c.includes('ranger')) return 2;\n"
    "  return 1;\n"
    "}\n"
    "function dgSearchRoom() {\n"
    "  if (!state.dungeon) { alert('No hay dungeon activo'); return; }\n"
    "  const pc = _bestPcAtPosition('vanguard') || _getPCList().find(p => p.alive !== false);\n"
    "  if (!pc) { alert('No hay PCs en el party'); return; }\n"
    "  const thr = _searchThreshold(pc);\n"
    "  const r = rollDie(6);\n"
    "  const success = r <= thr;\n"
    "  const msg = '🔍 SEARCH (' + pc.name + ' / vanguardia): 1d6=' + r + ' vs ≤' + thr + ' → ' + (success ? '✓ ENCUENTRA algo' : '✗ Nada visible');\n"
    "  logEvent(msg);\n"
    "  // Consume 1 turn\n"
    "  if (typeof dgAdvance === 'function') dgAdvance();\n"
    "  renderEventLog();\n"
    "  if (typeof renderGridCrawler === 'function' && state.dungeonView === 'grid') renderGridCrawler();\n"
    "  alert(msg + (success ? '\\n\\nDM: revelar lo encontrado (trap, secret door, escondite, etc).' : '\\n\\nLos PCs no detectaron nada en esta búsqueda. Pueden buscar de nuevo (consume otro turno).'));\n"
    "}\n"
    "function dgListenAtDoor() {\n"
    "  if (!state.dungeon) { alert('No hay dungeon activo'); return; }\n"
    "  const pc = _bestPcAtPosition('vanguard') || _getPCList().find(p => p.alive !== false);\n"
    "  if (!pc) { alert('No hay PCs en el party'); return; }\n"
    "  const thr = _listenThreshold(pc);\n"
    "  const r = rollDie(6);\n"
    "  const success = r <= thr;\n"
    "  const msg = '👂 LISTEN AT DOOR (' + pc.name + '): 1d6=' + r + ' vs ≤' + thr + ' → ' + (success ? '✓ ESCUCHA algo' : '✗ Silencio');\n"
    "  logEvent(msg);\n"
    "  // Listen no consume turn (1 round = 10 sec)\n"
    "  renderEventLog();\n"
    "  alert(msg + (success ? '\\n\\nDM: describir el sonido (voces, pasos, gemidos, agua, etc).' : '\\n\\nNo se escucha nada del otro lado. Pueden volver a escuchar (sin costo).'));\n"
    "}",
)


# ── 3) Botones Search & Listen en tracker card ──
patch(
    "v6h search+listen buttons in tracker",
    "  html += '<button class=\"btn secondary\" onclick=\"gridLightTorch()\">🔥 Encender antorcha</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgWanderingCheck()\">🎲 Wandering check</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridAddNoise()\">🔊 Ruido +1</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetTime()\">⟲ Reset pasos</button>';\n"
    "  html += '<span></span>';\n"
    "  html += '</div>';",
    "  html += '<button class=\"btn secondary\" onclick=\"gridLightTorch()\">🔥 Encender antorcha</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgWanderingCheck()\">🎲 Wandering check</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridAddNoise()\">🔊 Ruido +1</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"gridResetTime()\">⟲ Reset pasos</button>';\n"
    "  // v6h: Search & Listen\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgSearchRoom()\" title=\"1d6 vs clase del PC vanguardia. Consume 1 turno.\">🔍 Search room (1t)</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgListenAtDoor()\" title=\"1d6 vs clase del PC vanguardia. No consume turno.\">👂 Listen door (1r)</button>';\n"
    "  html += '</div>';",
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
