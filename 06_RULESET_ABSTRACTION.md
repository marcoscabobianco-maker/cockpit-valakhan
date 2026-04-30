# Ruleset Abstraction — A5e + ACKS + CLAN como un solo motor

> ITER 4 de iteración nocturna. 29 abril 2026.
> Diseño que permite al cockpit V5 hablar los 3 sistemas (más los que vengan) con un mismo loop, distintos parámetros.

## Insight central

Los tres sistemas hacen **la misma cosa** con distintos vocabularios y granularidades. La diferencia importante no es lo que **hacen**, sino **cuándo y con qué dado tiran**.

| Sistema | Unidad espacial | Unidad temporal | Encounter cadence |
|---|---|---|---|
| **A5e** | Region | Day | 1 por region |
| **ACKS** | Hex | Watch (3/día) | 1 por watch |
| **CLAN** | Scene | Scene | GM ad-hoc |

Si separamos **el loop** (lo común) de **los parámetros** (lo específico), el cockpit V5 corre los 3 sistemas con el mismo motor.

## Dos loops, no uno

Hay dos loops que el cockpit modela:

1. **Spatial Turn Loop** — overland / hexcrawl / wilderness.
2. **Dungeon Turn Loop** — escala local, room-to-room.

La transición entre ambos es la **migración wilderness ↔ dungeon** que pediste como "el sueño del master". Cada uno tiene sus phases, sus tiradas, su persistencia.

## El tier transversal

ACKS, A5e y CLAN tienen niveles de dificultad. Los unifico:

| Tier abstracto | A5e | ACKS rarity | CLAN category |
|---|---|---|---|
| 1 | Tier 1 | Common | Novato |
| 2 | Tier 2 | Uncommon | Veterano (low) |
| 3 | Tier 3 | Rare | Veterano (high) |
| 4 | Tier 4 | Very Rare | Maestro |

Esto es **lo más importante para multi-sistema**: una zona del mapa tiene un `tier` (1-4) y todas las tablas (encuentros, challenges, weather) se indexan por (terrain, tier). El cockpit pinta el tier del hex en la UI (borde rojo para tier 4) y el sistema activo decide cómo se traduce a sus categorías nativas.

## El modelo de archivos

```
reglas/
  turn_loop.json          ← spatial loop (hexcrawl)
  encounter_check.json    ← cuándo/cómo se tira encuentro
  weather.json            ← determinación del clima
  dungeon_turn.json       ← turn loop dentro de dungeon
  wandering_monster.json  ← encuentro aleatorio en dungeon
```

Cada JSON tiene:

```js
{
  "abstract": { /* qué hace en términos genéricos */ },
  "implementations": {
    "a5e": { /* parámetros específicos A5e */ },
    "acks": { /* parámetros específicos ACKS */ },
    "clan": { /* parámetros específicos CLAN */ }
  },
  "cockpitImplementation": {
    "v5b_current": "qué hace HOY el cockpit",
    "v5c_target": ["qué falta para soporte completo"]
  }
}
```

Esto es el **contrato del motor**: el cockpit lee `state.world.system`, busca esa clave en `implementations`, y aplica los parámetros.

## Cómo se usa desde el código

Pseudocódigo del flow (V5C):

```js
const ruleset = await fetch("./reglas/turn_loop.json").then(r => r.json());
const sys = state.world.system;  // "a5e" | "acks" | "clan"
const impl = ruleset.implementations[sys];

// Al entrar a hex:
if (sys === "a5e" && hex.regionId !== state.lastRegionId) {
  // entrada a region nueva → modal de activities
  showRegionEntryModal(hex);
} else if (sys === "acks") {
  // ACKS no tiene "region", el watch avanza con cada acción
}

// Encounter check al avanzar watch (ACKS) o entrar region (A5e):
const encCheck = await fetch("./reglas/encounter_check.json").then(r => r.json());
const encImpl = encCheck.implementations[sys];
const die = rollDie(encImpl.die);  // 1d6 ACKS, 1d20 A5e
if (passesThreshold(die, encImpl.thresholdRule, hex)) {
  const table = state.world.encounters[hex.terrain][hex.tier];
  const result = pickFromTable(table);
  logEvent(`Encounter: ${result}`);
}
```

El cockpit **no tiene reglas hardcodeadas** del sistema. Lee del JSON.

## Resumen de cada regla

### `turn_loop.json` — Spatial Turn Loop

**Phases del loop**:
1. **enter** — establecer condiciones (weather, traits, tier)
2. **activities** — PCs eligen rol/actividad
3. **encounter_check** — tirar dado, consultar tabla
4. **resolve** — combate/social/ambiental
5. **resources** — consumir Supply/raciones/luz
6. **log** — escribir al event log

**Diferencia clave**:
- A5e: 1 vez por **region** (loop largo, narrativo)
- ACKS: 1 vez por **watch** (3 por día, rítmico)
- CLAN: por **scene** (sin tempo mecánico)

### `encounter_check.json` — Encounter Check

**Proceso abstracto**:
1. Trigger (entrada o paso de tiempo)
2. Tirar dado
3. Si éxito, consultar tabla por (terrain, tier)
4. Distance + surprise + reaction
5. Resolver

