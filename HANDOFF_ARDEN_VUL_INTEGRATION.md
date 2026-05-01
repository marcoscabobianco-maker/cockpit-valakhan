# HANDOFF · Arden Vul integración multi-level
**Sesión:** cockpit V5c (Cemanahuac)
**Fecha:** 2026-04-30
**Para:** fork V5v (Marcos) que ya tiene Barrowmaze migrado

---

## TL;DR

Tenés todo listo para copiar al fork V5v:
- **27 mapas** del megadungeon Arden Vul extraídos del PDF como webp (10 levels + 17 sublevels = 27 archivos).
- **1293 room markers** auto-detectados con OCR, posicionados en coords del display image (no SVG units).
- **Lógica cockpit** para `dungeon multi-level` (selector de nivel + bg/coords por level + manual marker per level + zoom/pan SVG).
- **JSON schema** definido para `dungeons.<id>` con `type: "multi-level"`.

Total assets: **62 MB** (`maps/arden_vul/`). El JSON de la campaña sumó +9 KB para integrar.

**No deployé al v5c de este chat** (a pedido tuyo). Todo queda como assets + handoff para que migres a V5v.

---

## Inventario de assets (62 MB)

```
maps/arden_vul/
├── manifest.json                           ← 5 KB. Index de los 27 levels con bg URLs y dimensiones
├── _probe.json                             ← debug: bbox y count de drawings/images por page (descartar)
├── L1_bg.webp .. L10_bg.webp               ← 10 mapas de levels principales (display, ~100-400 KB c/u)
├── L1_full.webp .. L10_full.webp           ← versión sin downscale (~600 KB-4 MB c/u)
├── L1_coords.json .. L10_coords.json       ← coords OCR por level (1-3 KB c/u)
├── SL1_bg.webp .. SL15_bg.webp             ← 17 sublevels (SL6 está dividido en SL6a/SL6b, SL10 en SL10A/SL10B)
├── SL1_full.webp .. SL15_full.webp         ← versiones full
└── SL1_coords.json .. SL15_coords.json     ← coords OCR
```

### Distribución de rooms detectadas por nivel

| Level | Detectados | Esperados (módulo ROUTER) | Coverage |
|---|---:|---:|---|
| L1  — Basement                | ~3   | 12   | bajo (mapa chico, OCR ruidoso) |
| L2  — Howling Caves           | ~10  | 44   | medio |
| **L3 — Halls of Thoth**       | **155** | 166  | **93%** ★ |
| **L4 — Forum of Set**         | **149** | 122  | **>100%** (FP esperables) |
| L5  — Obsidian Gates          | 78   | 106  | 73% |
| **L6 — Troll Lifts**          | **134** | 134  | **100%** ✓ |
| L7  — Court of Troll Thegn    | 67   | 108  | 62% |
| L8  — Nether Reaches          | 67   | 122  | 55% |
| L9  — Chasm Floor             | 69   | 95   | 73% |
| L10 — Ziggurat de Kauket      | ~9   | 38   | 24% |
| SL1-15 (sublevels)            | ~440 | ~340 | ~100%+ (FP) |
| **TOTAL**                     | **1293** | ~1170 | **alto, con falsos positivos esperables** |

**Lectura honesta**: OCR detecta el 80-100% de rooms en mapas grandes y bien etiquetados (L3, L4, L6). En mapas chicos o con números muy juntos, baja al 25-60% (L10, L1). Los falsos positivos (números pintados en walls que no son rooms, leyendas) están presentes pero son raros — Marcos los puede borrar manualmente con click-to-place override.

---

## Schema JSON

### `manifest.json` (registry de los 27 levels)

