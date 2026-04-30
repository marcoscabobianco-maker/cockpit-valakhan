# Level Up A5e — Mapping del Exploration System al Cockpit

> ITER 3 de iteración nocturna. 29 abril 2026.
> Pregunta: ¿cómo mapeo Trials & Treasures (A5e) al cockpit V5b? Respuesta abajo, concepto por concepto.

## El sistema A5e en 30 segundos

A5e (Advanced 5th Edition) reemplazó el viaje genérico de 5e DMG ("¿cuántas millas hacés por día?") con un **journey loop estructurado** que mete a la mesa en lo que ACKS y CLAN ya hacían: **el viaje es contenido, no transición**.

Diferencias claves vs ACKS:
- **Unidad espacial = Region**, no hex. Una region puede ser ≥1 hex (24mi/hex normal pace = 1 día = 1 region "default size").
- **Activities por region**, no por watch. Cada PC elige UNA activity de un menu fijo y rola al final de la region.
- **Supply = "journey HP" del party**. Mecánica abstracta de food+water+morale logística. Cuando llega a 0, fatiga.
- **Fatigue + Strife** reemplazan Exhaustion 5e. Físico vs psicológico. Recuperan en **haven** (lugar seguro).
- **Tier** de region = dificultad de challenges/encounters (no nivel de PCs).
- Tablas: encounter tables + exploration challenge tables, ambas categorizadas por **tier**.

## El Journey Checklist (lo importante)

```
1. Identificar Regions de la ruta (mapa)
2. Por cada Region:
   a. Establecer condiciones (traits, weather, task DC base)
   b. Adventurers eligen 1 journey activity c/u → rolls
   c. Narrator tira encounters/challenges de la tabla del tier
   d. Resolver Supply, fatigue, strife
3. Llegar a destino
```

Esto es **EXACTAMENTE** lo que el cockpit V5b hace al moverse hex a hex, solo que A5e lo formaliza más y agrupa por region.

## Las 14 Journey Activities (data canónica)

Cada PC elige **una** por region traversada.

| Activity | Skill | Éxito | Fallo |
|---|---|---|---|
| Befriend Animal | Animal Handling | 1 animal sigue al party hasta peligro | Nada |
| Busk | Acrobatics/Athletics/Performance | 1 gp/día + bonus por DC | Nada |
| Chronicle | History | Expertise die a History/Survival en region | No nota nada |
| Cook | Cook's utensils/Survival | -25% Supply consumo | Nada |
| Cover Tracks | Survival | +1 día separación de perseguidores | Perseguidores cerca |
| Entertain | Performance | Bonus contra Strife | Nada |
| Gather Components | Arcana/Nature | 1d4 gp componentes/día + bonus | Nada |
| Gossip | Investigation/Persuasion | Rumores | Nada |
| Harvest | Medicine/Nature (kit) | +1 use healer's satchel/día | Nada |
| Hunt and Gather | Survival | +1 Supply/día | Nada |
| Pray | Religion | Advantage 1 check + boon | Dioses no escuchan |
| Rob | Intimidation/Sleight of Hand | 1d8 gp/semana | Nada |
| Scout | Perception | Revela regions adyacentes | No info |
| Track | Survival (opposed) | Sigue presa | -1 día de presa |

**Estructuralmente** = una tabla dispatch: `(activity, skill, dc, successRoll, failureEffect)`. Va al `_systemConfig.journeyActivities` del JSON.

## Tier (la pieza más importante para multi-sistema)

**Tier en A5e** (1-4) = nivel de la *zona*, no de los PCs. Una región tier 3 tiene encounters tier 3 y challenges tier 3 sin importar si el party es nivel 1 o 10. Sirve para sandbox / West Marches puro: las zonas son lo que son, los PCs eligen riesgo.

**Mapeo al hex map**:
- Cada hex tiene un campo `tier: 1|2|3|4`.
- El cockpit pinta hexes de tier alto con un borde rojo (señal "no entren novatos").
- Encounter tables del JSON están indexadas por terreno + tier.

