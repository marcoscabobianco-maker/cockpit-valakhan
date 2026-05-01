# HANDOFF v6k5 · Cockpit Valakhan · Continuar iteración

**Fecha cierre**: 2026-05-01
**Live URL**: https://mc-prism.pages.dev/cockpit
**Última versión**: v6k5
**Última commit**: (pendiente push, ver `git log` después de commit)
**Última deploy CF**: (ver output de `wrangler pages deploy` o tail del background bash bf01oytt4)

---

## 🆕 Cambios V6k5 (sobre V6k4)

1. **iOS PWA fullscreen fix** (cuando se ancla a pantalla de inicio del iPad):
   - `:root` ganó `--safe-bottom: env(safe-area-inset-bottom, 0px)`.
   - `html, body` cambian `100vh` → `100dvh` (dynamic viewport height).
   - `main` ahora es `calc(100dvh - 130px - var(--safe-bottom))`.
   - `.mode-view` agrega `padding-bottom: calc(12px + var(--safe-bottom))`.
   - `.session-list` y siblings usan `100dvh` + safe-bottom.
   - `.detail-content` modal: `92vh` → `92dvh`.
   - **Por qué**: en iOS standalone (Add to Home Screen), `100vh` no respeta la home indicator y los botones del fondo quedan tapados. `100dvh` + `safe-area-inset-bottom` resuelven ambos.

2. **Toggle markers ON/OFF** (iPad usability):
   - Variable global `_markersHidden` (default `false`).
   - Función `toggleMarkers()`.
   - Bloque de dibujo de markers (línea ~11321) ahora chequea `&& !_markersHidden`.
   - Botón flotante `🜍 Ocultar markers` / `🜍 Mostrar markers` posicionado `position:absolute; top:8px; right:8px` dentro de `.grid-real-wrap` (que es `position:relative; overflow:auto`, así que el botón NO scrollea con el canvas).
   - **Por qué**: los markers HIPER-visibles V6k4 (radio 22 mobile, doble border + dorado) tapan el grid en iPad y no dejan dibujar mapas analógicos. Desktop no tiene este problema (radio 8).

3. **Título dinámico**:
   - Constante JS `_COCKPIT_VERSION = "v6k5"` inyectada inline en el `<head>`.
   - `document.title = "Cockpit " + _COCKPIT_VERSION + " · Valakhan ATEM Farol Club"` se ejecuta apenas se parsea el script.
   - **Por qué**: antes el título quedaba hardcoded en cada release. Ahora basta con cambiar la constante.

---

## ⚠️ Pendientes urgentes (sin resolver en V6k5)

1. **Marcos no ve markers en Desktop V6k3** (reportado antes de V6k4):
   - V6k4 hizo markers HIPER-visibles (radio 22 mobile, 8 desktop, doble border negro+blanco+dorado).
   - V6k5 mantiene esto + agrega toggle.
   - **Si después de V6k5 + hard refresh sigue sin ver markers en desktop**, hay un bug más profundo. Diagnóstico V6k4 muestra overlay top-left del canvas: `🛠 V6k4 · Mobile=YES/no · 🜍 Markers visibles: N (DM/player)`. Si N=0, no se cargó `_roomCoordsCache` (verificar fetch de `maps/barrowmaze_room_coords.json` en DevTools Network).
   - Nota: el overlay diagnóstico todavía dice "V6k4" en V6k5 (no lo cambié). Cosmético.

2. **Image limit en sesiones de Claude**: cada vez que se procesan muchos PNGs grandes del PDF, se llega al límite ~2000px y la sesión bloquea futuras imágenes. Workaround: en futuras extracciones del PDF, downscale agresivo (max 1500px) ANTES de leer.

3. **Bleed Sala 151 y otras rooms**: el extractor v6j (50/50 column split) deja text bleed cuando una columna del PDF se mete en la otra. Smart-column extractor v6k3 falló (53 vs 373 rooms). Pendiente: extractor híbrido (heurístico de detección de columna real + fallback a 50/50).

---

## 🎯 Para pegar en una sesión nueva de Claude

```
Continuá el cockpit Valakhan, mesa ACKS Novatos ONG, Marcos Cabobianco,
party en Sala 74A Barrowmaze. Live: https://mc-prism.pages.dev/cockpit
Versión actual: v6k5.

WORKING DIRS:
- C:/Users/Usuario/Desktop/Cemanahuac/   (cockpit-valakhan repo, prototipo_v6k5.html)
- C:/Users/Usuario/COWORK/ATEM/mc-prism-deploy/  (Cloudflare deploy folder)

CREDENCIALES configuradas (no pedir auth):
- gh CLI logueado (marcoscabobianco-maker)
- wrangler logueado para Cloudflare Pages (mc-prism)
- git credential helper persistido

DEPLOY PATTERN (validado en V6k5):
  1. cp prototipo_v6kX.html prototipo_v6kY.html  (o que el _apply lo escriba directo)
  2. Crear _apply_v6kY.py con re.sub patches (con count guard contra duplicates)
  3. PYTHONIOENCODING=utf-8 python _apply_v6kY.py
  4. Validar JS: extraer scripts NO-json + node --check
     (ver _validate_v6k5.py — filtra type="application/json")
  5. cp prototipo_v6kY.html mc-prism-deploy/cockpit.html
  6. cd mc-prism-deploy && npx wrangler pages deploy . --project-name=mc-prism
     (si tira 502 Bad Gateway, reintentar con backoff 30s — pasa de a ratos)
  7. git add + commit + push (auto con credential helper)

ESTADO ACTUAL (V6k5):
- Mapa Barrowmaze real (5256×4888 stitched) con walls vectorizadas, 90.8% reachable.
- 375 markers dorados clickeables → modal con info room (244/375 con desc detallada).
- 27 illustrations + bestiario 120 criaturas.
- Tracker tiempo + raciones + rest.
- Wandering auto-switch a combat tras 1.8s.
- Trampas DM-strict.
- Saves auto ACKS + Mortal Wounds inline.
- Search/Listen integrados.
- iPad: viewport detection, bg liviano (1920w 347KB), markers grandes, layout vertical, modales 95%, botones 44px touch.
- V6k5: PWA standalone fullscreen fix, toggle markers, título dinámico.

NO HACER:
- Tocar Arden Vul (Marcos lo descartó por ahora).
- Volver al fog-paint canvas viejo.
- Reintroducir infravisión (no existe en ACKS).
- Modificar mc-prism Next.js (otro repo).
- Re-extraer rooms con parser smart-column (intenté en v6k3, peor).
```

