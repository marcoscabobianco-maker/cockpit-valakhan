# HANDOFF v6k4 · Cockpit Valakhan · Continuar iteración

**Fecha cierre**: 2026-05-01
**Live URL**: https://mc-prism.pages.dev/cockpit
**Última versión**: V6k4
**Última commit**: e6090d2
**Última deploy CF**: 5fa4c0f2

## ⚠️ Pendientes urgentes para próxima sesión

1. **Título dinámico de la pestaña**: actualmente queda fijo en "Cockpit V6kX — descripción larga". Marcos quiere que aparezca a la izquierda de "Valakhan ATEM Farol Club" (nombre del proyecto) y se reemplace automáticamente por la última versión. Patch: agregar variable `_VERSION = 'v6k5'` en JS, setear `document.title` desde JS al cargar.

2. **Marcos reporta no ver markers en Desktop V6K3**: ya deployé V6k4 con fix HIPER-visible (radio 22 mobile, 8 desktop, doble border negro+blanco+dorado, sin shadowBlur). **Si sigue sin ver markers después de hard refresh**, hay bug más profundo. Diagnóstico V6k4 muestra overlay top-left del canvas: `🛠 V6k4 · Mobile=YES/no · 🜍 Markers visibles: N (DM/player)`. Si N=0, no se cargó `_roomCoordsCache` (verificar fetch de `maps/barrowmaze_room_coords.json`).

3. **Image limit en sesiones de Claude**: cada vez que se procesan muchos PNGs grandes del PDF, se llega al límite ~2000px y la sesión bloquea futuras imágenes. Workaround: en futuras extracciones del PDF, downscale agresivo (max 1500px) ANTES de leer.

4. **Persistente bug Sala 151** y otras con bleed leve de columna: el extractor v6j (50/50 column split) deja text bleed en algunas rooms. Smart-column extractor v6k3 falló (53 vs 373 rooms). Pendiente: extractor híbrido.

---

## 🎯 Para pegar en una sesión nueva de Claude

Copiá este bloque tal cual:

```
Continuá el cockpit Valakhan, mesa ACKS Novatos ONG, Marcos Cabobianco,
party en Sala 74A Barrowmaze. Live: https://mc-prism.pages.dev/cockpit
Commit actual: 82311de · Deploy CF: 3e0e927c · Versión: V6k3.

WORKING DIRS:
- C:/Users/Usuario/Desktop/Cemanahuac/   (cockpit-valakhan repo, prototipo_v6k3.html)
- C:/Users/Usuario/COWORK/ATEM/mc-prism-deploy/  (Cloudflare deploy folder)

CREDENCIALES ya configuradas:
- gh CLI logueado (marcoscabobianco-maker)
- wrangler logueado para Cloudflare Pages (mc-prism)
- git credential helper persistido (no pide auth en push)

DEPLOY PATTERN:
  1. cp prototipo_v6kX.html prototipo_v6kY.html
  2. Crear _apply_v6kY.py con re.sub patches (con count= guard contra duplicates)
  3. PYTHONIOENCODING=utf-8 python _apply_v6kY.py
  4. Validar JS: extraer scripts y node --check
  5. cp prototipo_v6kY.html mc-prism-deploy/cockpit.html
  6. cd mc-prism-deploy && npx wrangler pages deploy . --project-name=mc-prism --commit-message="..."
  7. git add + commit + push (sale auto con credential helper)

ESTADO ACTUAL (V6k3):
- Mapa Barrowmaze real (6 páginas stitched 5256×4888) con walls vectorizadas:
  90.8% reachability desde Sala 74A.
- 375 markers dorados (radio 14 + halo en mobile, 6 desktop) clickeables → modal
  con info de room (244/375 con desc detallada).
- 27 illustrations del módulo extraídas, 17 rooms con illustration linkeada.
- 120 criaturas en bestiario Barrowmaze (modal con buscador).
- Tracker tiempo (hora del día + descanso nocturno + raciones + progress bars).
- Wandering check auto-switch a combat panel después de 1.8s.
- Trampas DM-strict: vista jugador NO ve nada hasta triggered.
- Saves auto ACKS por clase + Mortal Wounds inline (HP=0).
- Search/Listen integrados con tirada por clase del PC vanguardia.
- iPad fixes: viewport detection, bg liviano (1920w 347KB), markers grandes,
  layout vertical estricto, modales 95% fullscreen, botones 44px touch.

PRÓXIMOS PASOS PROBABLES:
1. Spell slots para Silas (warlock) y Dimitri (mage).
2. XP tracker post-sesión (combat HD + treasure 1gp=1xp).
3. Validar mapping illustration #N ↔ page real (heurístico ahora; algunas
   pueden estar offset si las primeras pages del appendix son character sheets).
4. Mejorar parser rooms para Sala 151 y otras con bleed leve de columna.
5. Ajustar wandering tabla por nivel del módulo (actualmente una sola tabla 1d20).

REPOS:
- Cockpit: github.com/marcoscabobianco-maker/cockpit-valakhan
- mc-prism (Vercel separado): github.com/marcoscabobianco-maker/mc-prism
  (NO se modifica desde acá)

NO HACER:
- Tocar Arden Vul (V6f hizo viewer pero Marcos lo descartó por ahora).
- Volver al fog-paint canvas viejo (descartado).
- Reintroducir infravisión (no existe en ACKS, solo Detect Hidden de thief).
- Modificar mc-prism Next.js (otro repo separado).
- Re-extraer rooms con parser smart-column (intenté en v6k3, dio 53 vs 373,
  worse). El extractor v6j (50/50 column split) es el bueno.
```

