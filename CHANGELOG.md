# Changelog — Cockpit Valakhan

URL en vivo: https://mc-prism.pages.dev/cockpit.html
Repo: https://github.com/marcoscabobianco-maker/cockpit-valakhan

## v5t — Fase G+H — path por día + auto-encounter (2026-04-29)
- **Path por día**: el path histórico ahora guarda `{hex, day, watchIdx}` por movimiento. SVG dibuja marcadores circulares con número de día (`d35`, `d36`...) sobre el último hex de cada día.
- **Auto-encounter al avanzar watch**: si el party está en wilderness y avanzás watch, 1d6 contra terrain. Si hay encuentro, toast pop-up con resultado + log automático.
- **Botón Auto en topbar**: toggle on/off del auto-encounter (default ON). Skip en pueblos/ciudades/brumas.
- **Full moon transition warning**: cuando un nuevo día cae en luna llena, toast dorado con efectos Ravenloft.

## v5s — Fase E — Settlement District Encounters (2026-04-29)
- **7 distritos** del settlement panel: Avenue (day/night), Slums, Market, Temple, Docks, Tavern.
- Cada distrito tiene su propia tabla (10-12 entradas) y frequency (cada 6 turnos avenue, cada 1 turno slums, etc).
- Threshold d6 propio por distrito (slums = 4+, avenue day = 6+).
- Lycanthrope full-moon detection automática.

## v5r — Fase D — Lunar phases + rumor table (2026-04-29)
- **Topbar**: ícono lunar con 8 fases (ciclo 28 días). Click → modal con efecto narrativo + mini-calendario 14 días.
- **Luna llena Ravenloft**: warnings explícitos (lycanthropes activos, undead +1 morale, Powers Check +5%, Bellaca/nahuallis +2 a Sagaz).
- **Settlement panel**: nuevo botón "📰 Tirar rumor" con 12 rumores default + 4 específicos Helix + 4 específicos Stejara. Substituye placeholders como `{hex_random_dungeon}`.

## v5q — Fase C — Notes index + Session export (2026-04-29)
- **Notes index**: lista todas las notas por hex en modo Sesión. Click en una nota → navega al hex en modo Mapa.
- **3 botones export en topbar Sesión**: 
  - Markdown sesión actual (últimos 50 eventos)
  - Markdown campaña completa (sesiones + PCs + notas + log)
  - Copy log al clipboard (para WhatsApp/Discord)
- Markdown bien formateado: header, sesiones por id, PCs con stats y conditions, notas por hex, log completo.

## v5p — Fase B — PCs panel mode (2026-04-29)
- **Nuevo modo "👥 PCs"** en topbar.
- Grid de los 11 PCs con HP/AC/level/clase/jugador.
- Click → modal detalle: HP +/-1/-5/+1/+5, level up, conditions toggleables (Fatigued/Strife/Wounded/Cursed/Charmed/Poisoned/Restrained), custom condition, Mortal Wound roll, agregar al combate.
- Botón global "+ Cargar TODOS al combate" (skip muertos/desaparecidos).
- Persistencia: `state.pc_overrides[pcId] = { hp_cur, hp_max, level, conditions[] }`.
- Auto-detección notas críticas: Silas con 2 deseos pendientes, Hector desaparecido, daños permanentes.

## v5o — Fase A — Bestiario limpio + Settlement panel (2026-04-29)
- **Bestiario limpio**: 370 monstruos con 49 OCR fixes + 54 alias marcados. Reemplaza el inline acks-data contaminado del PDF extract.
- **Settlement Panel**: panel completo de Market Class (ACKS RB Ch.8) en hex panel cuando `h.isCity`:
  - Class I-VI con población, magia max, hirelings/semana, stockpile gp.
  - Roll hirelings disponibles esta semana.
  - Mercantile Ventures: dropdown destino → 2d6 supply&demand → resultado interpretado.
- **acks_rulebook_slim.json** (~2.7 KB): subset settlements + mercantile embebido.
- marketClass V (Gosterwick) + IV (Castleton) agregados al hex map.

## v5n — Fog of war paint-with-finger (2026-04-29)
- Modo Dungeon → Barrowmaze: canvas opaco negro sobre la imagen Cía Zafiro.
- Tu dedo borra la niebla (modo Revelar) o la repinta (modo Cubrir).
- Slider pincel 10-120 px. Touch en iPad funciona (PointerEvents).
- Persiste en localStorage como dataURL del canvas.
- Player mode: solo ven la niebla, no pueden pintar.

