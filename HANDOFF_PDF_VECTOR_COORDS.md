# HANDOFF · Auto-extracción de coordenadas vectoriales del PDF Barrowmaze
**Sesión:** cockpit V5c (este chat)
**Fecha:** 2026-04-30
**Para:** fork V5v / dungeon-crawler con radios de visión

---

## TL;DR

Los números de habitación del módulo Barrowmaze (1-375) están en el PDF como **texto vectorial**, no como dibujo raster. Eso significa que se pueden extraer con sus coordenadas exactas en una sola pasada. **No hace falta OCR.**

Pipeline: **PyMuPDF → coords PDF → conversion al sistema de la imagen stitched → JSON**. ~22 KB final, cargable en cualquier viewer.

Resultado: 375 rooms con (x, y) en sistema SVG 800×744. Tiempo: <1 segundo de extracción.

Esta misma técnica se puede aplicar a CUALQUIER PDF OSR que tenga rooms numeradas (Stonehell, Castle Xyntillan, Halls of Arden Vul, etc.).

---

## El insight

```
Los números de habitación en mapas de PDFs publicados modernos
(InDesign export) son texto vector, no parte del dibujo raster.
```

Verificación rápida en cualquier PDF:

```python
import fitz  # PyMuPDF
doc = fitz.open("mapa.pdf")
page = doc[0]
spans = []
for block in page.get_text("dict")["blocks"]:
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            spans.append((span["text"], span["bbox"], span["size"]))
print(f"Spans con texto: {len(spans)}")
# Si hay >0, los números son extraíbles
```

Si el PDF es escaneado (raster puro), no funciona — ahí sí hace falta OCR. Para el módulo Barrowmaze 10th Ebook OSR 2022 (InDesign 16.1), funciona perfecto.

---

## Geometría de la stitched image (Barrowmaze)

La imagen final del cockpit es una composición de 6 páginas del PDF. Layout descubierto por Marcos en sesión paralela (ver `sandbox/barrowmaze-assembly/HANDOFF.md`):

```
       col 0    col 1    col 2
       (left)   (center) (right)

row 0  | 234 |  | 235 |  | 238 |    ← north row
       +-----+  +-----+  +-----+
row 1  | 236 |  | 237 |  | 239 |    ← south row
       +-----+  +-----+  +-----+
```

Entonces el mapping `page_index → (col, row)` es:

```python
PAGE_LAYOUT = {
    0: (0, 0),  # PDF page 1 → stitched col=0 row=0 (book page 234)
    1: (1, 0),  # PDF page 2 → col=1 row=0 (book 235)
    2: (0, 1),  # PDF page 3 → col=0 row=1 (book 236)
    3: (1, 1),  # PDF page 4 → col=1 row=1 (book 237)
    4: (2, 0),  # PDF page 5 → col=2 row=0 (book 238)
    5: (2, 1),  # PDF page 6 → col=2 row=1 (book 239)
}
```

---

## Constantes de transformación

Todas vienen del pipeline de stitch del proyecto paralelo:

```python
DPI = 250                            # render PDF a 250 DPI
PT_TO_PX = DPI / 72                  # = 3.4722 (PDF point a píxel)

# Crop aplicado a cada tile renderizado (en píxeles a 250 DPI)
# Saca márgenes y leyendas, deja solo el grid del mapa
CROP = (170, 204, 1922, 2648)        # (left, top, right, bottom)
TILE_W = CROP[2] - CROP[0]           # 1752 px
TILE_H = CROP[3] - CROP[1]           # 2444 px

# Stitched final
STITCHED_W = 3 * TILE_W              # 5256 px
STITCHED_H = 2 * TILE_H              # 4888 px

# Para el cockpit: el SVG renderea a 800 px wide, alto proporcional
SVG_W = 800
SVG_H = round(SVG_W * STITCHED_H / STITCHED_W)  # = 744 px
SCALE = SVG_W / STITCHED_W           # = 0.1522 (factor único)
```

---

## Conversión coordenada (lo crítico)

Para cada span de texto en el PDF:

```
PDF point (px_pt, py_pt en página p)
   ↓ × PT_TO_PX
píxel a 250 DPI dentro de la página renderizada
   ↓ − CROP[0] horizontal,  − CROP[1] vertical
píxel dentro del tile cropped
   ↓ + col × TILE_W,  + row × TILE_H
píxel en stitched 5256×4888
   ↓ × SCALE
coord SVG 800×744 ← LO QUE GUARDÁS
```

En código:

