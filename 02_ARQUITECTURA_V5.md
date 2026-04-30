# Arquitectura V5 — El cockpit del Judge

> Propuesta concreta. Tres escalas anidadas, modelo de persistencia, separación clara entre "lo que vive en la mesa" y "lo que vive en la base de datos".

## Principio rector

> **El mapa no es la app. El mapa es la entrada al estado.**

La V5 no es un visualizador con extras. Es un **cockpit** donde el Judge:
1. Sabe en qué momento del calendario está la campaña.
2. Ve el mundo a la escala que le interesa AHORA.
3. Tira las tablas que aplican a esa escala sin cambiar de pantalla.
4. Anota lo que pasó. La anotación queda persistida y aparece cuando vuelva.

Lo que un jugador ve es un subset del cockpit (fog of war + sus notas).

## Las tres escalas

```
┌─────────────────────────────────────────────────┐
│  ESCALA 1 — IMPERIAL  (1 hex = 24 millas)        │
│  El mapa-mundi de Cemanahuac                     │
│  Tenochtitlan · Tlaxcala · Aztlán · Coatépec     │
│  Unidad de tiempo: SEMANA / MES                  │
│  Uso: travel inter-regional, política, calendario│
└────────────────────┬────────────────────────────┘
                     │ click en hex con marcador
                     ▼
┌─────────────────────────────────────────────────┐
│  ESCALA 2 — REGIONAL  (1 hex = 6 millas)         │
│  El West Marches propiamente dicho               │
│  Hexcrawl, encuentros por terreno, weather       │
│  Unidad de tiempo: WATCH (4-8h) / DÍA            │
│  Uso: exploración del wilderness                 │
└────────────────────┬────────────────────────────┘
                     │ click en POI / cueva / ruina
                     ▼
┌─────────────────────────────────────────────────┐
│  ESCALA 3 — LOCAL  (room graph + grid 5')        │
│  Dungeon, edificio, cerro ritual                 │
│  Fog of war room-to-room                         │
│  Unidad de tiempo: TURN (10 min) / ROUND (10 s)  │
│  Uso: dungeon delve, asalto a edificio, ritual   │
└─────────────────────────────────────────────────┘
```

**Reglas de transición:**
- Cada nivel tiene un calendario propio que **suma al global**. Entrar a un dungeon no detiene el reloj imperial — solo cambia el "zoom" del tracker activo.
- Salir de un dungeon vuelve al hex de origen, con el delta de tiempo aplicado (X turnos = Y horas = N watches consumidos).
- Persistencia explícita en cada borde: al salir, el estado del nivel inferior queda guardado.

## Qué es DB y qué es vista de mesa

Esta es la pregunta clave que vos planteaste. Mi propuesta:

### Base de datos (no se toca en sesión, se prepara antes)

| Cosa | Por qué es DB |
|---|---|
| Mapa de los hex (terreno, coords) | El mundo está pre-keyed |
| Tabla de encuentros por terreno | Es la regla del libro |
| Bestiario CLAN (Nahualli Coyotl, Tlacatecolotl, etc.) | Es contenido fijo |
| Tablas de weather, foraging, navigation throws | Reglas |
| Hex keys: qué hay realmente en cada hex (POIs, monstruos guardados) | Preparación del Judge |
| Dungeons pre-mapeados (Coatépec, Aztlán) | Preparación |
| Glosario de NPCs estables (Xiuhpetlatl, Mazatl Ohtli) | Preparación |
| Calendario diegético "esqueleto" (festividades mexica) | Preparación |

### Vista de mesa (se modifica DURANTE la sesión)

| Cosa | Por qué es vista |
|---|---|
| Posición actual de los PCs (en qué hex / en qué room) | Cambia a cada turno |
| Fog of war (qué descubrieron) | Estado revelado |
| Calendario actual (día Ce-Ácatl + watches consumidos) | Avanza |
| HP / PV / PC actuales de cada PC | Cambia constante |
| Recursos consumidos (antorchas, raciones, agua) | Cambia |
| Encuentros que ya ocurrieron (no se vuelve a tirar) | Log |
| NPCs alterados (muertos, aliados, sospechosos) | Estado |
| Loot recogido | Estado |
| Sospechas/notas del Clan sobre el infiltrado | Anotaciones |