Esta noción ya existe en CLAN (Novato/Veterano/Maestro) y en ACKS implícitamente (encounter rarity Common→Very Rare). **Tier es el común denominador para el ruleset abstraction de ITER 4**.

## Mapping completo concepto → cockpit

| A5e concept | DB / Estado vivo | Cómo se modela en V5b |
|---|---|---|
| **Region** | DB | Hex con campo `regionId`. O cluster de hexes con mismo terrain compartiendo region. |
| **Region tier** | DB | `hex.tier: 1-4` |
| **Region traits** | DB | `hex.traits: ["arid","fey","cursed"]` |
| **Journey** | Estado vivo | `state.journey = { regions: [...], currentRegion, day }` |
| **Supply** | Estado vivo | `state.party.supply: 12` (counter) |
| **Hunt and Gather +1 Supply** | Tirada → estado | Acción del cockpit, modifica supply |
| **Cook -25%** | Modificador | `state.party.flags.cookActive = true` |
| **Forced march** | Tirada | Botón "fast pace" → save → fatigue |
| **Travel pace** | Estado vivo | `state.party.pace: "slow"|"normal"|"fast"` |
| **Watch / day cycle** | Estado vivo | Cockpit usa **3 watches** (Mañana/Tarde/Noche). A5e no formaliza watches igual, pero los soporta. |
| **Exploration challenge** | DB → log | Tabla por tier × terrain. Roll → log evento. |
| **Encounter** | DB → log | Idem encounter check del cockpit actual. |
| **Discovery** | DB pre-keyed | `hex.discoveries: [...]` revelados al pasar. Lista que se va vaciando. |
| **Boon** | DB → estado | Tabla de boons random por tier. Asignado al party. |
| **Fatigue** | Estado vivo per PC | `pc.fatigue: 0-6` |
| **Strife** | Estado vivo per PC | `pc.strife: 0-6` |
| **Haven** | DB | `hex.haven: true|false`. Solo en haven se recupera fatigue/strife ≥2. |
| **Activity por region** | UI | Modal "elegí tu activity para esta region" cuando el party entra. |
| **Tier 1 vs 4 encounter table** | DB | `encounters[terrain][tier] = [...]` |

## Diferencias estructurales con ACKS y CLAN

| Eje | A5e | ACKS | CLAN |
|---|---|---|---|
| Unidad espacial | Region (≥1 hex) | Hex (1 sí o sí) | Hex (CLAN no lo formaliza tanto) |
| Encounter cadence | 1 por region | 1 por watch (3/día) | 1 por escena |
| Activity cadence | 1 por region por PC | rol implícito (Navigator + Scout + ...) en watches | libre |
| Supply | counter explícito (party HP) | tracking item por item (raciones, agua) | implícito |
| Exhaustion | Fatigue + Strife (separadas) | Exhaustion 5e simple | Reservas (PV/PC) |
| Tier | 1-4 explícito | rarity Common → Very Rare | Novato → Maestro |
| Haven | concepto formal | civilizado vs wilderness vs outlands | concepto narrativo |

**Implicación para el cockpit**: hay un loop común (entrar a region → activities → encounter → supply → log) y una **abstracción de "tier"** transversal. ITER 4 lo formaliza.

## Qué es DB / qué es vista de mesa (para A5e específicamente)

### DB (preparada antes, no se toca en sesión)

- Region definitions (id, name, tier, terrain, traits, default_dc, weather_table)
- Encounter tables por (terrain, tier)
- Exploration challenge tables por (terrain, tier)
- Discovery list por region (pre-keyed)
- Boon table por tier
- Journey activities catalog
- Haven locations (hex con `haven: true`)
- NPC list

### Estado vivo (cambia durante journey)