---

## 📂 Archivos críticos

```
Cemanahuac/
├── prototipo_v6k5.html              ← LIVE
├── _apply_v6k5.py                   ← script de patches V6k5
├── _validate_v6k5.py                ← extractor JS para node --check (filtra JSON)
├── _apply_v6kN.py                   ← scripts anteriores (k4, k3, k2, k1, V6j ... V5v)
├── HANDOFF_v6k5_continuar.md        ← este archivo
├── HANDOFF_v6k4_continuar.md        ← anterior
├── HANDOFF_v6k_nocturno.md          ← V6k details
├── CHANGELOG.md
├── campaigns/novatos_ravenloft.json ← party (11 PCs) + dungeons
└── maps/
    ├── barrowmaze_bg_1920.webp      ← mapa mid 1920w usado por iPad
    ├── barrowmaze_room_coords.json  ← 375 rooms x/y SVG 800x744
    └── barrowmaze_rooms_full.json   ← 373 rooms con desc

mc-prism-deploy/
├── cockpit.html                     ← copia del prototipo_v6k5.html
└── maps/
    ├── barrowmaze_real.webp         ← desktop (557KB)
    ├── barrowmaze_real_mobile.webp  ← mobile/iPad (347KB)
    ├── wallmap_barrowmaze.json      ← 90.8% reachable
    ├── barrowmaze_room_coords.json
    ├── barrowmaze_rooms_full.json
    ├── barrowmaze_bestiary.json
    └── barrowmaze_illustrations/    ← 27 webp + _index.json
```

---

## 🐛 Bugs / limitaciones conocidos (heredados)

1. Bleed columna en Sala 151 y otras (ver pendientes urgentes #3).
2. Mapping illustration #N ↔ page heurístico (puede estar offset 4-6 pages).
3. Sala 143 aislada en wallmap (ctrl+click cell para abrir manual).
4. Categorías bestiario duplicadas singular/plural.
5. Wandering tabla genérica (módulo tiene tablas distintas por área).
6. No hay spell slots para casters (Silas warlock, Dimitri mage).
7. No hay XP tracker post-sesión.
8. Overlay diagnóstico canvas todavía dice "V6k4" en V6k5 (cosmético).

---

## 🔑 Permisos confirmados

OK sin preguntar:
- ✅ Editar archivos en `Cemanahuac/`
- ✅ Copiar a `mc-prism-deploy/` y deploy a CF Pages
- ✅ Commit + push a `cockpit-valakhan`
- ✅ Re-extraer assets del PDF Barrowmaze (uso personal, módulo comprado)

NO autorizado sin preguntar:
- ❌ Modificar `mc-prism` Next.js repo
- ❌ Subir cosas al drive G:
- ❌ Tocar credenciales/tokens
- ❌ `git push --force` o `git reset --hard`

---

## 📊 Wildcard mode summary (V5z → V6k5)

| V | Foco | Patches | Deploy |
|---|---|---|---|
| V5z | Hora del día + raciones + descanso nocturno | 7 | b0141318 |
| V6a | Encuentro pipeline + tabla Barrowmaze | 4 | (intermedio) |
| V6b | PC roster (11 novatos) + formación | 3 | (intermedio) |
| V6c | Click rooms keyed (244 rooms con desc/treasure) | 5 | 770be4f5 |
| V6d | Trampas place + detect + trigger | 8 | (intermedio) |
| V6e | ACKS Quick refs + atajos | 2 | 36145f45 |
| V6f | Arden Vul multi-level (DESCARTADO) | 4 | d50b3d23 |
| V6g | Saves auto + Mortal Wounds inline | 5 | (intermedio) |
| V6h | Search/Listen integrados | 3 | 5ed40691 |
| V6i | Wallmap v2 (1.2% → 90.8%) + ACKS RAW + DM ctrl+click | 7 | 9ffd7258 |
| V6j | Rooms re-extracted clean + wandering auto-combat + traps DM-strict | 4 | (intermedio) |
| V6k | Illustrations (27) + Bestiario (120) | 5 | 2c7ddf5b |
| V6k1 | Cache-bust automático | inline | 7fb7ed13 |
| V6k2 | iPad fixes: responsive + bg liviano + touch | 5 | 9ee37a15 |
| V6k3 | iPad markers grandes + layout vertical + modales fullscreen | 3 | 3e0e927c |
| V6k4 | Markers HIPER-visibles (radio 22, doble border) + diagnóstico overlay | 3 | 5fa4c0f2 |
| V6k5 | **PWA fullscreen fix + toggle markers + título dinámico** | 11 | (this) |

**Total**: 76 patches, 16 versiones.

— Cockpit Valakhan v6k5 · 2026-05-01