**Regla técnica derivada**: la DB es **read-only durante la sesión**. La vista de mesa es **write-heavy durante la sesión** y se persiste a `localStorage` (luego sync a Cloudflare KV o Drive).

Esta separación es lo que vos llamaste "identificar qué cosas son las que se utilizan en la mesa y qué cosas sirven como base de datos". La V5 hace explícita esa separación en la UI: panel izquierdo es DB, panel derecho es estado vivo.

## Modelo de datos (resumen)

```
World {
  id, name ("Cemanahuac"),
  scales: {
    imperial: { hexSize: 24mi, hexes: [...] },
    regional: { hexSize: 6mi, hexes: [...] },  // por región imperial
  },
  locations: [Location],     // POIs lincados a hexes
  npcs: [NPC],
  bestiary: [Monster],       // CLAN
  tables: { encounters, weather, foraging, ... }
}

Location {
  id, parentHex, name,
  type: "settlement" | "dungeon" | "ritual_site" | "wilderness_lair",
  rooms: [Room]?,            // si es dungeon
  npcs: [npcId]?,
  description, gm_notes
}

Room {
  id, name, x, y, w, h,
  connections: [roomId],
  contents: { monsters, traps, treasure, features },
  light: "dark" | "torchlit" | "natural" | ...
}

Campaign {
  id, name ("Cemanahuac S1"), worldId,
  calendar: { year, month, day, watch },
  pcs: [PC],
  state: {
    fogOfWar: { hexId|roomId: "hidden"|"discovered"|"explored" },
    pcPositions: { pcId: { scale, ref } },
    eventLog: [Event],       // todo lo que pasó
    consumables: { pcId: { torches, rations, ... } },
    relationships: { npcId: { suspected, ally, hostile, ... } },
    loot: [Item]
  }
}

Event {
  timestamp (in-game), realDate, scale, hexOrRoomId,
  type: "encounter" | "weather" | "discovery" | "combat" | "ruling",
  description, rolls: [Roll]?
}
```

Esto es lo mínimo. Cada tabla puede crecer.

## Stack tecnológico recomendado

**Para el prototipo (lo que dejé):**
- HTML autocontenido + vanilla JS + `localStorage`
- Datos seedeados inline
- Funciona offline, doble click

**Para la V5 productiva (cuando quieras escalar):**
- React + TypeScript (igual que `acks-assistant`)
- Datos en JSON estático (DB) + `localStorage` (estado vivo)
- Sync opcional a **Cloudflare Workers + KV** (siguiendo el patrón de `mc-prism-deploy` para Session Editor)
- Deploy a `mc-prism.com/cemanahuac` o subdomain
- iPad-first (lo que ya planeaste en `PLAN_ASISTENTE_IPAD.md`)

## Qué construir primero (orden propuesto)

1. **Escala 2 (regional, hex)** con un solo hex anotado y el modal de "este hex contiene…". Es el corazón del West Marches.
2. **Calendario diegético** persistente. Avanza watch por watch. Loggea eventos.
3. **Tabla de encuentros por terreno** integrada (click derecho hex → tirar encounter).
4. **Una location de prueba** (Coatépec) con su room graph reusando el modelo de `sakkara-map.jsx`.
5. **Transición hex→location** con persistencia bidireccional.
6. **Escala 1 (imperial)** después, cuando el corazón funcione.
7. **Sync a Cloudflare KV** cuando quieras compartir entre dispositivos.

Esa secuencia respeta tu pedido: empezamos por **persistencia + tablas + diferenciación DB/vista**, y la migración wilderness↔dungeon aparece en el paso 5 sobre cimientos sólidos.

## Lo que el prototipo HTML ya muestra

- Render de un hex map regional pequeño (10×8 hexes) con terrenos.
- Click en hex → panel lateral con info DB + área de notas vivas.
- Tirar encounter desde el panel (rolls reales con resultado loggeado).
- Avanzar watch (calendario diegético).
- **Persistencia en `localStorage`**: refrescá el browser, el estado vuelve.
- Modo "Judge view" vs "Player view" (fog of war).
- Botón "Bajar a escala local" (placeholder por ahora — la idea es que abra el dungeon graph).
- Reset de campaña (borra `localStorage` para empezar de cero).

No es la V5 final. Es el "hello world" de la arquitectura propuesta. Si te convence el approach, lo escalamos en pasos chicos.