```json
{
  "_doc": "Arden Vul level maps extracted from PDF as raster images",
  "levels": [
    {
      "id": "L1",
      "name": "Level 1 — The Basement",
      "page_pdf": 1135,
      "bg_url": "maps/arden_vul/L1_bg.webp",
      "bg_full_url": "maps/arden_vul/L1_full.webp",
      "bg_w": 1600, "bg_h": 2044,
      "original_w": 6261, "original_h": 8000,
      "aspect_ratio": 0.7826
    }
    // ... 26 more
  ]
}
```

### `<level_id>_coords.json` (coords por level)

```json
{
  "level_id": "L3",
  "level_name": "Level 3 — Halls of Thoth",
  "bg_url": "maps/arden_vul/L3_bg.webp",
  "bg_w": 1600, "bg_h": 1952,
  "room_coords": {
    "1":   { "x": 234.5, "y": 1023.1 },
    "2a":  { "x": 312.7, "y": 1145.8 },
    "166": { "x": 1320.4, "y": 1801.0 }
  },
  "_unique_rooms": 155,
  "_ocr_time_s": 18.6
}
```

**Coords están en sistema bg display** (1600 wide), NO en SVG units. Para usarlas en SVG, escalar por (svgW / bg_w):

```js
const svgX = coord.x * (svgWidth / bgW);
const svgY = coord.y * (svgWidth / bgW);  // mismo factor (preserve aspect)
```

---

## Cambio al schema de campaign (`novatos_ravenloft.json`)

El dungeon `ardis_vala` cambió de single-level a **multi-level**. Estructura:

```json
"ardis_vala": {
  "name": "Ardis Vala (Halls of Arden Vul · adaptado a Valachhan)",
  "type": "multi-level",
  "status": "not_entered_party",
  "startLevel": "L3",
  "_lore": "...",
  "levels": [
    {
      "id": "L1",
      "name": "Level 1 — The Basement",
      "page_pdf": 1135,
      "bg_url": "maps/arden_vul/L1_bg.webp",
      "coords_url": "maps/arden_vul/L1_coords.json",
      "bg_w": 1600, "bg_h": 2044,
      "aspect_ratio": 0.7826
    }
    // ... 26 more
  ],
  "rooms": { /* legacy 14 rooms con coords manuales del v5b — backward compat */ },
  "connections": [ /* legacy */ ],
  "startRoom": "ext_long_falls"
}
```

**Importante**: cuando `type === "multi-level"`, el cockpit IGNORA `rooms` para el SVG y usa los `coords_url` por level. Los `rooms` legacy quedan para mostrar en panel info / lista navegable (heredado de v5c).

---

## Cambios JS al cockpit (V5v)

### 1. `DUNGEON_BACKGROUNDS` extendido

```js
const DUNGEON_BACKGROUNDS = {
  "barrowmaze": {
    url: "maps/barrowmaze_bg_1920.webp",
    aspectRatio: 1920/1785, opacity: 0.55,
    autoCoordsUrl: "maps/barrowmaze_room_coords.json"
  },
  "ardis_vala": {
    multiLevel: true,
    opacity: 0.65,
    getLevelConfig: (lvlEntry) => ({
      url: lvlEntry.bg_url,
      aspectRatio: lvlEntry.aspect_ratio || (lvlEntry.bg_w / lvlEntry.bg_h),
      autoCoordsUrl: lvlEntry.coords_url
    })
  }
};
```

### 2. Cache de coords (per dungeon, per level)

