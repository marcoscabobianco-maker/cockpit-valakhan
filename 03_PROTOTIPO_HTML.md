# Prototipo HTML — Cómo probarlo

> Doble click en `prototipo_v5.html` y se abre en el browser default. Funciona offline. Persistencia local.

## Qué prueba

El prototipo es un **"hello world" arquitectónico**. Demuestra que las decisiones de `02_ARQUITECTURA_V5.md` son construibles. No es la app final.

Específicamente prueba:

1. **Tres paneles simultáneos**: DB izquierda · Mapa centro · Estado derecha. Lo que vos pediste de "qué es DB y qué es mesa" se ve a simple vista.
2. **Hex map regional con terrenos** (10 tipos, paleta mexica), 8 columnas × 6 filas, 48 hexes seedeados.
3. **Persistencia real con `localStorage`**: cualquier cosa que hagas (mover el Clan, escribir nota, tirar encounter, avanzar watch) sobrevive al refresh. Probá: hacé algo, cerrá la pestaña, reabrí el archivo. El estado vuelve.
4. **Modo Judge / Player con fog of war**:
   - Judge ve todo el mapa con info GM.
   - Player ve solo hexes "explored" + "discovered" (vecinos de explored). Los "hidden" aparecen como bloques negros.
5. **Calendario diegético**: año Ce-Ácatl, día N, watch (Mañana/Tarde/Noche). Avanza con un botón. Loggea cada avance.
6. **Encounter check** integrado: tabla de encuentros por terreno, tirada visible, resultado al log.
7. **Migración wilderness → dungeon** (LO IMPORTANTE):
   - Hex Coatépec (col 5, row 3) tiene marcador 🜍.
   - Click en él, después click en "🜍 Bajar a escala local".
   - Se abre modal con un room graph (7 salas), conexiones, fog of war independiente, contador de turnos (10 min cada uno).
   - Movés entre salas con click. Cada movimiento +1 turno.
   - Wandering monster check con dado real.
   - "Volver al hex" cierra el dungeon manteniendo el estado dungeon (si volvés a entrar, está como lo dejaste).
8. **Log de eventos persistente**: todo lo que pasa queda con timestamp diegético.
9. **Notas vivas por hex**: campo de texto que persiste por hex.
10. **Reset campaña**: borra `localStorage` y vuelve a estado inicial.

## Cómo ejercitarlo (camino guiado)

1. **Abrí el archivo**. Vas a ver el Clan en Tlatelolco (D3, marcador "C" naranja).
2. **Click en C4 (Tenochtitlan)**: panel derecho muestra info pública + GM-only. Notá la barra roja "GM ONLY" y la verde "VISIBLE".
3. **Botón "→ Mover Clan acá"**: el Clan se mueve, se revelan vecinos.
4. **Click en F4 (Camino a Coatépec)**, "Mover", luego en F4 dale "Encounter check". Mirá el log abajo.
5. **Botón "▶ Avanzar watch"** en el header. Calendario salta. Ahora estás en Tarde.
6. **Click en F4 (Cerro de Coatépec)**, después "🜍 Bajar a escala local". Modal del dungeon.
7. **Click en sala 2 ("Boca de la cueva")**. Entrás. +1 turno (10 min).
8. **Click en sala 3 ("Recinto del ritual")**, sala 5, sala 7. Vas explorando.
9. **🎲 Wandering monster**: tirá unas veces.
10. **"⤴ Volver al hex"**: cierra el dungeon. Mirá en el panel derecho "Posición del Clan": ahora dice escala regional otra vez, pero el dungeon retiene el estado.
11. **Cambiá a modo Player** (botón en header). El mapa se llena de fog. Solo ves lo descubierto.
12. **Refresh el browser**. Todo sigue ahí.
13. **Reset campaña** si querés volver al estado inicial.

## Lo que NO está (sabido, deliberado)

- Escala 1 (imperial). El prototipo solo tiene escala regional + dungeon.
- Bestiario completo CLAN (solo 6 placeholders).
- Tiradas de combate / iniciativa / saving throws (eso vive en `acks-assistant`, lo integraríamos en V5 productiva).
- Sync entre dispositivos (es solo `localStorage`).
- Reglas de weather, foraging, navigation throw (placeholders).
- Personajes (PCs como entidades con ficha — solo hay un marcador "Clan").
- Mover entre escala 1 e escala 2 (no hay escala 1).
- Edición del mundo desde la UI (los hexes están hardcodeados; en V5 productiva habría editor).

## Lo que PUEDE estar para iterar V5A → V5B → V5C

| Iteración | Qué agrega |
|---|---|
| **V5A (este prototipo)** | Tres escalas conceptuales con escala 2 + 3 funcionales, persistencia local, fog of war. |
| **V5B** | Escala 1 imperial. Edición del mundo desde la UI (agregar hex, mover NPC, definir POI). PCs como entidades. Sync a Drive. |
| **V5C** | Integración con `acks-assistant`: bestiario completo, tablas de combate, character sheets. Multi-campaña (CLAN, ACKS coexisten). |
| **V5D** | Vista de jugador compartida (Cloudflare Pages) con auth simple, los players ven su fog, pueden comentar hexes. Como Session Editor pero para mapas. |

## Bugs/limitaciones conocidas del prototipo

- **CSS variables en SVG `fill`**: usa `getComputedStyle` para resolver vars. Funciona pero podría parpadear en primer render con tema custom.
- **Hex offset coordinates**: usé flat-top con vecinos por paridad de columna. Las fórmulas están en `neighborsOf()`. Si una columna par debe shiftear distinto en tu convención, ajustar.
- **Render performance**: con 48 hexes está fluido. Para 500+ hex (escala 1) habrá que pasar a Canvas o virtualizar SVG.
- **Modo Player no esconde el panel DB**: el bestiario sigue visible en player mode. En V5 productiva, panel DB tendría un toggle por sección.
- **Una sola campaña en `localStorage`**: el storage key es fijo. En V5 productiva, multi-campaña con dropdown.

## Por qué este prototipo importa

Porque demuestra (en 800 líneas de un solo archivo, sin build, sin server) que:

- **Persistencia + tablas + DB-vs-mesa** son construibles AHORA, sin nada exótico.
- **Wilderness ↔ dungeon con persistencia bidireccional** funciona con `localStorage` + un modal.
- **El stack es el mismo que ATEM**: HTML autocontenido, datos embebidos como JSON, deploy a Cloudflare Pages igual que `mc-prism`.
- La V5 no es un mapa, **es el cockpit del Judge**. Y el cockpit cabe en un solo HTML cuando arranca.

Si esto te convence, la V5 productiva es ampliación, no rediseño.