```python
cx_pt = (bbox[0] + bbox[2]) / 2    # centro del span en pts
cy_pt = (bbox[1] + bbox[3]) / 2

cx_in_tile = cx_pt * PT_TO_PX - CROP[0]
cy_in_tile = cy_pt * PT_TO_PX - CROP[1]

if not (0 <= cx_in_tile <= TILE_W and 0 <= cy_in_tile <= TILE_H):
    continue  # el span está en el área cropped, no en el mapa

cx_svg = (col * TILE_W + cx_in_tile) * SCALE
cy_svg = (row * TILE_H + cy_in_tile) * SCALE
```

---

## Filtros aplicados

Los PDFs de mapas tienen MUCHO texto vector que NO son rooms (page numbers, leyendas, cross-references). Filtros usados:

### 1. Por tamaño de fuente

```python
if size > 6.5:
    continue   # page numbers son ~8.0, room IDs son ~5.4
```

Esto descarta los **page numbers** (234, 235...) que aparecen abajo de cada página. El threshold exacto varía por módulo (chequear con un sample antes).

### 2. Por contenido

```python
if not re.match(r'^\d{1,3}$', text):
    continue  # solo números 1-3 dígitos
```

Descarta título, leyenda, cross-references textuales.

### 3. Cross-references repetidas (1-9)

Los módulos OSR usan numeritos pequeños 1-4 en los bordes de cada página para indicar "esta puerta lleva al hexágono X de la página Y". Esos no son rooms.

```python
# Si un ID tiene 4+ ocurrencias y TODAS están a <30px del borde del tile:
# es cross-ref, descartar
near_edge = (
    cx_in_tile < 30 or cx_in_tile > TILE_W - 30 or
    cy_in_tile < 30 or cy_in_tile > TILE_H - 30
)
```

En la práctica, para Barrowmaze este filtro NO descartó nada porque las cross-refs no estaban tan cerca del borde. La heurística más útil fue: **si una room aparece N veces, elegir la occurrence non-edge**. Las cross-refs caen near-edge, las rooms reales no.

```python
non_edge_occs = [o for o in occurrences[rid] if not o.near_edge]
chosen = non_edge_occs[0] if non_edge_occs else occurrences[rid][0]
```

---

## Script reproducible

`extract_room_coords.py`:

```python
#!/usr/bin/env python3
"""Extract room number coordinates from a PDF map module.

Output: JSON { room_id: {x, y} } in target SVG coordinate system.
"""
import fitz, json, re, sys, argparse
from collections import defaultdict

def extract(pdf_path, page_layout, crop, dpi=250, svg_w=800,
            font_size_max=6.5, edge_px=30, output_path=None):
    """
    page_layout: dict { page_idx: (col, row) }
    crop: (left, top, right, bottom) in DPI px to remove from each tile
    """
    pt_to_px = dpi / 72
    tile_w = crop[2] - crop[0]
    tile_h = crop[3] - crop[1]
    cols = max(c for c, r in page_layout.values()) + 1
    rows = max(r for c, r in page_layout.values()) + 1
    stitched_w = cols * tile_w
    stitched_h = rows * tile_h
    svg_h = round(svg_w * stitched_h / stitched_w)
    scale = svg_w / stitched_w

    doc = fitz.open(pdf_path)
    occurrences = defaultdict(list)

    for page_idx, p in enumerate(doc):
        if page_idx not in page_layout:
            continue
        col, row = page_layout[page_idx]
        for block in p.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if span["size"] > font_size_max:
                        continue
                    if not re.match(r'^\d{1,3}$', text):
                        continue
                    bbox = span["bbox"]
                    cx_pt = (bbox[0] + bbox[2]) / 2
                    cy_pt = (bbox[1] + bbox[3]) / 2
                    cx_in_tile = cx_pt * pt_to_px - crop[0]
                    cy_in_tile = cy_pt * pt_to_px - crop[1]
                    if not (0 <= cx_in_tile <= tile_w
                            and 0 <= cy_in_tile <= tile_h):
                        continue
                    cx_svg = round((col * tile_w + cx_in_tile) * scale, 1)
                    cy_svg = round((row * tile_h + cy_in_tile) * scale, 1)
                    near_edge = (
                        cx_in_tile < edge_px or cx_in_tile > tile_w - edge_px or
                        cy_in_tile < edge_px or cy_in_tile > tile_h - edge_px
                    )
                    occurrences[text].append({
                        "x": cx_svg, "y": cy_svg, "near_edge": near_edge
                    })
    doc.close()

    # Resolve duplicates
    final = {}
    for rid, occs in occurrences.items():
        non_edge = [o for o in occs if not o["near_edge"]]
        chosen = non_edge[0] if non_edge else occs[0]
        final[rid] = {"x": chosen["x"], "y": chosen["y"]}

    out = {
        "_doc": "Auto-extracted room coords from PDF maps (vector text)",
        "svg_w": svg_w, "svg_h": svg_h,
        "scale_factor": scale,
        "stitched_dimensions": [stitched_w, stitched_h],
        "room_coords": final
    }
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2)
    return final

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    # Defaults Barrowmaze; override for other modules
    BARROWMAZE_LAYOUT = {0:(0,0),1:(1,0),2:(0,1),3:(1,1),4:(2,0),5:(2,1)}
    BARROWMAZE_CROP = (170, 204, 1922, 2648)
    final = extract(args.pdf, BARROWMAZE_LAYOUT, BARROWMAZE_CROP,
                    output_path=args.out)
    print(f"Extracted {len(final)} rooms → {args.out}")
```