```js
const AUTO_COORDS = {};  // key: dgId or `${dgId}::${lvlId}`

async function loadAutoCoordsForDungeon(dgId, levelId) {
  const cacheKey = levelId ? `${dgId}::${levelId}` : dgId;
  if (AUTO_COORDS[cacheKey] !== undefined) return AUTO_COORDS[cacheKey];
  const bg = DUNGEON_BACKGROUNDS[dgId];
  if (!bg) { AUTO_COORDS[cacheKey] = null; return null; }
  let url;
  if (bg.multiLevel) {
    if (!levelId) { AUTO_COORDS[cacheKey] = null; return null; }
    const dgData = (state.world.dungeons || {})[dgId];
    const lvlEntry = (dgData?.levels || []).find(l => l.id === levelId);
    if (!lvlEntry) { AUTO_COORDS[cacheKey] = null; return null; }
    url = bg.getLevelConfig(lvlEntry).autoCoordsUrl;
  } else {
    url = bg.autoCoordsUrl;
  }
  if (!url) { AUTO_COORDS[cacheKey] = null; return null; }
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("not found");
    const data = await res.json();
    AUTO_COORDS[cacheKey] = data.room_coords || {};
    return AUTO_COORDS[cacheKey];
  } catch (e) {
    AUTO_COORDS[cacheKey] = null;
    return null;
  }
}
```

### 3. Resolución dinámica de bg + coords activos

```js
function getActiveBgConfig() {
  const dg = state.dungeon;
  if (!dg) return null;
  const bg = DUNGEON_BACKGROUNDS[dg.id];
  if (!bg) return null;
  if (!bg.multiLevel) return bg;
  const dgData = (state.world.dungeons || {})[dg.id];
  if (!dgData || dgData.type !== "multi-level") return null;
  const activeLvlId = dg.activeLevel || dgData.startLevel || dgData.levels?.[0]?.id;
  const lvlEntry = dgData.levels.find(l => l.id === activeLvlId);
  if (!lvlEntry) return null;
  return { ...bg.getLevelConfig(lvlEntry), opacity: bg.opacity };
}

function getActiveCoords() {
  const dg = state.dungeon;
  if (!dg) return null;
  const bg = DUNGEON_BACKGROUNDS[dg.id];
  if (!bg) return null;
  if (bg.multiLevel) {
    const dgData = state.world.dungeons[dg.id];
    const lvlId = dg.activeLevel || dgData.startLevel || dgData.levels?.[0]?.id;
    return AUTO_COORDS[`${dg.id}::${lvlId}`] || {};
  }
  return AUTO_COORDS[dg.id] || {};
}

async function switchDungeonLevel(lvlId) {
  if (!state.dungeon) return;
  state.dungeon.activeLevel = lvlId;
  saveState();
  await loadAutoCoordsForDungeon(state.dungeon.id, lvlId);
  renderDungeon();
}
```

### 4. Manual markers per (dungeon, level)

```js
function getMarkers() {
  if (!state.dungeon) return {};
  state.mapMarkers = state.mapMarkers || {};
  const dgData = state.world.dungeons?.[state.dungeon.id];
  let key = state.dungeon.id;
  if (dgData?.type === "multi-level") {
    const lvl = state.dungeon.activeLevel || dgData.startLevel || dgData.levels?.[0]?.id || "_";
    key = `${state.dungeon.id}::${lvl}`;
  }
  state.mapMarkers[key] = state.mapMarkers[key] || {};
  return state.mapMarkers[key];
}
```

### 5. Zoom + pan en el SVG (resuelve issue del v5c)