## v5m — Limpieza de tabs duplicadas (2026-04-29)
- Removidas tabs Spells/Bestiary/MagicItems/Profs del cockpit (duplicaban el ACKS Assistant).
- Banner verde en Data apunta a `/tools/`.
- Cockpit foco: hex map, dungeon image, worldbook, sessions, combat tracker light.

## v5l — ACKS Assistant en /tools/ (2026-04-29)
- Build de `acks-assistant/dist/` (Vite/React) deployado a `https://mc-prism.pages.dev/tools/`.
- Botón "🛠 Tools ACKS" en topbar del cockpit abre en pestaña nueva.
- Spells (Fuse.js search), Bestiary, TreasureGenerator, HirelingGenerator, MortalWounds, Weather, ReactionCalc, TurnUndead, MagicItemBrowser — 18 componentes React profesionales.

## v5k — Operacional consolidación (2026-04-29)
- Combat reset borra TODOS los actores con confirmación.
- Quick rolls dmg: 1d6/1d8/1d10/1d12/2d6/2d8/2d10.
- Mortal Wound calculator (ACKS Combat IV): pregunta CON/helmet/HP status/healing → 1d20+mods → resultado completo.
- Treasure parser limpio: ya no muestra `chance %` ni JSON crudo, solo loot real.
- Spells dropdown: max-width fijo, no se corta.
- Multi-monster from encounter: parse "5 Esqueletos" o "1d6 Goblins" → N actors con HP individual rolled.
- Path con días + pace selector + roll encounter en path.
- Combat Reference buscable, full-width, 14 entradas RAW.

## v5j — Operativo (2026-04-29)
- Detail Modal universal para cards (bestiary/spells/items/treasure/NPCs/locations).
- Quitados los bloques negros sobreimpresos del dungeon image.
- GM/Player toggle global en topbar.
- Treasure type parser (mostrar gold/gems/items separado).
- Tap-mover marker C en hex map + path histórico.
- Río continuo overlay sobre hexes con terrain rio/agua/lago/cascadas.
- Botón "+ Cargar monstruo del bestiario" en Combat.
- Botón "→ Combat" en encounters.

## v5i — Marcadores interactivos sobre Cía Zafiro (2026-04-29)
- Sobre la imagen real, modo "Mover party / Marcar explorado / POI / Nota".
- Persistencia en localStorage por dungeon.
- Lista de POIs/notas con coords %.

## v5h — Mapas + Spells lazy (2026-04-29)
- Tab "📍 Mapas" en Data: 9 imágenes (Cía Zafiro, Mapa Wensley, Mapa físico Valakhan, Aurëpos, Westmerc, Adwenn ducado/ciudad, Túmulos, Barrowmaze 1.5m).
- Modal full-screen al click.
- Spells/Magic Items/Proficiencies cargados lazy via fetch (luego eliminados en v5m a favor del Assistant).

## v5f — UX modos full-screen (2026-04-29)
- Topbar con 7 botones grandes touch-friendly: Mapa / Dungeon / Combate / Encuentro / Conjuros / Data / Sesión.
- Cada modo es vista full-screen.
- iPad-first.

## v5e — Worldbook FarolClub embebido (2026-04-29)
- Tab "World" con 121 NPCs + 62 lugares + 9 facciones + 11 sesiones + 5 quests del Kanka FarolClub Aurëpos.
- Sub-tabs: NPCs / Lugares / Facciones / Sesiones / Quests con search.

## v5c-d — Multi-campaña + Tools embebidos (anterior)
- 4 campañas seedeadas (Cemanahuac, Novatos, Buenos Aires A5e, Sakkara).
- ACKS Tools embebidos antes de v5l: dice/encounter/weather/treasure/bestiary/combat.

## v5b — Engine multi-campaña (2026-04-28)
- Refactor de v5: DB en JSON externos, state en localStorage por campaña.
- Selector de campaña en header.

## v5 — Prototipo inicial (2026-04-28)
- Hex map regional (8×6) con SVG flat-top.
- Modo dungeon con room graph.
- Persistencia localStorage.
- 3 escalas anidadas concept.