Uso:

```bash
python extract_room_coords.py \
    --pdf "Mapas de Barrowmaze 10th Ebook OSR 2022.pdf" \
    --out maps/barrowmaze_room_coords.json
```

---

## Formato de output

`barrowmaze_room_coords.json` (22 KB):

```json
{
  "_doc": "Auto-extracted Barrowmaze room coords from PDF maps (vector text)",
  "svg_w": 800,
  "svg_h": 744,
  "scale_factor": 0.1522,
  "stitched_dimensions": [5256, 4888],
  "room_coords": {
    "1":   { "x": 34.8, "y": 353.5 },
    "2":   { "x": 34.8, "y": 378.8 },
    "74":  { "x": 118.7, "y": 309.1 },
    "375": { "x": 672.2, "y": 105.0 }
  }
}
```

**Importante**: `room_coords[rid].x/y` son coords en sistema SVG 800×744 (escalable proporcionalmente). Para usar en otra resolución, multiplicar por (target_w / 800).

---

## Cómo integrarlo a V5v (dungeon-crawler con radios de visión)

### Stack base recomendado

Si V5v ya tiene zoom/pan, line-of-sight y grid de celdas, agregar coords es trivial. Tres consideraciones:

#### 1. **Coords absolutas, no por celda**

Las coords extraídas son **continuas en píxeles SVG**, no en grid cells. Si V5v usa grid (por ej. "1 square = 10 ft" del módulo, lo dice la legend del PDF), conviertir:

```js
// En el módulo Barrowmaze, cada celda del grid es 10 ft.
// La imagen stitched es 5256×4888 px. Si contás celdas a mano sobre
// el mapa físico, sale que el dungeon es ~aproximadamente 240×180 cells
// (son 80 cells por tile × 3 cols, 60 cells × 2 rows — verificar contando)
//
// Conversión SVG → grid cell:
const CELL_SIZE_SVG = SVG_W / 240;  // ~3.33 px per cell at SVG res
const cellX = Math.floor(coord.x / CELL_SIZE_SVG);
const cellY = Math.floor(coord.y / CELL_SIZE_SVG);
```

V5v puede usar las coords directamente para "marcar dónde está la sala N en el grid", sin tener que dibujar paredes a mano.

#### 2. **Zoom + pan**

El v5c que estamos viendo NO tiene zoom (issue que mencionaste). Solución mínima viable con SVG:

```js
// SVG nativo soporta zoom via viewBox
let viewBox = { x: 0, y: 0, w: SVG_W, h: SVG_H };

function zoom(factor, cx, cy) {
  // cx, cy: punto del SVG donde centrar el zoom (mouse position)
  const newW = viewBox.w / factor;
  const newH = viewBox.h / factor;
  viewBox.x = cx - (cx - viewBox.x) / factor;
  viewBox.y = cy - (cy - viewBox.y) / factor;
  viewBox.w = newW;
  viewBox.h = newH;
  svg.setAttribute("viewBox", `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`);
}

// Wheel zoom
svg.addEventListener("wheel", (e) => {
  e.preventDefault();
  const pt = svg.createSVGPoint();
  pt.x = e.clientX; pt.y = e.clientY;
  const ctm = svg.getScreenCTM().inverse();
  const svgPt = pt.matrixTransform(ctm);
  zoom(e.deltaY < 0 ? 1.2 : 1/1.2, svgPt.x, svgPt.y);
});

// Pan: mousedown + drag
let panning = false, lastPt = null;
svg.addEventListener("mousedown", (e) => {
  panning = true; lastPt = { x: e.clientX, y: e.clientY };
});
svg.addEventListener("mousemove", (e) => {
  if (!panning) return;
  const dx = (e.clientX - lastPt.x) * (viewBox.w / svg.clientWidth);
  const dy = (e.clientY - lastPt.y) * (viewBox.h / svg.clientHeight);
  viewBox.x -= dx; viewBox.y -= dy;
  lastPt = { x: e.clientX, y: e.clientY };
  svg.setAttribute("viewBox", `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`);
});
svg.addEventListener("mouseup", () => panning = false);
svg.addEventListener("mouseleave", () => panning = false);
```