- `state.journey.currentRegionId`
- `state.journey.day` (entered region)
- `state.party.supply: number`
- `state.party.pace: "slow"|"normal"|"fast"`
- `state.party.flags: {cookActive, coverTracksActive, ...}`
- `state.pcs[id].fatigue: 0-6`
- `state.pcs[id].strife: 0-6`
- `state.pcs[id].activeActivity: string` (la elegida en region actual)
- `state.discoveries[hexId]: ["found_a", "found_b", ...]` (consumidas)
- `state.boons[]: ["boon_id_a"]` (acumuladas)
- `state.events[]: log`

## El UX que sigue del mapping

### Entrada a region nueva (UI sugerida)

Cuando movés el party a un hex y el `regionId` cambia (o hay flag "first time"):

1. **Modal "Region: Country Roads"** aparece.
2. Lista los traits, tier, weather del día (rolled at entry).
3. Formulario: cada PC elige activity de un dropdown.
4. Botón "Resolver region" → tira los activity checks, tira el encounter, tira el challenge, aplica Supply consumption.
5. Cada resultado loggeado.
6. Cierra modal, party está en el otro lado.

Esto **es la UX correcta para Buenos Aires** (A5e). Para Cemanahuac (CLAN) y Sakkara (ACKS) el modal puede ser más simple, pero el flow es el mismo.

### Panel de party (nuevo, no estaba en V5b)

Debe agregarse en V5C:
- Supply (con +/- buttons, daily auto-decrement)
- Pace selector
- Fatigue/Strife per PC
- Active activity per PC
- Boon list

## Bonus — actualización de `campaigns/buenos_aires.json`

Agregué al JSON de BA:
- `_systemConfig.journeyActivities` con las 14 actividades canónicas
- `_systemConfig.travelPace` con stats slow/normal/fast
- `_systemConfig.fatigueStrife` con definiciones
- `_systemConfig.haven` con criterio
- Hex schema extendido: `tier`, `regionId`, `haven`, `traits`, `discoveries`
- Section `regions` (vacío por ahora, para que llenes vos)

Eso queda como template para que cuando armes Buenos Aires, ya tengas los slots a llenar. El cockpit V5b actual NO usa estos campos extra (los ignora porque son specific de A5e). En V5C, cuando el sistema activo es A5e, esos campos se activan.

## Lo que falta para A5e completo en el cockpit (V5C+)

1. **Modal de region transition** (cuando cambia regionId).
2. **Panel de party** con Supply, Fatigue, Strife.
3. **Activity picker** por PC.
4. **Discovery system** — lista de discoveries por hex/region, marcadas como "found" cuando se consumen.
5. **Boon log** — boons activos del party con efecto.
6. **Pace selector** + auto-roll forced march save.
7. **Haven detection** + auto-recover fatigue/strife on long rest.
8. **Tier-based encounter tables** — el JSON los soporta, falta el render.
9. **Region editor** (UI para definir regions desde la app, no solo desde JSON).

Es razonablemente acotado. Cada uno es 1-2 horas de implementación.

## Sources

- [Exploration | Level Up](https://a5e.tools/rules/exploration)
- [Journey Activities | Level Up](https://a5e.tools/rules/journey-activities)
- [Journeys | Level Up](https://a5e.tools/rules/journeys)
- [Journey Checklist | Level Up](https://a5e.tools/rules/journey-checklist)
- [Journey Best Practices | Level Up](https://a5e.tools/rules/journey-best-practices)
- [Exploration Challenges | Level Up](https://a5e.tools/rules/exploration-challenges)
- [Trials & Treasures (A5E) — EN Publishing](https://enpublishingrpg.com/products/level-up-trials-treasures)
- [Reflections on Exploration rules in play](https://www.enworld.org/threads/reflections-on-exploration-rules-in-play.686366/)
- [What are we doing with fatigue and strife?](https://www.enworld.org/threads/what-are-we-doing-with-fatigue-and-strife.680674/)
- [Let's Take A Journey… (Level Up news)](https://www.levelup5e.com/news/lets-take-a-journey)
