# Formatos paralelos — Wilderness + Dungeon + Persistencia

> 12 sistemas que resuelven (parcialmente) el problema "West Marches con migración de escala". Lo que tomamos de cada uno.

## Eje 1: VTTs (Virtual Tabletop) — el modelo de "scenes anidadas"

### 1. Foundry VTT
- Modelo de **Scenes**: cada lugar es una escena con su grilla, fog of war, tokens, walls.
- Las escenas tienen **journal entries** lincados (texto persistente).
- "Scene transitions" via macros: hex en world map → click → carga la escena del dungeon.
- **Lo que tomamos**: la idea de que cada nivel es una scene autónoma con su estado, y que el world map es UNA scene más con links a las otras.
- **Lo que NO**: requiere licencia, server, y es C++/JS pesado. Para una mesa chica, overkill.

### 2. Owlbear Rodeo (v2)
- Webapp pura, simple, fog of war, dice integrados, persistencia por room URL.
- No tiene migración entre mapas (cada mapa es independiente).
- **Lo que tomamos**: la simplicidad del UX touch-first, el patrón "comparto un link y todos ven".
- **Lo que NO**: una mesa = un mapa (no hay nesting).

### 3. Roll20
- Pages = scenes, ya viejito pero el patrón es el mismo.
- **Lo que tomamos**: nada nuevo más allá de Foundry.

## Eje 2: Hex map editors — el modelo wilderness

### 4. Hex Kit (Cone of Negative Energy)
- Editor de hexmap con tiles. Estático, no persistencia online.
- **Lo que tomamos**: el lenguaje visual del tile (cada hex es un tile pintado, no SVG procedural).

### 5. Worldographer (sucesor de Hexographer)
- Hex maps con **datos por hex**: terreno, settlement, ruta, GM notes.
- Exporta a JSON.
- **Lo que tomamos**: el modelo de datos: `hex { coord, terrain, label, gm_notes, encounters[] }`. Esto va directo a la DB.

### 6. Watabou's Procgen (Mythic Gazetteer)
- Generadores procedurales (cities, dungeons, hex worlds) con **URL como estado**.
- Persistencia = la URL contiene el seed. No editable.
- **Lo que tomamos**: el truco de seed en URL para compartir un world inmutable. Para West Marches, el world arranca como un seed y los jugadores lo van anotando encima.

## Eje 3: Dungeon mappers

### 7. Dungeon Scrawl (Probable Train)
- Editor de dungeons rápido, exporta SVG/PNG.
- **Lo que tomamos**: nada estructural, pero el grid 5'/cell es estándar y queremos respetarlo.

### 8. Dungeondraft + Dungeon Alchemist
- Mapas bonitos, no interactivos.
- **Lo que tomamos**: nada (estamos en otro plano).

## Eje 4: TTRPG digitales con persistencia explícita

### 9. The Alexandrian's Hexcrawl Procedure (paper)
- No es software, es una **especificación** de cómo correr un hexcrawl con persistencia diegética: cada hex tiene "keyed locations" + "encounter table" + "weather" + "navigation throw".
- **Lo que tomamos**: **el procedimiento mismo es la app**. Si modelamos el turn loop (1 watch = N checks: navigation, encounter, weather, foraging, rest), la app se vuelve un wizard de turno.

### 10. Mausritter / Cairn / Knave hex crawls
- Guías de West Marches modernas con plantillas hexkey: una página = un hex, una tabla de encuentros, un dungeon pequeño embebido.
- **Lo que tomamos**: el principio "**cada hex es una página de notas**". El mapa es solo el índice. La data vive en las páginas.

### 11. The Quill VTT / Quest Portal
- Webs nuevas que mezclan hexcrawl + character sheets + persistence.
- **Lo que tomamos**: ratifican la dirección — esto es lo que el espacio quiere y todavía no hay un winner claro.

## Eje 5: Lo que ya hicimos nosotros (los visores ATEM)

### 12. Visor de Cuadernos ATEM + Buscador ATEM + Session Editor
- HTML autocontenido, datos embebidos, anotaciones lincadas, búsqueda full-text, deploy a Cloudflare Pages.
- **Persistencia**: por ahora estática (datos en JSON al build), pero ya hay precedente de Cloudflare Worker proxying audio (Session Editor).
- **Lo que tomamos**: **TODO**. La V5 es un visor más en la familia ATEM. Misma estética (hard rule "el cuaderno manda" = "la mesa manda"), mismo deploy pipeline, misma cultura "doble click y funciona".

## Síntesis: lo que adoptamos para V5

| De | Concepto |
|---|---|
| Foundry | **Scene nesting** (world hex → location → dungeon) con transition explícita |
| Owlbear | **UX simple, touch-first**, una pantalla = una vista |
| Worldographer | **Modelo de datos por hex** con campos GM-only y player-visible |
| Watabou | **Seed inicial inmutable** + capa de anotaciones encima |
| Alexandrian | **Turn loop como wizard** (watch → checks en orden) |
| Mausritter | **Cada hex es una página**, el mapa es el índice |
| Visores ATEM | **Stack** (HTML + JSON + Cloudflare), **estética**, **deploy** |

## Patrones que NO copiamos (deliberadamente)

- **Real-time multi-user** (Foundry, Owlbear): para West Marches asincrónico, NO necesitamos Yjs/CRDT. Una sola persona escribe a la vez (el Judge en sesión, los players entre sesiones).
- **Combate en grid táctico** (Foundry, Roll20): ACKS y CLAN se llevan bien con teatro de la mente. Si necesitamos grid puntual, lo hacemos en una pantalla aparte (combat tracker que ya existe en `acks-assistant`).
- **Generación procedural infinita** (Watabou): el world está pre-keyed por el Judge. No queremos sorpresas no-curadas.