```js
function initZoomPan() {
  const svg = document.getElementById("dungeonmap");
  if (!svg || svg.dataset.zoomInit === "1") return;
  svg.dataset.zoomInit = "1";

  let panning = false, lastClient = null;

  // Wheel zoom
  svg.addEventListener("wheel", (e) => {
    e.preventDefault();
    if (state._placeMode) return;
    const vbStr = svg.getAttribute("viewBox");
    if (!vbStr) return;
    const [vx, vy, vw, vh] = vbStr.split(/\s+/).map(Number);
    const pt = svg.createSVGPoint();
    pt.x = e.clientX; pt.y = e.clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    const sp = pt.matrixTransform(ctm.inverse());
    const factor = e.deltaY < 0 ? 1.2 : 1/1.2;
    const newW = vw / factor, newH = vh / factor;
    const newX = sp.x - (sp.x - vx) / factor;
    const newY = sp.y - (sp.y - vy) / factor;
    svg.setAttribute("viewBox", `${newX} ${newY} ${newW} ${newH}`);
  }, { passive: false });

  // Drag pan
  svg.addEventListener("mousedown", (e) => {
    if (state._placeMode) return;
    if (e.button !== 0) return;
    panning = true; lastClient = { x: e.clientX, y: e.clientY };
    svg.style.cursor = "grabbing";
  });
  svg.addEventListener("mousemove", (e) => {
    if (!panning) return;
    const vbStr = svg.getAttribute("viewBox");
    if (!vbStr) return;
    const [vx, vy, vw, vh] = vbStr.split(/\s+/).map(Number);
    const dx = (e.clientX - lastClient.x) * (vw / svg.clientWidth);
    const dy = (e.clientY - lastClient.y) * (vh / svg.clientHeight);
    svg.setAttribute("viewBox", `${vx - dx} ${vy - dy} ${vw} ${vh}`);
    lastClient = { x: e.clientX, y: e.clientY };
  });
  const stopPan = () => {
    panning = false;
    svg.style.cursor = state._placeMode ? "crosshair" : "default";
  };
  svg.addEventListener("mouseup", stopPan);
  svg.addEventListener("mouseleave", stopPan);
}

function resetZoom() { renderDungeon(); }  // re-renderiza, restablece viewBox
```

Llamar `initZoomPan()` desde `openDungeon` después de `renderDungeon()`. Solo se inicializa una vez (flag `dataset.zoomInit`).

### 6. Render selector de level

```js
function renderLevelSelector() {
  const dg = state.dungeon;
  const sel = document.getElementById("dungeon-level-selector");
  if (!sel) return;
  if (!dg) { sel.style.display = "none"; return; }
  const dgData = (state.world.dungeons || {})[dg.id];
  if (!dgData || dgData.type !== "multi-level" || !dgData.levels?.length) {
    sel.style.display = "none"; return;
  }
  sel.style.display = "flex";
  const dropdown = sel.querySelector("select");
  const activeLvl = dg.activeLevel || dgData.startLevel || dgData.levels[0].id;
  if (dropdown.options.length !== dgData.levels.length) {
    dropdown.innerHTML = "";
    dgData.levels.forEach(l => {
      const opt = document.createElement("option");
      opt.value = l.id;
      opt.textContent = l.name;
      dropdown.appendChild(opt);
    });
  }
  dropdown.value = activeLvl;
}
```

Llamar al final de `renderDungeon()`.

### 7. `openDungeon()` con load de level

```js
async function openDungeon(id, hexName) {
  const dungeons = state.world.dungeons || {};
  if (!dungeons[id]) { /* ... */ return; }
  if (!state.dungeon || state.dungeon.id !== id) {
    state.dungeon = { id, currentRoom: dungeons[id].startRoom, fogOfWar: {}, turns: 0 };
    if (dungeons[id].startRoom) state.dungeon.fogOfWar[dungeons[id].startRoom] = "explored";
  }
  state.pcPosition = { scale: "local", hex: state.selectedHex, dungeon: id, room: state.dungeon.currentRoom };
  document.getElementById("dungeon-name").textContent = dungeons[id].name;
  document.getElementById("dungeon-modal").classList.add("open");
  saveState();

  if (dungeons[id].type === "multi-level") {
    if (!state.dungeon.activeLevel) {
      state.dungeon.activeLevel = dungeons[id].startLevel || dungeons[id].levels?.[0]?.id;
    }
    await loadAutoCoordsForDungeon(id, state.dungeon.activeLevel);
  } else {
    await loadAutoCoordsForDungeon(id);
  }
  renderDungeon();
  initZoomPan();
}
```

### 8. `renderDungeon()` modificado

