# HANDOFF v6k6 · Cockpit Valakhan · Continuar iteración

**Fecha cierre**: 2026-05-02
**Live URL**: https://mc-prism.pages.dev/cockpit
**Última versión**: v6k6
**Última deploy CF**: 17715a27 (preview: https://17715a27.mc-prism.pages.dev)

---

## 🔥 Cambio mayor V6k6: markers re-extraídos del PDF vectorial

El JSON viejo de `barrowmaze_room_coords.json` tenía los IDs de room **completamente arbitrarios** — el extractor original detectó 375 círculos en el mapa y los renumeró 1, 2, 3, ..., 375 en orden de detección, sin leer los números reales del módulo. Por eso "room 1" del JSON viejo no correspondía a "Room 1" del módulo Barrowmaze. Y `rooms_full.json` tenía descripciones MAL ASOCIADAS (room 1 traía texto de "Nergal's Beckoning" del final del libro).

**Solución V6k6** (Opción F del plan):
1. Copiados los PDFs source desde `G:/Mi unidad/02_ROL_Y_MEGACAMPAÑA/Biblioteca_Absoluta/` a `_pdfs/` local.
2. Extraído texto vectorial (`pymupdf`) de las 6 páginas del PDF "Mapas de Barrowmaze 10th Ebook OSR 2022.pdf". Los números son **texto vectorial**, no imagen, así que se leen perfectos sin OCR.
3. Confirmado layout 3x2 del stitched: top row [mod 234, 235, 238] / bottom row [mod 236, 237, 239].
4. Per-page bbox detection para mapping pt → coords SVG 800x744.
5. Generado `barrowmaze_room_coords_v3.json` con **391 IDs reales** (380 numéricos + 9 Q + 8 D + sub-rooms 92A/158A/etc).
6. Validado side-by-side: `_compare_v3_p3.jpg` muestra que markers v3 caen sobre los rooms reales del módulo.

### Cambios específicos del cockpit V6k6:
- URL de carga: `barrowmaze_room_coords.json` → `barrowmaze_room_coords_v3.json`.
- Markers iPad: radius 22 → **12** (los HIPER-visibles V6k4 tapaban el grid).
- Markers desktop: 8 (sin cambio).
- Borders proporcionales al tamaño (más finos en mobile).
- Modal de room: **bloqueado el lookup en `_roomsFullCache`** (la tabla v1 estaba mal asociada). Ahora muestra solo el ID confirmado y un mensaje "re-extracción de descripción pendiente".
- Title: v6k5 → v6k6.
- Overlay diagnóstico: V6k4 → V6k6.

---

## ⚠️ Pendiente importante: re-extracción de `rooms_full.json`

El cockpit V6k6 muestra los markers en posiciones correctas, pero **no muestra descripciones por room** (la tabla v1 no es confiable). Para recuperar descripciones:

1. **Re-extraer del PDF módulo completo** (`Barrowmaze 10th Ebook OSR 2022.pdf`, 264 páginas) con un parser que:
   - Use IDs reales del módulo (Q1, D1, 92A, etc.).
   - Sea column-aware (el extractor v1 falló con bleed entre columnas).
   - Asocie cada heading a su párrafo correspondiente.
2. **Alternativa**: Marcos agrega descripciones a mano para los rooms que importan en cada sesión.

Esto es ~3-4h de trabajo de scripting + validación. No urgente para mañana — el cockpit funciona sin desc, los markers ya son confiables.

---

## 📂 Archivos críticos V6k6

```
Cemanahuac/
├── prototipo_v6k6.html              ← LIVE
├── _apply_v6k6.py                   ← script de patches V6k6
├── _extract_pdf_room_coords.py      ← extractor del PDF de mapas (vectorial)
├── _build_coords_v3.py              ← genera room_coords_v3.json (gitignored)
├── _layout_check.py                 ← confirma layout 3x2 del stitched
├── _validate_pdf_extraction.py      ← genera _pdf_validation/ (markers sobre PDF)
├── _generate_validation_v2.py       ← batches con markers v2/v3 sobre stitched
├── _generate_validation_batches.py  ← batches con markers v1 (legacy/comparison)
├── _compare_zoom.py                 ← side-by-side PDF vs stitched zoom
├── HANDOFF_v6k6_continuar.md        ← este archivo
├── HANDOFF_v6k5_continuar.md        ← anterior
├── _pdfs/                           ← PDFs source (gitignored, 175MB)
│   ├── Barrowmaze 10th Ebook OSR 2022.pdf  (modulo completo, 264p)
│   └── Mapas de Barrowmaze 10th Ebook OSR 2022.pdf  (6 mapas, 3.5MB)
├── _pdf_validation/                 ← imagenes de validacion (PDF + markers verdes)
├── _validation_batches_v3/          ← batches v3 sobre stitched
├── _compare_v3_p3.jpg               ← prueba clave: PDF p.3 vs stitched bot-left
└── maps/
    ├── barrowmaze_bg_1920.webp      ← stitched 1920x1785 (sin cambio)
    ├── barrowmaze_room_coords.json  ← v1 (OBSOLETO, IDs arbitrarios)
    ├── barrowmaze_room_coords_v2.json ← v2 (gitignored, intermedio)
    ├── barrowmaze_room_coords_v3.json ← v3 (LIVE, IDs reales del PDF)
    └── barrowmaze_rooms_full.json   ← OBSOLETO, descripciones mal asociadas
```

---

## 🎯 Para pegar en una sesión nueva de Claude

```
Continuá el cockpit Valakhan, mesa ACKS Novatos ONG, Marcos Cabobianco,
party en Sala 74A Barrowmaze. Live: https://mc-prism.pages.dev/cockpit
Versión actual: v6k6.

WORKING DIRS:
- C:/Users/Usuario/Desktop/Cemanahuac/   (cockpit-valakhan repo, prototipo_v6k6.html)
- C:/Users/Usuario/COWORK/ATEM/mc-prism-deploy/  (Cloudflare deploy folder)

PDFs SOURCE (en G:):
- G:/Mi unidad/02_ROL_Y_MEGACAMPAÑA/Biblioteca_Absoluta/Barrowmaze 10th Ebook OSR 2022.pdf
- G:/Mi unidad/02_ROL_Y_MEGACAMPAÑA/Biblioteca_Absoluta/Mapas de Barrowmaze 10th Ebook OSR 2022.pdf
(También copiados a _pdfs/ local, gitignored)

CREDENCIALES configuradas (no pedir auth):
- gh CLI logueado (marcoscabobianco-maker)
- wrangler logueado para Cloudflare Pages (mc-prism)
- git credential helper persistido

DEPLOY PATTERN (validado V6k6):
  1. _apply_v6kY.py lee prototipo_v6kX.html y escribe v6kY (con count guards)
  2. PYTHONIOENCODING=utf-8 python _apply_v6kY.py
  3. Validar JS: extraer scripts NO-json + node --check
     IMPORTANTE: cuidar quoting de strings JS dentro de Python
  4. cp prototipo_v6kY.html mc-prism-deploy/cockpit.html
  5. Si cambian assets (JSON, imgs), copiar a mc-prism-deploy/maps/ también
  6. cd mc-prism-deploy && npx wrangler pages deploy . --project-name=mc-prism
     (si tira 502, reintentar con backoff 30s — hubo outage en 2026-05-01)
  7. git add + commit + push

ESTADO ACTUAL (V6k6):
- Mapa Barrowmaze real (5256×4888 stitched 6 páginas mod 234-239) con walls vectorizadas, 90.8% reachable.
- 391 markers REALES del PDF vectorial (numéricos + Q1-Q9 + D1-D8 + sub-rooms 92A/158A).
- Markers iPad radius 12 (antes 22 tapaban grid). Desktop radius 8.
- Toggle 🜍 Ocultar/Mostrar markers (V6k5).
- PWA fullscreen fix (100dvh + safe-area-inset-bottom, V6k5).
- Título dinámico desde JS (V6k5).
- Tracker tiempo + raciones + rest.
- Wandering auto-switch combat tras 1.8s.
- Trampas DM-strict.
- Saves auto ACKS + Mortal Wounds inline.
- Search/Listen integrados.
- 27 illustrations + bestiario 120 criaturas.
- Modal room: solo muestra ID + mensaje (rooms_full v1 era basura).

PENDIENTE IMPORTANTE:
- Re-extraer rooms_full.json del módulo PDF completo con IDs reales y column-aware.

NO HACER:
- Volver a usar barrowmaze_room_coords.json (v1, IDs arbitrarios).
- Mostrar descripciones de barrowmaze_rooms_full.json (mal asociadas).
- Tocar Arden Vul (Marcos descartó).
- Modificar mc-prism Next.js.
```

---

## 🔑 Permisos confirmados

OK sin preguntar:
- ✅ Editar archivos en `Cemanahuac/`
- ✅ Copiar a `mc-prism-deploy/` y deploy a CF Pages
- ✅ Commit + push a `cockpit-valakhan`
- ✅ Re-extraer assets del PDF Barrowmaze (uso personal, módulo comprado)
- ✅ Leer (no escribir) PDFs en `G:/Mi unidad/02_ROL_Y_MEGACAMPAÑA/`

NO autorizado sin preguntar:
- ❌ Modificar `mc-prism` Next.js repo
- ❌ Escribir en `G:/`
- ❌ Tocar credenciales/tokens
- ❌ `git push --force` o `git reset --hard`

---

## 📊 Wildcard mode summary (V5z → V6k6)

| V | Foco | Deploy |
|---|---|---|
| V5z–V6h | (ver handoffs anteriores) | varios |
| V6i | Wallmap v2 (1.2% → 90.8%) + ACKS RAW + DM ctrl+click | 9ffd7258 |
| V6j | Rooms re-extracted clean + wandering auto-combat + traps DM-strict | (intermedio) |
| V6k | Illustrations (27) + Bestiario (120) | 2c7ddf5b |
| V6k1 | Cache-bust automático | 7fb7ed13 |
| V6k2 | iPad fixes: responsive + bg liviano + touch | 9ee37a15 |
| V6k3 | iPad markers grandes + layout vertical + modales fullscreen | 3e0e927c |
| V6k4 | Markers HIPER-visibles + diagnóstico overlay | 5fa4c0f2 |
| V6k5 | PWA fullscreen + toggle markers + título dinámico | b5eadd82 |
| V6k6 | **Markers REALES (PDF vectorial v3) + iPad markers chicos** | 17715a27 |

— Cockpit Valakhan v6k6 · 2026-05-02
