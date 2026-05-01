"""
v6e patches: Polish final del wildcard mode.

Wildcard mode delivery #5 (final, acumulativo).

Changes:
  - title v6e
  - Link rapido a /tools/ ACKS Assistant en el panel derecho del modo real
    (boton "🛠 ACKS Assistant" abre tools en nueva pestana).
  - Mini-card "Quick refs ACKS" con valores comunes:
    * Movement (exploration / encounter / running)
    * Light (torch / lantern radius)
    * Search / Listen (1 turn / 1 round, 1d6=1)
    * Save targets generic level 1 (P/P 15+, B 17+, P/D 14+, R/R/W 12+, S/S/S 16+)
  - Recordatorio de atajos de teclado en algun lugar visible.

Pipeline: cp v6d -> v6e, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6e.html")
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
    "<title>Cockpit V6d — v6d: Trampas place + detect + trigger sobre el grid</title>",
    "<title>Cockpit V6e — v6e: Wildcard polish (ACKS Assistant link + Quick refs + atajos)</title>",
)


# ── 2) Quick refs ACKS card + ACKS Assistant link en el panel derecho ──
patch(
    "v6e quick refs + ACKS link",
    "  // v5z: Tracker visual con time-of-day + progress bars + raciones + long rest\n",
    "  // v6e: Quick refs ACKS card + ACKS Assistant link\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>🛠 ACKS Quick Refs</h3>';\n"
    "  html += '<div style=\"font-size:11px;line-height:1.7;color:var(--ink);\">';\n"
    "  html += '<div><b>Movement</b>: Exploration 120ft/turn (10min) · Combat 40ft/round (10s) · Running 120ft/round.</div>';\n"
    "  html += '<div><b>Light</b>: Torch 30ft/6 turns · Lantern 30ft/24 turns (1 oil flask) · Infravision 60ft (racial).</div>';\n"
    "  html += '<div><b>Search</b> (10×10): 1 turn · find: 1d6 1-2 elf 1 otros.</div>';\n"
    "  html += '<div><b>Listen</b>: 1 round · 1d6 1-3 thief 1-2 demi 1 humano.</div>';\n"
    "  html += '<div><b>Wandering</b>: 1d6 cada 2 turns · 1 = encuentro (Barrowmaze: tabla del módulo).</div>';\n"
    "  html += '<div><b>Surprise</b>: 1d6 c/lado · 1-2 sorprendido (skip 1° round).</div>';\n"
    "  html += '<div><b>Reaction</b>: 2d6+Cha · 2 hostile · 3-5 unfriendly · 6-8 uncertain · 9-11 friendly · 12 amicable.</div>';\n"
    "  html += '<div><b>Saves L1</b> (target d20≥): P/P 15 · B 17 · P/D 14 · R/R/W 12 · S/S/S 16.</div>';\n"
    "  html += '<div><b>Distance</b>: 1d6×10 ft (dungeon) · 2d4×10 yards (open).</div>';\n"
    "  html += '</div>';\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:8px 0;\">';\n"
    "  html += '<a class=\"btn\" href=\"/tools/\" target=\"_blank\" rel=\"noopener\" style=\"display:inline-block;text-decoration:none;width:100%;text-align:center;\">🛠 Abrir ACKS Assistant (spells, bestiary, treasure, mortal wounds…)</a>';\n"
    "  html += '<div style=\"font-size:10px;color:var(--ink-dim);margin-top:6px;\">Atajos: <kbd>WASD</kbd>/flechas mover · <kbd>G</kbd> toggle DM · <kbd>T</kbd> +1 turno · <kbd>shift+click</kbd> trampa</div>';\n"
    "  html += '</div>';\n"
    "  // v5z: Tracker visual con time-of-day + progress bars + raciones + long rest\n"
    "  html += '<div class=\"card\" style=\"padding:10px;\">';\n"
    "  html += '<h3>🛠 ACKS Quick Refs</h3>';\n"
    "  html += '<div style=\"font-size:11px;line-height:1.7;color:var(--ink);\">';\n"
    "  html += '<div><b>Movement</b>: Exploration 120ft/turn (10min) · Combat 40ft/round (10s) · Running 120ft/round.</div>';\n"
    "  html += '<div><b>Light</b>: Torch 30ft/6 turns · Lantern 30ft/24 turns (1 oil flask) · Infravision 60ft (racial).</div>';\n"
    "  html += '<div><b>Search</b> (10×10): 1 turn · find: 1d6 1-2 elf 1 otros.</div>';\n"
    "  html += '<div><b>Listen</b>: 1 round · 1d6 1-3 thief 1-2 demi 1 humano.</div>';\n"
    "  html += '<div><b>Wandering</b>: 1d6 cada 2 turns · 1 = encuentro (Barrowmaze: tabla del módulo).</div>';\n"
    "  html += '<div><b>Surprise</b>: 1d6 c/lado · 1-2 sorprendido (skip 1° round).</div>';\n"
    "  html += '<div><b>Reaction</b>: 2d6+Cha · 2 hostile · 3-5 unfriendly · 6-8 uncertain · 9-11 friendly · 12 amicable.</div>';\n"
    "  html += '<div><b>Saves L1</b> (target d20≥): P/P 15 · B 17 · P/D 14 · R/R/W 12 · S/S/S 16.</div>';\n"
    "  html += '<div><b>Distance</b>: 1d6×10 ft (dungeon) · 2d4×10 yards (open).</div>';\n"
    "  html += '</div>';\n"
    "  html += '<hr style=\"border:none;border-top:1px solid var(--border);margin:8px 0;\">';\n"
)


# Save
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