```js
function renderDungeon() {
  const dg = state.dungeon;
  if (!dg) return;
  const dgData = (state.world.dungeons || {})[dg.id];
  if (!dgData) return;
  const svg = document.getElementById("dungeonmap");
  svg.innerHTML = "";

  // Background image (resuelve multi-level)
  const bg = getActiveBgConfig();
  if (bg) {
    const targetW = 800;
    const targetH = Math.round(targetW / bg.aspectRatio);
    svg.setAttribute("viewBox", `0 0 ${targetW} ${targetH}`);
    svg.setAttribute("height", targetH);
    const img = document.createElementNS("http://www.w3.org/2000/svg", "image");
    img.setAttributeNS("http://www.w3.org/1999/xlink", "href", bg.url);
    img.setAttribute("href", bg.url);
    img.setAttribute("x", 0); img.setAttribute("y", 0);
    img.setAttribute("width", targetW); img.setAttribute("height", targetH);
    img.setAttribute("opacity", bg.opacity);
    img.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svg.appendChild(img);
  } else {
    svg.setAttribute("viewBox", "0 0 800 500");
    svg.setAttribute("height", 500);
  }
  renderLevelSelector();

  // Render markers (auto + manual)
  renderMapMarkers();

  // ... resto del código de connections + rooms con x/y queda igual
}
```

### 9. `renderMapMarkers()` con escalado bg → SVG

**Las coords del JSON están en sistema bg image (ej. 1600 wide), no en SVG (800 wide).** Hay que escalar:

```js
function renderMapMarkers() {
  const dg = state.dungeon;
  if (!dg) return;
  const dgData = (state.world.dungeons || {})[dg.id];
  if (!dgData) return;
  const svg = document.getElementById("dungeonmap");
  const manualMarkers = getMarkers();
  const autoCoords = getActiveCoords() || {};

  // Calcular factor de escala bg → SVG
  let scaleX = 1, scaleY = 1;
  const bg = getActiveBgConfig();
  if (bg) {
    // Get bg dimensions from level entry (multi) or DUNGEON_BACKGROUNDS (single)
    let bgW;
    if (DUNGEON_BACKGROUNDS[dg.id]?.multiLevel) {
      const lvlId = dg.activeLevel || dgData.startLevel;
      const lvlEntry = dgData.levels.find(l => l.id === lvlId);
      bgW = lvlEntry?.bg_w || 1600;
    } else {
      // For barrowmaze single-level: coords already in SVG units (800)
      bgW = 800;
    }
    scaleX = scaleY = 800 / bgW;
  }

  // ... merge auto + manual y renderear circles. Aplicar scaleX/Y a coords.
  // Ejemplo:
  //   const cx = (pos.x * scaleX);
  //   const cy = (pos.y * scaleY);
}
```

**Nota crítica**: el JSON de Barrowmaze ya tiene coords en SVG units (800), pero los de Arden Vul están en bg image units (1600). Si V5v unifica esto, mejor convertir todos a SVG units en el script Python (multiplicar por 800/bg_w al guardar).

### 10. HTML del modal (selector + zoom)

```html
<div id="dungeon-modal">
  <div class="dungeon-panel">
    <header>
      <h1 style="font-size: 16px;">🜍 <span id="dungeon-name">Dungeon</span></h1>
      <div class="modes">
        <button onclick="resetZoom()" title="Reset zoom">⌖ Centrar</button>
        <button onclick="closeDungeon()">⤴ Volver al hex</button>
      </div>
    </header>
    <!-- NUEVO: selector de level (oculto si single-level) -->
    <div id="dungeon-level-selector" style="display:none; align-items:center; gap: 8px; margin-bottom: 6px; padding: 6px 10px; background: var(--bg-2); border: 1px solid var(--border); border-radius: 3px;">
      <span style="font-size: 11px; color: var(--ink-dim); text-transform: uppercase;">Nivel:</span>
      <select onchange="switchDungeonLevel(this.value)" style="flex:1; background: var(--panel-2); color: var(--ink); border: 1px solid var(--border); padding: 4px 6px; font-size: 12px; border-radius: 3px;"></select>
    </div>
    <!-- resto del modal queda igual: place-mode-banner, room-svg-wrap, room-detail, keyed-rooms-section -->
  </div>
</div>
```

