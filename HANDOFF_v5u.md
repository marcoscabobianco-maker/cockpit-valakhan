# Handoff v5u → próxima sesión (LATEST)

**Fecha**: 2026-04-30
**Estado**: v5u LIVE en https://mc-prism.pages.dev/cockpit.html
**Repos**:
- Cockpit: https://github.com/marcoscabobianco-maker/cockpit-valakhan (commit 7f2e2a9)
- mc-prism: github.com:marcoscabobianco-maker/mc-prism (commit 4578ef1)

## Cambio crítico v5t → v5u

El **fog-paint-with-finger** anterior **no funcionaba bien** en sesión real (Marcos lo confirmó). Lo reemplacé por un **Grid Tactical Crawler** vanilla JS que es port directo del componente DungeonCrawler.tsx que Marcos tenía en su otra app mc-prism (Next.js/React).

### Grid Crawler features
- Mapa ASCII 20×11 (#=wall, .=floor, D=door)
- Fog of war computacional: `seen` (memoria) + `visibleNow` (radio 3 manhattan desde player)
- Player marker emerald que se mueve con touch buttons o keyboard arrows/WASD
- Mapa **editable en runtime** via textarea
- Persistencia state.dungeon.grid en localStorage
- Reset niebla, Reset mapa, Aplicar mapa custom
- **Es la vista DEFAULT del modo Dungeon para Barrowmaze** (en lugar del fog-paint).

### Otras dos vistas siguen disponibles
- "Room graph" (rooms del JSON con conexiones SVG)
- "📍 Mapa real" (imagen Cía Zafiro con markers POI/notas/party — sin fog paint anterior)

## Cambios paralelos en mc-prism (Next.js)

Marcos pasó 2 git patches + DungeonCrawler component + doc. Aplicado:
- `nav-sidebar.tsx`: nuevo item "Dungeon ACKS" 🕯 + DarkModeToggle bug fix
- `lib/campaign-parser.ts`: agregada def "acks-megadungeon" como Campaña Activa
- `components/dungeon/dungeon-crawler.tsx`: componente React (el que hizo Marcos)
- `app/dungeon/page.tsx`: ruta /dungeon
- `sources/campaigns/acks-megadungeon/mesa-acks-megadungeon.md`: doc

## Próxima sesión Claude Code: prompt de arranque

```
Continuá cockpit-valakhan + mc-prism. Lee:
- https://raw.githubusercontent.com/marcoscabobianco-maker/cockpit-valakhan/main/HANDOFF_v5u.md
- https://raw.githubusercontent.com/marcoscabobianco-maker/cockpit-valakhan/main/CHANGELOG.md

Working dirs:
- Cockpit: C:/Users/Usuario/Desktop/Cemanahuac/
- mc-prism: C:/Users/Usuario/CODE/mc-prism/

Deploys:
- Cockpit: cd C:/Users/Usuario/COWORK/ATEM/mc-prism-deploy && npx wrangler pages deploy . --project-name=mc-prism
- mc-prism: Vercel (auto-deploy desde GitHub)

Wrangler logueado, gh CLI logueado como marcoscabobianco-maker. mc-prism repo
usa SSH (git@github.com:marcoscabobianco-maker/mc-prism.git), funciona.

Sigue desde v5u. Nueva prioridad #1: marcadores PC individuales sobre el grid
(no solo el "C" único del party).
```

## Pendientes (orden de prioridad)

### 🔴 Alta prioridad
1. **Marcadores PC individuales sobre el Grid Crawler**: cada PC con su dot+initial separados (no solo el party "C"). Marcos pidió esto explícitamente.
2. **Nombre del Patriarca/Abad** introducido en S3 (placeholder en NPCs).

### 🟡 Media
3. **Atlas mapas Barrowmaze** del PDF cuando avancen más allá de zona Cía Zafiro.
4. **Inventario simple por PC** (lista de items + gold).
5. **Calendar enriquecido con festividades** Aurëpos/Ravenloft.

### 🟢 Baja / explorar
6. **Backlog técnico de la mesa ACKS MegaDungeon** (de mesa-acks-megadungeon.md):
   - Sistema rumor seeds + objetivos por sesión
   - Generador encuentros por estrato
   - Recap automático para preparación de sesión

## NO HACER
- ❌ Long/short rest (ACKS NO tiene, es 5e)
- ❌ Reimplementar Spells/Bestiary del Assistant en cockpit
- ❌ Vectorizar pasillos del Barrowmaze (Marcos ya descartó)
- ❌ Volver al fog-paint canvas anterior (no funcionaba)

## Fases completas (commits de referencia)

| Fase | Versión | Commit | Qué |
|---|---|---|---|
| A | v5o | 9143ab5 | Bestiario limpio + Settlement Panel |
| B | v5p | a4a54a3 | PCs panel mode |
| C | v5q | c84ce57 | Notes index + Session export |
| D | v5r | 198c6d4 | Lunar phases + rumor table |
| E | v5s | 97e117e | District encounters |
| G+H | v5t | 31f2997 | Path por día + auto-encounter |
| I | v5u | 7f2e2a9 | **Grid tactical crawler (default)** |
| Doc | - | aec2004 + dc9e997 | README + CHANGELOG + HANDOFF |
| mc-prism | - | 4578ef1 | nav + parser + DungeonCrawler + doc |

## Status del context al cerrar

- ~95% del millón de tokens consumido en esta sesión
- Todos los cambios pusheados a ambos repos
- Cockpit deployado en Cloudflare
- mc-prism pusheado a GitHub (Vercel auto-deploya)
- localStorage del cockpit persiste en cliente

**El proyecto continúa intacto cuando se corte la sesión. Próxima Claude empieza limpio leyendo este handoff.**

---

## Update final 2026-04-30: Dungeon Atlas en mc-prism

**5 páginas Barrowmaze extraídas a PNG** (pp 233-237) en `mc-prism/public/dungeons/barrowmaze/page_*.png`. Página 234 = donde está la party (Sala 74A Mongrelmen).

**mc-prism nueva arquitectura**:
- `lib/dungeon-map-parser.ts` — lee JSONs de `sources/dungeons/*.json`
- `components/dungeon/fog-map-viewer.tsx` — SVG fog overlay sobre imagen, radio 3 manhattan
- `sources/dungeons/barrowmaze.json` — 5 secciones con conexiones page→page
- `app/dungeon/page.tsx` — biblioteca de módulos (reemplaza al DungeonCrawler simple)
- `app/dungeon/[module]/page.tsx` — ruta dinámica por módulo

**Pendiente próxima sesión**:
- Marcos pidió hacer lo mismo con **Arden Vul** (PDF en `G:/Mi unidad/02_ROL_Y_MEGACAMPAÑA/Biblioteca_Absoluta/The Halls of Arden Vul (1e,OSRIC) (1).pdf`). Es más grande que Barrowmaze (1161 pp, atlas más complejo). Marcos puede pasar el parser específico que tenga.
- Ajustar `width/height/gridSize` del JSON barrowmaze según escala real del PDF (actual 40x55 60px es aproximado).
- Calibrar `startCell` por sección a la posición exacta de la sala de inicio en cada página.
- Markers PC individuales sobre el FogMapViewer (sigue siendo prioridad 1).

**Commits finales**: cockpit `a1cc6f8` (handoff). mc-prism: el push de este commit incluye todo dungeon atlas + parser + viewer.
