# Changelog — Cockpit Valakhan

URL en vivo: https://mc-prism.pages.dev/cockpit
Repo: https://github.com/marcoscabobianco-maker/cockpit-valakhan

## v6f — Arden Vul multi-level viewer (27 levels, 1293 rooms OCR) (2026-04-30)
- **Soporte multi-level**: detecta `dungeon.type === 'multi-level'` (Ardis Vala / Arden Vul) y dispatchea a viewer dedicado.
- **27 levels** (10 main + 17 sublevels) con bg.webp 1600 wide + coords OCR.
- **Selector de level** dropdown con los 27 levels + barra de navegación rápida (botones por ID).
- **Canvas-based viewer simple**: bg image + markers dorados sobre rooms detectadas (1293 total, ~80% coverage OCR).
- Click marker → alert con room ID + level name (info detallada `rooms_full` pendiente de extraer).
- **Barrowmaze (single-level) intacto** con grid táctico real V6e — comportamiento dispatch by `dgData.type`.
- Limitaciones: sin walls vectorizadas / LoS / fog of war / party rect / tracker para Arden Vul (pendiente: replicar pipeline sample-based por level).
- Helpers: `dgArdenLoadLevel`, `dgArdenSwitchLevel`, `renderArdenVulViewer`.
- Assets: `maps/arden_vul/` (4.7 MB, 27 bg + 27 coords + manifest, sin `_full.webp`).

## v6e — Wildcard polish · Quick refs ACKS + ACKS Assistant link + atajos (2026-04-30)
- **Quick refs ACKS card** en panel derecho: movement, light, search, listen, wandering, surprise, reaction, saves L1, distance.
- **Botón "🛠 Abrir ACKS Assistant"** que lanza `/tools/` en nueva pestaña.
- Atajos visibles: `WASD`/flechas mover, `G` toggle DM, `T` +1 turno, `shift+click` colocar trampa.

## v6d — Trampas place + detect + trigger (2026-04-30)
- `state.dungeon.grid.traps[]` activo (groundwork v5w). Cada trap: `{x, y, desc, saveType, detected, triggered}`.
- DM mode + **shift+click** sobre cell → prompt para colocar trampa con descripción y save type.
- Render canvas: trap detected = amarillo, triggered = rojo intenso, oculta = solo DM ve (rojo tenue).
- Auto-check al entrar cell con trap: 1d6, 1 = detect (1-2 si vanguardia es Thief/Assassin/Explorer/Ranger), si falla → triggered.
- Banner alertas con trampa disparada + botón "Resolver".
- Card "Posición real" con contador y modal para listar/borrar trampas.
- Helpers: `dgPlaceTrap`, `dgRemoveTrap`, `dgClearAllTraps`, `dgCheckTrapAtCell`, `dgResolveTrap`, `dgListTrapsModal`.

## v6c — Click rooms keyed (244 rooms con desc/treasure) (2026-04-30)
- Carga async de `maps/barrowmaze_room_coords.json` (375 rooms) + `maps/barrowmaze_rooms_full.json` (244 rooms con desc/treasure/HD).
- Markers dorados (5px radius) sobre el canvas en cada posición de sala.
- Visibilidad: en DM modo todos visibles; en player solo si la cell está en `seenSet`.
- Click en marker (radio 22 px) → modal con room name, área, chunk, descripción narrativa, treasure_coins.
- Helpers: `dgLoadRoomsData`, `dgShowRoomInfo`, `dgHandleMapClick`.

## v6b — PC roster (11 novatos) + formación + lightBearer (2026-04-30)
- Carga PCs desde `CAMPAIGNS.pcs` (novatos_ravenloft.json: 11 PCs alive).
- Card "👥 Party (N)" en panel derecho del modo real, agrupada por posición (Vanguardia / Medio / Retaguardia).
- Cada PC: nombre, clase/level, HP bar coloreada (verde >60%, amarillo >30%, rojo <30%), AC.
- Botones rápidos: −1 HP, +1 HP, −1d6 HP, select posición, toggle 🔥 portador de luz.
- Helpers: `dgInitParty`, `dgPCHpDelta`, `dgPCDamage`, `dgSetPCPosition`, `dgSetLightBearer`.
- Mortal Wound trigger automático cuando HP llega a 0 (log avisando consultar /tools/ ACKS Assistant).

## v6a — Encuentro pipeline + tabla Barrowmaze + banner combate (2026-04-30)
- `BARROWMAZE_WANDERING` table 1d20 con 8 entries: skeletons, zombies, giant rats, gnolls, ghouls, giant spider, wights, wraith. Stats ACKS-compatible (HD/AC/DMG/notes).
- `dgWanderingCheck` ramificado: si dungeon='barrowmaze', usa tabla específica + crea `state.dungeon.activeEncounter` con surprise + distance rolls.
- Banner sticky **🜍 ENCUENTRO** con info estructurada (count × name, HD/AC/DMG, distance, surprise hints).
- Botón **→ Combate** precarga `combatAddFoe` con N copias del monster + switch a modo combat.
- Botón **Dismiss** para resolución narrativa (parlar/huir/esquivar).
- Helpers: `dgRollBarrowmazeEncounter`, `dgEncounterToCombat`, `dgDismissEncounter`, `rollDie`, `rollDiceExpr`.