---

## 📋 Test plan inmediato (ya en V6k3 live)

### En iPad Pro 12.9
1. Abrir `https://mc-prism.pages.dev/cockpit`.
2. Title debe decir **V6k3**.
3. Tab Dungeon → Barrowmaze.
4. Esperar que aparezca el mapa con la party celeste en Sala 74A.
5. **Markers dorados deben ser bien visibles** (bolitas grandes con número adentro).
6. Click en un marker → modal con info (probá Sala 12, 47, 74, 143, 151).
7. Layout debe ser **vertical** (cards apiladas, no botones por fuera).
8. Modal debe ser casi fullscreen (95% del viewport).

### En desktop
1. Abrir misma URL.
2. Layout horizontal (mapa izquierda, cards derecha).
3. Markers más chicos (radio 6, no 14) — diseño desktop original.
4. Click marker → modal centrado de 640px.

### Funcionalidad core a verificar (ambos)
- Movimiento con flechitas / WASD.
- Tecla `G`: toggle DM ↔ Jugadores.
- Tecla `T`: +1 turno.
- Shift+click cell: colocar trampa (DM mode).
- Ctrl+click cell: abrir/cerrar wallmap (DM mode override).
- Banner alertas: rest DUE, wandering DUE, antorcha agotada, atardecer/noche.
- Botón "🜍 Bestiario Barrowmaze" en Quick Refs → modal con 120 criaturas + buscador.
- Wandering positivo: debería disparar banner + auto-switch a Combat después 1.8s.

---

## 📂 Archivos críticos en el repo

```
Cemanahuac/
├── prototipo_v6k3.html              ← LIVE, último HTML
├── _apply_v6k3.py                   ← script de patches V6k3
├── _apply_v6kN.py                   ← scripts anteriores (k2, k1, V6j, V6i, V6h, V6g, V6f, V6e, V6d, V6c, V6b, V6a, V5z, V5y, V5x, V5w, V5v)
├── CHANGELOG.md                     ← changelog completo
├── HANDOFF_v6k3_continuar.md        ← este archivo
├── HANDOFF_v6k_nocturno.md          ← handoff anterior (V6k details)
├── HANDOFF_PDF_VECTOR_COORDS.md     ← detalles del pipeline de vectorización
├── HANDOFF_ARDEN_VUL_INTEGRATION.md ← Arden Vul (descartado por Marcos)
├── campaigns/
│   ├── novatos_ravenloft.json       ← party (11 PCs) + dungeons
│   └── _barrowmaze_rooms_full.json  ← legacy (no usado, ver maps/)
└── maps/
    ├── barrowmaze_bg_1280.webp      ← mapa lite 1280w (200 KB)
    ├── barrowmaze_bg_1920.webp      ← mapa mid 1920w (347 KB) — usado por iPad
    ├── barrowmaze_room_coords.json  ← 375 rooms x/y SVG 800x744
    └── barrowmaze_rooms_full.json   ← 373 rooms con title/summary/narrative/stats/treasure

mc-prism-deploy/                     ← deploy folder (no se commitea)
├── cockpit.html                     ← copia del prototipo_v6k3.html
└── maps/
    ├── barrowmaze_real.webp         ← 2628w (557 KB) — desktop default
    ├── barrowmaze_real_mobile.webp  ← 1920w (347 KB) — mobile/iPad default
    ├── wallmap_barrowmaze.json      ← 87 KB, 203×219 cells, 90.8% reachable
    ├── barrowmaze_room_coords.json  (mismo)
    ├── barrowmaze_rooms_full.json   (mismo)
    ├── barrowmaze_bestiary.json     ← 120 creatures (27 KB)
    └── barrowmaze_illustrations/
        ├── _index.json              ← mapping room → illustration_url
        └── illustration_NN_pXXX.webp × 27 (~9 MB total)
```