Eso permite scroll-zoom + click-drag pan sobre el mapa. Las coords de los markers no cambian; solo cambia el viewBox.

#### 3. **Line-of-sight con radios**

Si V5v usa LOS, las coords de rooms son **landmarks naturales** para el algoritmo:

```js
// Cada room está en (x, y) en SVG coords.
// Visión del party (en sala N) con radio R cubre todas las rooms
// con distancia euclidiana < R, MENOS las bloqueadas por paredes.
const partyPos = roomCoords[currentRoom];
const VISION_RADIUS_SVG = 60;  // ~60 SVG px ≈ 18 cells ≈ 180 ft

const visibleRooms = Object.entries(roomCoords).filter(([rid, pos]) => {
  const dist = Math.hypot(pos.x - partyPos.x, pos.y - partyPos.y);
  if (dist > VISION_RADIUS_SVG) return false;
  // Walls: necesitás un dataset de paredes. Si no lo tenés todavía,
  // falla a "todas dentro del radio son visibles" como aproximación.
  return !lineBlockedByWall(partyPos, pos, walls);
});
```

Las paredes de Barrowmaze NO están extraídas todavía (eso es la siguiente capa, mucho más compleja). Pero las coords de rooms ya te dan el 80% del valor: el GM ve cuáles rooms están "cerca" del party sin contar celdas a mano.

#### 4. **Grid overlay opcional**

Para tracking más fino, dibujar el grid encima del background:

```js
const CELL_SIZE_PX = 800 / 240;  // SVG units per cell
for (let i = 0; i <= 240; i++) {
  const line = document.createElementNS("...", "line");
  line.setAttribute("x1", i * CELL_SIZE_PX); line.setAttribute("y1", 0);
  line.setAttribute("x2", i * CELL_SIZE_PX); line.setAttribute("y2", SVG_H);
  line.setAttribute("stroke", "rgba(212,160,74,0.15)");
  line.setAttribute("stroke-width", 0.3);
  svg.appendChild(line);
}
```

Marcos puede toggle el grid on/off para no saturar la vista.

---

## Issues conocidos que V5v debe resolver

### Issue del v5c (este chat) — sin zoom

El SVG 800×744 se renderea fixed en el modal del cockpit. No hay scroll-zoom ni pan. **Eso es lo primero que V5v tiene que resolver**. El código del § "Zoom + pan" arriba lo soluciona en ~30 líneas.

### Cross-references 1-9 mal posicionadas

Los IDs 1-9 tenían 4 occurrences cada uno (cross-refs N/S/E/W del módulo). El filtro elige la occurrence "non-edge" cuando existe, pero si todas son near-edge, queda la primera. Esto puede dar coords incorrectas para 1-9.

**Workaround manual**: en cockpit, override con click-to-place (ya implementado en v5c, función `placeMarkerAt`). El marker manual sobreescribe el auto.

**Workaround automático**: para esos rooms, usar el texto del módulo (Areas 1-10 keyed) y mappear "Area 1, room 1" → buscar en qué Area está y filtrar por bounding box del Area.

### Grid cells exactas no calibradas

Para que V5v haga LOS preciso, hay que **contar manualmente cuántas celdas tiene la imagen stitched** (the legend dice "1 Square = 10 feet" pero no dice cuántas hay total). En el HANDOFF de Marcos:

> "Calibración de celdas no hecha todavía: hay que contar manualmente cuántas celdas tiene el mapa combinado para setear `width`/`height` en `barrowmaze.json` (actualmente 36×24, claramente erróneo para 6 páginas combinadas)."

Estimación rápida (sin verificar): si cada tile es 1752 px a 250 DPI y cada celda es 25 px = 0.1 inch a 250 DPI = 10 ft, entonces 1752 / 25 = ~70 cells por tile. Con 3 tiles horizontal = ~210 cells horizontal. Para vertical: 2444 / 25 = 97 cells por tile, × 2 = ~195 cells vertical. **Approx 210×195 = ~41,000 cells totales.** Para confirmar: contar manualmente sobre `combined_v3_full.png` (5256×4888).