**Diferencia clave**:
- A5e: 1d20 vs DC del tier (T1=12, T4=18). Pace mod ±2.
- ACKS: 1d6, threshold por civilization (4-in-6 civilized → 1-in-6 wilderness).
- CLAN: GM-adjudicated.

### `weather.json` — Weather

**Proceso abstracto**:
1. Tirar al inicio de unidad de tiempo
2. Modificar por season + climate
3. Aplicar consequences (encounter/pace/supply mod)

**Diferencia clave**:
- A5e: 1d20 contra weather table del region (Trials & Treasures).
- ACKS: 2d6 daily, modificadores Köppen + season (JJ Ch.2 Section B).
- CLAN: narrativo.

### `dungeon_turn.json` — Dungeon Turn

**Phases del loop dungeon**:
1. **action** — mover/buscar/escuchar/forzar/descansar
2. **wandering_check** — cada N turns
3. **light** — tickear antorchas/aceite
4. **rest_check** — fatigue si no descansa
5. **log**

**Diferencia clave**:
- ACKS: 10 min/turn, wandering 1d6 cada 2 turns, torch 6 turns, lantern 24 turns, rest 1/5.
- A5e: 10 min/turn, wandering GM-adjudicated, torch 60 turns, lantern 360 turns.
- CLAN: scene-based, sin formalización.

### `wandering_monster.json` — Wandering Monster

**Subset de encounter_check pero con tabla por dungeon level (no por terrain).**

- ACKS: 1d6 cada 2 turns, tabla por nivel del dungeon (1-12).
- A5e: GM elige.
- CLAN: GM elige.

## Lo que el cockpit V5b ya hace y lo que falta

### V5b (HOY)
- Spatial Turn Loop: phases enter+log parcial, encounter_check funcional con 1d6 (ACKS-default lite).
- Dungeon Turn Loop: room graph, contador de turns, wandering 1d6 cada vez que GM aprieta botón.
- Sistema activo guardado en `state.world.system`, pero el motor todavía no lee `reglas/*.json` para parametrizarse.

### V5C (próximo)
1. **Cargar `reglas/*.json` al startup** y exponerlos como `state.rulesets`.
2. **Despachar acciones por sistema activo**:
   - `advanceWatch()` solo aplica si `sys === "acks"` (A5e usa días).
   - `enterRegion()` solo aplica si `sys === "a5e"`.
   - `dungeonTurn()` aplica a todos pero con duraciones distintas.
3. **Tablas indexadas por (terrain, tier)** en cada `campaign.encounters`.
4. **Modal de region entry** para A5e (con activities picker).
5. **Resource panels distintos**: Supply para A5e, raciones individuales para ACKS, narrativo para CLAN.
6. **Auto-tick de antorchas y conjuros** en dungeon turn.

Cada bullet es 1-3 horas de impl. Total V5C ≈ 15-25 horas para soporte completo de los 3 sistemas.

## Por qué este modelo escala

Si mañana querés sumar **Mausritter** o **Cairn** o **Forbidden Lands** al cockpit, lo que hacés es:

1. Agregar `_systemConfig.system: "mausritter"` al JSON de la campaña.
2. Agregar `implementations.mausritter` a cada `reglas/*.json`.
3. (Opcional) Sumar UI específica si tiene mecánicas únicas (Mausritter usa pip-dice, Forbidden Lands usa custom dice).

El motor ya despacha por sistema. La única razón para tocar el código del cockpit es UI nueva, no reglas nuevas.

## Decisiones tomadas en esta abstracción

- ✅ **Tier 1-4 como abstracción común** (y no rarity ni categories como nombre interno).
- ✅ **Los JSONs de reglas viven afuera** del HTML, fuente de verdad editable.
- ✅ **Cada regla tiene una sección `cockpitImplementation`** que documenta lo que falta. Es self-tracking del trabajo pendiente.
- ✅ **No reinvento la rueda**: `dungeon_turn` es esencialmente lo que ACKS ya define, A5e adapta tangencialmente, CLAN ignora. La abstracción respeta la mejor implementación (ACKS) y deja que las otras hagan menos.
- ⚠️ **Dejé `clan` muy laxo** en casi todas las reglas (GM-adjudicated en lugar de mecánica formalizada). Es honesto: CLAN no formaliza estos loops mecánicamente. El cockpit en modo CLAN ofrece la herramienta opcional pero no la fuerza.
- ❓ **No abstrayé combat**. Cada sistema tiene combate muy distinto y no es el foco del cockpit hexcrawl. El cockpit invoca al combate apropiado (acks-assistant, dnd-beyond, etc.) pero no lo replica.

## Lo que Marcos debe revisar

1. **¿Tier 1-4 te sirve como common denominator?** Alternativa: lvl-of-zone (numérico) sin granularidad fija. La actual asume 4 niveles.
2. **¿La granularidad de los JSONs de reglas es correcta?** 5 archivos. Podrían ser 3 (turn_loop + encounter + dungeon) o 8 (sumar combat, social, etc.).
3. **¿Querés que cada regla tenga `cockpitImplementation`?** Útil para tracking, pero infla el JSON. Podría sacarse a un `reglas/_pending.md` separado.
4. **¿Tiene sentido el flag `clan: GM-adjudicated`?** O preferís NO incluir CLAN en estos JSONs y dejar que CLAN viva sin abstraction (porque es genuinamente narrativo).

Cualquiera de estas decisiones es revertible. La estructura es la propuesta.