---

## 🐛 Bugs / limitaciones conocidos

1. **Algunas rooms con bleed de columna** (Sala 151 dice "the area immediately"):
   intenté smart-column extractor pero salió peor (53 vs 373 rooms). Mantengo
   el v6j (50/50 column split simple). Pendiente mejor solución.

2. **Mapping illustration #N ↔ page**: heurístico. Asume orden secuencial en
   appendix (page 212 = #1, page 213 = #2, ...). Las primeras pages del appendix
   pueden ser character sheets / handouts (page 208 confirmé que es character sheet,
   no illustration). Mapping puede estar offset 4-6 pages. Validar abriendo PDF.

3. **Sala 143 aislada en wallmap** (94% sample, 16/17 reachable). Si querés
   acceder, ctrl+click en una cell del pasillo en DM mode = abrir manual.

4. **Algunas categorías de bestiario duplicadas singular/plural** (Skeleton/Skeletons,
   Mummy/Mummies). Es lo que dice el módulo literal.

5. **Wandering tabla genérica** para todo el dungeon. El módulo Barrowmaze tiene
   tablas distintas por área (Antechamber, Mounds, levels 1-3). Pendiente extraer.

6. **No hay spell slots** para casters (Silas warlock, Dimitri mage).

7. **No hay XP tracker** post-sesión.

---

## 🔑 Permisos confirmados

Todos estos están OK sin necesidad de pedir más:
- ✅ Editar archivos en `Cemanahuac/` (HTML, .py, .md, .json en maps/ y campaigns/)
- ✅ Copiar a `mc-prism-deploy/` y deploy a Cloudflare Pages (wrangler ya logueado)
- ✅ Commit + push a `cockpit-valakhan` (gh CLI + helper persistido)
- ✅ Re-extraer assets del PDF Barrowmaze (uso personal, módulo comprado)
- ✅ Generar imágenes derivadas del PDF (illustrations, wallmaps, etc)

NO autorizado sin preguntar:
- ❌ Modificar `mc-prism` Next.js repo (otro proyecto separado)
- ❌ Subir cosas al drive G: (solo lectura)
- ❌ Tocar credenciales/tokens
- ❌ `git push --force` o `git reset --hard` (a menos que pida explícito)

---

## 📊 Wildcard mode summary (V5z → V6k3)

| V | Foco | Patches | Deploy |
|---|---|---|---|
| V5z | Hora del día + raciones + descanso nocturno + progress bars | 7 | b0141318 |
| V6a | Encuentro pipeline + tabla Barrowmaze + banner combate | 4 | (intermedio) |
| V6b | PC roster (11 novatos) + formación + lightBearer | 3 | (intermedio) |
| V6c | Click rooms keyed (244 rooms con desc/treasure) | 5 | 770be4f5 |
| V6d | Trampas place + detect + trigger | 8 | (intermedio) |
| V6e | ACKS Quick refs + link Assistant + atajos | 2 | 36145f45 |
| V6f | Arden Vul multi-level viewer (DESCARTADO por Marcos) | 4 | d50b3d23 |
| V6g | Saves auto + Mortal Wounds inline | 5 | (intermedio) |
| V6h | Search/Listen integrados | 3 | 5ed40691 |
| V6i | **CRITICAL** Wallmap v2 (1.2% → 90.8% reachable) + ACKS RAW + DM ctrl+click | 7 | 9ffd7258 |
| V6j | Rooms re-extracted clean + wandering auto-combat + traps DM-strict | 4 | (intermedio) |
| V6k | Illustrations (27) + Bestiario (120) | 5 | 2c7ddf5b |
| V6k1 | Cache-bust automático URL params | inline | 7fb7ed13 |
| V6k2 | iPad fixes: responsive + bg liviano + touch | 5 | 9ee37a15 |
| V6k3 | iPad markers grandes + layout vertical + modales fullscreen | 3 | 3e0e927c |

**Total**: 65 patches, 14 versiones, 12 deploys en CF Pages, 9 commits a GitHub.

— Cockpit Valakhan V6k3 · 2026-05-01
