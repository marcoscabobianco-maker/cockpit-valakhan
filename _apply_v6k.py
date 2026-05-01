"""
v6k patches: Illustrations + Bestiary Barrowmaze integrados al cockpit.

Wildcard mode nocturno:
  - 27 illustrations extraídas del módulo (pages 212-264, ~9 MB).
  - 17 rooms keyed con illustration linkeada (referenciadas por #N en el desc).
  - 120 unique creatures extraídas del campo stats de los rooms.

Pipeline: cp v6j -> v6k, this script.
"""
import io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "prototipo_v6k.html")
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


# 1) title
patch(
    "title",
    "<title>Cockpit V6j — v6j: Rooms re-extracted (clean) + wandering auto-combat + traps DM-strict</title>",
    "<title>Cockpit V6k — v6k: Illustrations del módulo (27) + Bestiario Barrowmaze (120 creatures)</title>",
)

# 2) Helpers loader illustrations + bestiary + modal upgrade
patch(
    "v6k illustrations + bestiary loader",
    "// === v6c: Rooms keyed (244 rooms info) ===\n"
    "const BARROWMAZE_ROOMS_COORDS_SRC = 'maps/barrowmaze_room_coords.json';",
    "// === v6k: Illustrations + Bestiary loaders ===\n"
    "const BARROWMAZE_ILLUSTRATIONS_SRC = 'maps/barrowmaze_illustrations/_index.json';\n"
    "const BARROWMAZE_BESTIARY_SRC = 'maps/barrowmaze_bestiary.json';\n"
    "let _illustrationsCache = null;\n"
    "let _bestiaryCache = null;\n"
    "function dgLoadBarrowmazeExtras() {\n"
    "  return Promise.all([\n"
    "    _illustrationsCache ? Promise.resolve(_illustrationsCache) : fetch(BARROWMAZE_ILLUSTRATIONS_SRC).then(r => r.ok ? r.json() : null).catch(() => null).then(d => { _illustrationsCache = d; return d; }),\n"
    "    _bestiaryCache ? Promise.resolve(_bestiaryCache) : fetch(BARROWMAZE_BESTIARY_SRC).then(r => r.ok ? r.json() : null).catch(() => null).then(d => { _bestiaryCache = d; return d; })\n"
    "  ]);\n"
    "}\n"
    "function dgGetIllustrationsForRoom(rid) {\n"
    "  if (!_illustrationsCache || !_illustrationsCache.room_to_illustration) return [];\n"
    "  return _illustrationsCache.room_to_illustration[rid] || [];\n"
    "}\n"
    "function dgShowBestiaryModal() {\n"
    "  if (!_bestiaryCache || !_bestiaryCache.bestiary) {\n"
    "    dgLoadBarrowmazeExtras().then(() => dgShowBestiaryModal());\n"
    "    return;\n"
    "  }\n"
    "  const b = _bestiaryCache.bestiary;\n"
    "  const sorted = Object.values(b).sort((a, c) => c.appearances.length - a.appearances.length);\n"
    "  let modal = '<div id=\"_dg-bestiary-modal\" style=\"position:fixed;inset:0;background:rgba(0,0,0,0.85);display:flex;align-items:center;justify-content:center;z-index:9999;\" onclick=\"if(event.target===this)this.remove()\">';\n"
    "  modal += '<div style=\"background:var(--bg-2);max-width:740px;width:92%;max-height:85vh;overflow-y:auto;padding:20px;border-radius:8px;border:1px solid var(--border);\">';\n"
    "  modal += '<div style=\"display:flex;align-items:center;gap:8px;margin-bottom:12px;\"><h2 style=\"margin:0;flex:1;\">🜍 Bestiario Barrowmaze ('+sorted.length+' criaturas)</h2><button class=\"btn secondary\" onclick=\"document.getElementById(\\'_dg-bestiary-modal\\').remove()\">✕</button></div>';\n"
    "  modal += '<input type=\"text\" placeholder=\"Filtrar por nombre…\" oninput=\"document.querySelectorAll(\\'#_dg-bestiary-modal .bestiary-row\\').forEach(r=>{r.style.display=r.dataset.name.toLowerCase().includes(this.value.toLowerCase())?\\'\\':\\'none\\'});\" style=\"width:100%;padding:6px 10px;background:var(--bg);color:var(--ink);border:1px solid var(--border);border-radius:4px;margin-bottom:10px;\">';\n"
    "  modal += '<div style=\"display:grid;grid-template-columns:repeat(auto-fill, minmax(220px,1fr));gap:8px;\">';\n"
    "  for (const c of sorted) {\n"
    "    modal += '<div class=\"bestiary-row\" data-name=\"'+escapeHTML(c.name)+'\" style=\"background:rgba(0,0,0,0.25);padding:8px;border-radius:4px;border-left:3px solid #c0392b;\">';\n"
    "    modal += '<div style=\"font-weight:600;font-size:13px;\">'+escapeHTML(c.name)+'</div>';\n"
    "    modal += '<div style=\"font-size:11px;color:var(--ink-dim);margin-top:3px;\">HD '+c.hd+' · AC '+c.ac+' · AL '+c.al+'</div>';\n"
    "    modal += '<div style=\"font-size:10px;color:var(--ink-dim);margin-top:4px;\">En '+c.appearances.length+' sala(s): '+c.appearances.slice(0,8).map(a => a.room).join(', ')+(c.appearances.length > 8 ? '…' : '')+'</div>';\n"
    "    modal += '</div>';\n"
    "  }\n"
    "  modal += '</div></div></div>';\n"
    "  const ex = document.getElementById('_dg-bestiary-modal');\n"
    "  if (ex) ex.remove();\n"
    "  const tmp = document.createElement('div');\n"
    "  tmp.innerHTML = modal;\n"
    "  document.body.appendChild(tmp.firstChild);\n"
    "}\n"
    "\n"
    "// === v6c: Rooms keyed (244 rooms info) ===\n"
    "const BARROWMAZE_ROOMS_COORDS_SRC = 'maps/barrowmaze_room_coords.json';",
)