Una vez calibrado:

```js
const GRID_W_CELLS = 210;  // verificar
const GRID_H_CELLS = 195;  // verificar
const CELL_PX_SVG = SVG_W / GRID_W_CELLS;
```

### Walls extraction (siguiente nivel)

Para LOS real, hay que extraer las **walls** del mapa. Eso es mucho más complejo:

- **Opción A**: extraer paths/strokes del PDF original (algunas ediciones tienen walls como SVG paths recuperables con PyMuPDF). Probar `page.get_drawings()`.
- **Opción B**: image processing sobre la stitched image (Hough lines en bordes detectados con Canny). Muy ruidoso.
- **Opción C**: usar Universal VTT (.uvtt) si Greg Gillespie lo publicó. Algunos módulos modernos sí.
- **Opción D** (pragmática): GM marca walls a mano sobre el mapa la primera vez que entra a una región. Lento pero exacto.

Mi voto: empezar sin LOS (radio circular puro) y agregar walls incrementalmente solo donde el party está explorando.

---

## Aplicabilidad a otros módulos

Esta técnica funciona para CUALQUIER PDF OSR moderno con texto vectorial. Probable que funcione con:

| Módulo | Layout estimado | Esfuerzo |
|---|---|---|
| **Halls of Arden Vul** | 10 niveles + 15 sub-niveles | Cada nivel es un PDF aparte. Repetir pipeline. |
| **Stonehell** | 1 PDF, múltiples páginas | Layout más simple. |
| **Castle Xyntillan** | varias secciones | Posible. |
| **Maze of the Blue Medusa** | 1 mapa gigante | Layout 1×1. Trivial. |
| **The Sunless Citadel** (5e) | 2 niveles, escasa data vector | Posible que sea raster. Verificar. |

Workflow general:

1. Bajar PDF.
2. Identificar layout (cuántas páginas, cómo se conectan).
3. Renderear a 250 DPI (PyMuPDF).
4. Decidir crop (saca márgenes y leyendas).
5. Stitch (Pillow).
6. Correr `extract_room_coords.py` con ese layout y crop.
7. Cargar en V5v.

Tiempo total por módulo: 30-60 min si los crop/layout son razonables.

---

## Archivos relevantes en este chat

- `C:\Users\Usuario\Desktop\Cemanahuac\maps\barrowmaze_room_coords.json` (22 KB, 375 rooms)
- `C:\Users\Usuario\Desktop\Cemanahuac\maps\barrowmaze_bg_1920.webp` (348 KB, mapa v3 limpio)
- `C:\Users\Usuario\Desktop\Cemanahuac\prototipo_v5c.html` (visor actual, sin zoom)
- `C:\Users\Usuario\CODE\mc-prism\sandbox\barrowmaze-assembly\` (sesión paralela: stitch pipeline + raw pages)

---

## Próximos pasos sugeridos para V5v

Ranqueados por impacto:

1. **Zoom + pan en el SVG** (~30 líneas de código, el más urgente).
2. **Cargar `barrowmaze_room_coords.json`** y renderear todos los markers (heredar lógica de v5c).
3. **Toggle grid overlay** on/off.
4. **Calibrar grid cells** contando manualmente.
5. **LOS circular puro** (sin walls) con radio configurable.
6. **Marker manual override** para corregir auto (heredar de v5c, `placeMarkerAt`).
7. **Walls** vía dibujado a mano incremental por el GM.

---

## Si V5v ya tiene un canvas/WebGL renderer

Usá las coords directamente como sprite positions. El SVG es solo una opción de renderer; el JSON de coords es agnóstico al renderer.

Para Phaser/PixiJS:

```js
const coords = await fetch("maps/barrowmaze_room_coords.json").then(r => r.json());
for (const [rid, pos] of Object.entries(coords.room_coords)) {
  const sprite = scene.add.circle(pos.x * scaleToCanvas, pos.y * scaleToCanvas, 8, 0xd4a04a);
  sprite.setData("roomId", rid);
}
```

Para Three.js (si V5v es 3D):

```js
const positions = coords.room_coords;
// Map (x, y) SVG → (x, z) world space, fixed y=0 (mapa plano)
```

---

Cualquier duda del pipeline: el script Python está en este MD y funciona standalone. Lo más complejo fue calcular las constantes de transformación (DPI, crop, layout) — el resto es texto vectorial trivial.

— Sesión cockpit V5c