## v5z — Hora del día + raciones + descanso nocturno + progress bars (2026-04-30)
- **Time-of-day display**: hora actual `HH:MM` desde `dgGetTimeInfo()` (cada turn = 10 min). Default 09:00 AM, día 1.
- Períodos coloridos: ☀ mañana / 🌤 tarde / 🌅 atardecer / 🌙 noche.
- **Long rest** (descanso nocturno ACKS): `dgLongRest()` avanza 48 turnos in-game (8h), incrementa día, consume 1 ración por PC, recupera 1d3 HP por PC, resetea torch/wandering/rest counters.
- Progress bars visuales (helper `dgProgressBar`) para: 🔥 antorcha, 👹 wandering, 😴 descanso, 🍞 raciones.
- Inventario raciones: `state.dungeon.rationsTotal` (default 11×7=77), `partySize` (default 11), `startHour` (default 9). Inputs configurables.
- Banner alertas: 🌅 atardecer (17-20h) y 🌙 noche (20-5h) — warning sobre Forbidden Marsh peligroso al volver a Helix.
- Banner alertas: 🍞 sin raciones suficientes para 1 día más.

## v5y — Drop Room Graph + Cía Zafiro JPEG, DM prominent, perf (2026-04-30)
- Eliminada barra `[Room graph] [Cía Zafiro] [Grid táctico]`. Solo grid view.
- Quitado SVG `dgmap` (rooms+conexiones) y div `dg-image-view` (fog paint + imgmap).
- Quitado background JPEG Cía Zafiro detrás del dungeon view.
- **Vista DM prominente**: botón grande arriba del canvas, atajo `G`. Atajo `T` = +1 turno.
- **Perf fix**: `gridMoveReal()` ahora detecta turn boundary; si NO hay turno nuevo, solo `redrawGridRealCanvas()` + `updateRealQuickStats()` (no full HTML rebuild). Movimiento snappy en iPad.
- IDs en stats inline: `grid-real-pos`, `grid-real-seen`, `grid-real-steps`, `grid-real-turns`, `grid-real-mins`, `grid-real-dm-label`.

## v5x — Barrowmaze real (walls vectorizadas + LoS) (2026-04-30)
- **Vectorización automática de walls** vía sample-based del PNG renderizado del PDF (PyMuPDF + Pillow).
- Pipeline: render 6 páginas PDF a 250 DPI → stitch 3×2 (5256×4888 px) → samplear cada cell de 24px → wallmap matrix 203×219 = 44,457 cells (41% walkable).
- Output: `maps/wallmap_barrowmaze.json` (87 KB) + `maps/barrowmaze_real.webp` (557 KB).
- Sala 74A localizada vía text-layer search del PDF en cell (32, 84).
- **Toggle ASCII / Real mode**: dos posiciones independientes (`g.realPlayer`, `g.realTail`, `g.realSeen` separados).
- **Canvas-based renderer** (`renderGridReal`): bg image + fog overlay + party rect 1×2 + LoS Bresenham con walls reales del módulo.
- Auto-center scroll on player en cada movimiento.

## v5w — Tracker dungeon + party rect + alertas (2026-04-30)
- **gridMove** auto-dispara `dgAdvance()` al cruzar turn boundary (cada `cellFt/partyFtPerTurn` pasos).
- Rest timer ACKS RAW (5 turnos actividad → 1 rest forzado, -1/-1 si no descansan). Reset en `dgRest()`.
- Wandering noise modifier: `🔊 Ruido +1` aumenta umbral del próximo wandering check (1d6 ≤ 1+noise).
- Tracking inventario antorchas (`torchesInPack`) — `gridLightTorch()` consume de mochila.
- Banner alertas sticky: 😴 rest DUE / 👹 wandering DUE / 🌑 antorcha agotada / 🔥 antorcha últimos turnos.
- Party como rectángulo 1×2 cells (10×20 ft): head celeste #5dade2 + tail #2980b9 75% opacity.
- Groundwork: `formation`, `lightBearer`, `traps[]` (UI agregada en v6b/v6d).

## v5v — LoS Bresenham + tiempo + DM toggle (2026-04-30)
- `gridRevealFrom` ahora usa **raycast Bresenham con bloqueo por wall** (no Manhattan distance pura). Las paredes cortan la visión, las puertas no.
- Marker celeste cuadrado `#5dade2` (antes verde-azulado).
- Contador de tiempo: pasos / turnos (10 min) / minutos acumulados. Configurable `partyFtPerTurn` y `cellFt`.
- Toggle Vista DM (👁) / Vista jugadores (👤): DM bypass fog. Default jugadores.
- Helpers: `gridLineOfSight`, `gridSetSpeed`, `gridResetTime`, `gridToggleDM`.

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