# 3) Trigger load on real-mode entry
patch(
    "v6k extras load on real-mode",
    "    if (typeof dgLoadRoomsData === 'function') dgLoadRoomsData().then(() => { if (typeof redrawGridRealCanvas === 'function') redrawGridRealCanvas(); }).catch(()=>{});",
    "    if (typeof dgLoadRoomsData === 'function') dgLoadRoomsData().then(() => { if (typeof redrawGridRealCanvas === 'function') redrawGridRealCanvas(); }).catch(()=>{});\n"
    "    if (typeof dgLoadBarrowmazeExtras === 'function') dgLoadBarrowmazeExtras().catch(()=>{});",
)

# 4) Modal de room: mostrar illustrations linkeadas si hay
patch(
    "v6k modal with illustrations",
    "  if (pos) modal += '<div style=\"font-size:11px;color:var(--ink-dim);\">Coords SVG (800w): ('+pos.x+', '+pos.y+')</div>';\n"
    "  modal += '<div style=\"display:flex;gap:8px;margin-top:12px;\">';",
    "  // v6k: illustrations linkeadas\n"
    "  if (typeof dgGetIllustrationsForRoom === 'function') {\n"
    "    const ills = dgGetIllustrationsForRoom(rid);\n"
    "    if (ills.length) {\n"
    "      modal += '<div style=\"margin-top:12px;padding:8px;background:rgba(93,173,226,0.12);border-radius:6px;border-left:3px solid #5dade2;\">';\n"
    "      modal += '<b>🖼 Illustration(es) del módulo:</b>';\n"
    "      for (const il of ills) {\n"
    "        modal += '<div style=\"margin-top:8px;\"><img src=\"'+il.url+'\" alt=\"Illustration #'+il.num+'\" style=\"max-width:100%;border-radius:4px;border:1px solid var(--border);cursor:zoom-in;\" onclick=\"window.open(this.src, _blank);\"></div>';\n"
    "        modal += '<div style=\"font-size:11px;color:var(--ink-dim);text-align:center;margin-top:2px;\">Illustration #'+il.num+' (click para abrir tamaño completo)</div>';\n"
    "      }\n"
    "      modal += '</div>';\n"
    "    }\n"
    "  }\n"
    "  if (pos) modal += '<div style=\"font-size:11px;color:var(--ink-dim);margin-top:8px;\">Coords SVG (800w): ('+pos.x+', '+pos.y+')</div>';\n"
    "  modal += '<div style=\"display:flex;gap:8px;margin-top:12px;\">';",
)

# 5) Botón "🜍 Bestiario" en quick refs card
patch(
    "v6k bestiary button in quick refs",
    "  html += '<button class=\"btn secondary\" onclick=\"dgPromptSaveAll()\" style=\"width:100%;margin-top:6px;\">🎲 Tirar saves automáticos (todos / vanguardia)</button>';",
    "  html += '<button class=\"btn secondary\" onclick=\"dgPromptSaveAll()\" style=\"width:100%;margin-top:6px;\">🎲 Tirar saves automáticos (todos / vanguardia)</button>';\n"
    "  html += '<button class=\"btn secondary\" onclick=\"dgShowBestiaryModal()\" style=\"width:100%;margin-top:6px;\">🜍 Bestiario Barrowmaze (120 criaturas)</button>';",
)

with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nApplied {len(patches)} patches")
print(f"Wrote: {TARGET}")
print(f"Size: {os.path.getsize(TARGET)} bytes (was {original_len})")