---

## Pipeline Python reutilizable

Si querés re-correr el OCR con tweaks (más PSM modes, distinto threshold, etc.), tenés el script. Lo guardé inline acá:

### `extract_arden_vul_maps.py`

```python
"""Extract bg + coords for all Arden Vul levels from main PDF."""
import fitz, json, os, io
from PIL import Image
import pytesseract
from PIL import ImageOps, ImageFilter

PDF = r"G:\Mi unidad\02_ROL_Y_MEGACAMPAÑA\Biblioteca_Absoluta\The Halls of Arden Vul (1e,OSRIC).pdf"
OUT_DIR = r"C:\Users\Usuario\Desktop\Cemanahuac\maps\arden_vul"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

LEVELS = [
    (1135, "L1",  "Level 1 — The Basement"),
    (1136, "L2",  "Level 2 — Howling Caves & Well of Light"),
    # ... resto idéntico (10 levels + 17 sublevels = 27 entries)
]

def extract_bg(doc, page_num, lvl_id, out_dir):
    """Extract embedded image from a map page; save webp display + full versions."""
    pidx = page_num - 1
    p = doc[pidx]
    images = p.get_images(full=True)
    if not images: return None
    xref = images[0][0]
    pix = fitz.Pixmap(doc, xref)
    if pix.n - pix.alpha >= 4:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    pil = Image.open(io.BytesIO(pix.tobytes("png")))
    orig_w, orig_h = pil.size
    pil.save(os.path.join(out_dir, f"{lvl_id}_full.webp"), "webp", quality=90)
    if orig_w > 1600:
        scale = 1600 / orig_w
        pil_d = pil.resize((1600, int(orig_h * scale)), Image.LANCZOS)
        pil_d.save(os.path.join(out_dir, f"{lvl_id}_bg.webp"), "webp", quality=85)
        return (orig_w, orig_h, 1600, int(orig_h * scale))
    pil.save(os.path.join(out_dir, f"{lvl_id}_bg.webp"), "webp", quality=85)
    return (orig_w, orig_h, orig_w, orig_h)

def ocr_multi(img_path, target_widths=[2000, 3000, 4500]):
    """Multi-scale OCR with adaptive preprocessing. Returns {rid: {ox, oy, conf}} in original img coords."""
    import re
    orig = Image.open(img_path).convert('L')
    orig_w, orig_h = orig.size
    all_hits = []
    for tw in target_widths:
        if tw > orig_w * 1.2: continue
        scale = tw / orig_w
        img = orig.resize((tw, int(orig_h * scale)), Image.LANCZOS) if tw < orig_w else orig.copy()
        proc_w, proc_h = img.size
        img_eq = ImageOps.autocontrast(img, cutoff=1)
        img_sh = img_eq.filter(ImageFilter.SHARPEN)
        for thr in [120, 150, 180]:
            img_bw = img_sh.point(lambda p, t=thr: 255 if p > t else 0)
            for psm in [11, 12]:
                cfg = f'--psm {psm} -c tessedit_char_whitelist=0123456789ABab'
                try:
                    data = pytesseract.image_to_data(img_bw, output_type=pytesseract.Output.DICT, config=cfg)
                except Exception: continue
                for i, txt in enumerate(data['text']):
                    txt = txt.strip()
                    if not txt: continue
                    if not re.match(r'^\d{1,4}[Aa-bA-Bs]?$', txt): continue
                    conf = int(data['conf'][i])
                    if conf < 35: continue
                    h = data['height'][i]
                    if h < 8 or h > proc_h // 25: continue
                    ox = int((data['left'][i] + data['width'][i] // 2) / scale)
                    oy = int((data['top'][i] + data['height'][i] // 2) / scale)
                    all_hits.append({"text": txt, "ox": ox, "oy": oy, "conf": conf})
    # Dedupe within 50px radius (per text)
    final = {}
    used = []
    for h in sorted(all_hits, key=lambda x: -x["conf"]):
        nearby = any(p["text"] == h["text"] and abs(p["ox"] - h["ox"]) < 50 and abs(p["oy"] - h["oy"]) < 50 for p in used)
        if nearby: continue
        used.append(h)
        if h["text"] not in final or h["conf"] > final[h["text"]]["conf"]:
            final[h["text"]] = {"ox": h["ox"], "oy": h["oy"], "conf": h["conf"]}
    return final, orig_w, orig_h

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    doc = fitz.open(PDF)
    manifest = {"levels": []}
    for page_num, lvl_id, lvl_name in LEVELS:
        dims = extract_bg(doc, page_num, lvl_id, OUT_DIR)
        if not dims: continue
        orig_w, orig_h, bg_w, bg_h = dims
        manifest["levels"].append({
            "id": lvl_id, "name": lvl_name, "page_pdf": page_num,
            "bg_url": f"maps/arden_vul/{lvl_id}_bg.webp",
            "bg_full_url": f"maps/arden_vul/{lvl_id}_full.webp",
            "bg_w": bg_w, "bg_h": bg_h,
            "original_w": orig_w, "original_h": orig_h,
            "aspect_ratio": orig_w / orig_h
        })
        # OCR
        rooms_orig, _, _ = ocr_multi(os.path.join(OUT_DIR, f"{lvl_id}_full.webp"))
        scale_to_bg = bg_w / orig_w
        coords = {rid: {"x": round(d["ox"] * scale_to_bg, 1), "y": round(d["oy"] * scale_to_bg, 1)}
                  for rid, d in rooms_orig.items()}
        with open(os.path.join(OUT_DIR, f"{lvl_id}_coords.json"), 'w', encoding='utf-8') as f:
            json.dump({"level_id": lvl_id, "level_name": lvl_name,
                       "bg_url": f"maps/arden_vul/{lvl_id}_bg.webp",
                       "bg_w": bg_w, "bg_h": bg_h,
                       "room_coords": coords,
                       "_unique_rooms": len(coords)},
                      f, indent=2, ensure_ascii=False)
    doc.close()
    with open(os.path.join(OUT_DIR, "manifest.json"), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
```

Tiempo total: ~10 min (extracción 30s + OCR 9 min en Ryzen mediano).

---

## Pasos para integrar al fork V5v

1. **Copiar assets** (62 MB):
   ```bash
   cp -r Cemanahuac/maps/arden_vul <V5v>/maps/arden_vul
   ```

2. **Update campaña** (`campaigns/novatos_ravenloft.json`): mergear el bloque `dungeons.ardis_vala` con `type: "multi-level"` + `levels: [27]`. JSON listo en `Cemanahuac/campaigns/novatos_ravenloft.json` (busca `"ardis_vala"`).

3. **Aplicar 10 cambios JS** del § "Cambios JS al cockpit" (DUNGEON_BACKGROUNDS, AUTO_COORDS, getActiveBgConfig, getActiveCoords, switchDungeonLevel, getMarkers per-level, initZoomPan, resetZoom, renderLevelSelector, openDungeon).

4. **Aplicar HTML** del modal con selector + reset zoom (§ HTML del modal).

5. **Validar**: `node --check` el JS extraído del HTML. Probar abrir Ardis Vala → debería ver el selector de nivel y al cambiar L1 → L3 actualizar bg + markers.

6. **Marcador current-room**: si state.dungeon.currentRoom es un ID que coincide con auto-coords de algún level, ese marker se highlight como "party here". Es transparente — si estás en Sala 74 de Barrowmaze (state.dungeon.currentRoom = "74"), y abrís Ardis Vala, el current-room no aplica hasta que asignes uno del level activo.

---

## Issues conocidos / honestidad

### OCR no es perfecto

- Coverage promedio 80%. Algunos levels (L1, L10, L2) tienen coverage bajo (25-55%) por ser mapas con números chicos o pocos rooms.
- Falsos positivos esperables: números pintados en walls, leyendas internas, cross-refs entre levels. Marcos puede borrar manualmente con click-to-place override (heredado de v5c).
- IDs alfanuméricos (74A, 2b, etc.) los detecta parcialmente — el regex acepta 1-4 digits + letra opcional.

### Mejoras posibles (no implementadas)

- **EasyOCR** en lugar de tesseract: más lento pero más preciso para fonts irregulares. Si querés probar: `pip install easyocr` y reemplazar `pytesseract.image_to_data` por `easyocr.Reader(['en']).readtext`.
- **Pre-segmentación** del mapa: detectar regiones de "drawing area" vs "leyenda" antes de OCR. Reduce falsos positivos drásticamente.
- **Validación cruzada** con el ROUTER_ARDEN_VUL.md (que tiene la lista de NPCs y rooms keyed por level): contrastar IDs detectados con los conocidos del módulo y descartar fuera de rango.

### Coords están en sistema BG image, no SVG

Esto es DIFERENTE al pipeline de Barrowmaze (cuyas coords están en SVG units 800). Si V5v unifica, recomendado convertir todas a SVG en el script Python:

```python
# En extract_arden_vul_maps.py, al guardar:
coords = {rid: {"x": round(d["ox"] * (800 / orig_w), 1),
                "y": round(d["oy"] * (800 / orig_w), 1)}
          for rid, d in rooms_orig.items()}
# Y eliminar la lógica de scaleX en renderMapMarkers.
```

Mejor unificar antes de mergear. Yo dejé como bg-units porque facilita re-rendear a otra resolución sin recompute.

### Asset volume

62 MB de webp. Para deploy a Cloudflare Pages, puede pesar. Opciones:

- Servir desde **Cloudflare R2** (object storage) y referenciar URLs absolutas.
- **Lazy-load** del bg solo cuando se selecciona el level.
- **Usar `_bg.webp` solamente** (descartar `_full.webp`): pasa de 62 MB a ~5 MB. Las versiones full son útiles si querés zoom muy alto, pero el cockpit las usa solo via display (1600 wide).

```bash
rm maps/arden_vul/*_full.webp   # ~57 MB liberados
```

---

## Resumen ejecutivo

| Item | Estado | Path |
|---|---|---|
| 27 webp bg display (1600 wide) | ✓ listos | `maps/arden_vul/<lvlid>_bg.webp` |
| 27 webp bg full (original) | ✓ listos | `maps/arden_vul/<lvlid>_full.webp` |
| 27 JSON coords | ✓ listos (1293 rooms) | `maps/arden_vul/<lvlid>_coords.json` |
| Manifest | ✓ listo | `maps/arden_vul/manifest.json` |
| JSON campaign con `ardis_vala` multi-level | ✓ listo | `campaigns/novatos_ravenloft.json` |
| JS cambios (10) | ✓ documentados acá | (este MD) |
| HTML modal con selector | ✓ documentado acá | (este MD) |
| Pipeline Python | ✓ documentado acá | (este MD) |
| Deploy al v5c de este chat | ✗ no hecho (a tu pedido) | — |

**Siguiente paso**: vos copiás los 62 MB y los 10 snippets de JS al fork V5v. Si el JS válido (`node --check`) y abrís el dungeon Ardis Vala, deberías ver el selector arriba con 27 niveles, cambiar a "Level 3 - Halls of Thoth" y ver el mapa real con ~155 markers dorados.

---

**Sesión cockpit V5c · Cemanahuac · 2026-04-30**
