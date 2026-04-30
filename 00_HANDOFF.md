# Handoff Cockpit V5 — Iteración Nocturna 28-29 abril 2026

> Trabajo dejado por Claude mientras Marcos descansaba. 5 iteraciones, ~5 horas de trabajo asíncrono.
> **Empezá leyendo este archivo, después decidí qué leer en profundidad.**

---

## TL;DR (30 segundos)

Pasamos de un prototipo hex map para Cemanahuac/CLAN a un **cockpit multi-campaña multi-sistema** con:
- 3 campañas seedeadas (Cemanahuac/CLAN, Buenos Aires/A5e, Sakkara/ACKS)
- Engine separado de data (HTML + JSONs externos)
- Abstracción de reglas que cubre A5e + ACKS + CLAN con un solo motor parametrizado
- Decisión de stack: **HTML standalone + Owlbear Rodeo como vidriera futura** (NO Foundry)
- Plan claro de V5C (próxima impl) y V5D (deploy multi-jugador)

**Para retomar**: abrí `prototipo_v5b.html` doble click → revisá multi-campaña funciona → leé `CHECK_LIST_REVISIONES.md` → marcá lo que aprobás.

---

## Qué leer y en qué orden

| # | Archivo | Tiempo | Razón |
|---|---|---|---|
| 1 | `CHECK_LIST_REVISIONES.md` | 10 min | **Empezá acá**. Todas mis decisiones con razón e impacto. Marcá ✅/✏️/❌. |
| 2 | `prototipo_v5b.html` (abrir doble click) | 5 min | Confirmá que el cockpit multi-campaña funciona. Cambiá campañas en el header, navegá hex, bajá a dungeon. |
| 3 | `04_OWLBEAR_DEEP_DIVE.md` | 10 min | La decisión arquitectónica más grande de la noche. Por qué stack híbrido. |
| 4 | `06_RULESET_ABSTRACTION.md` | 15 min | El modelo conceptual para multi-sistema. **Tier 1-4 transversal es el aporte clave.** |
| 5 | `05_LEVEL_UP_A5E.md` | 10 min | Todo el sistema A5e mapeado al cockpit. Si vas a correr Buenos Aires con A5e, leé esto. |
| 6 | `02_ARQUITECTURA_V5.md` | 10 min | El plan original (3 escalas anidadas, DB vs vista de mesa). Sigue vigente. |
| 7 | `01_FORMATOS_PARALELOS.md` | 5 min | Comparativa con Foundry/Owlbear/etc. Ya está cocinado en ITER 1. |
| 8 | `03_PROTOTIPO_HTML.md` | 5 min | Manual de uso del prototipo V5 original. (V5b mantiene la mayoría del UX.) |

---

## Archivos generados (mapa completo)

```
Desktop/Cemanahuac/
├── 00_HANDOFF.md                    ← este archivo
├── CHECK_LIST_REVISIONES.md         ← ⭐ empezá acá
├── 01_FORMATOS_PARALELOS.md         (pre-loop, formatos comparados)
├── 02_ARQUITECTURA_V5.md            (pre-loop, 3 escalas, DB vs mesa)
├── 03_PROTOTIPO_HTML.md             (pre-loop, manual del prototipo V5)
├── 04_OWLBEAR_DEEP_DIVE.md          (ITER 1, decisión stack)
├── 05_LEVEL_UP_A5E.md               (ITER 3, mapping A5e completo)
├── 06_RULESET_ABSTRACTION.md        (ITER 4, modelo multi-sistema)
├── _aventura_los_sesenta.txt        (texto del PDF Cemanahuac CLAN)
├── prototipo_v5.html                (V5 original, con Cemanahuac inline)
├── prototipo_v5b.html               (V5b, multi-campaña, JSONs externos + fallback inline)
├── campaigns/
│   ├── cemanahuac.json              (CLAN seed completo: 48 hexes, 6 monstruos, dungeon Coatépec)
│   ├── buenos_aires.json            (A5e template: 14 activities, supply, tier, journey config)
│   └── sakkara_acks.json            (ACKS placeholder lincando a acks-assistant)
└── reglas/
    ├── turn_loop.json               (spatial loop genérico, 6 phases)
    ├── encounter_check.json         (cuándo/cómo se tira encuentro)
    ├── weather.json                 (weather roll abstraction)
    ├── dungeon_turn.json            (dungeon turn 10-min loop)
    └── wandering_monster.json       (wandering subset de encounter)
```

**Total**: 7 documentos MD, 2 prototipos HTML, 8 JSONs (3 campañas + 5 reglas), 1 texto extraído. ~150 KB en disco.

---

## Resumen por iteración

### ITER 1 ✓ (Owlbear Rodeo deep dive)
- Investigué OBR a fondo (arquitectura cloud, extension API, pricing).
- **Hallazgo central**: 16 kB de room metadata. Demasiado chico para campaña West Marches.
- **Decisión**: stack híbrido. Cockpit Judge sigue siendo HTML standalone. OBR entra en V5D como vidriera de sesión sincrónica multi-player.
- Foundry definitivamente descartado.

### ITER 2 ✓ (Refactor multi-campaña)
- `prototipo_v5b.html` con engine multi-campaña.
- 3 JSONs en `campaigns/` (Cemanahuac completo, BA template, Sakkara placeholder).
- Selector de campaña en header con tag de sistema.
- `localStorage` separado por campaña — cambiar campaña preserva estado.
- Strategy: try fetch + fallback inline (file:// funciona doble click).
- Validado: `node --check` JS ✓, `python json.load` los 3 JSONs ✓.

### ITER 3 ✓ (Level Up A5e mapping)
- A5e exploration system mapeado al cockpit, concepto por concepto.
- 14 Journey Activities documentadas (Befriend Animal, Busk, Chronicle, Cook, Cover Tracks, Entertain, Gather Components, Gossip, Harvest, Hunt and Gather, Pray, Rob, Scout, Track).
- **Hallazgos clave A5e**:
  - Region (no hex) es la unidad espacial.
  - Tier 1-4 NO ligado a nivel PCs (West Marches puro).
  - Supply = party HP de viaje.
  - Fatigue + Strife reemplazan Exhaustion 5e.
- `buenos_aires.json` expandido con `_systemConfig` completo: supply, travelPace, journeyActivities, fatigueStrife, haven, regionTiers, explorationChallenges.

### ITER 4 ✓ (Ruleset abstraction)
- 5 JSONs en `reglas/` con `abstract` + `implementations.{a5e,acks,clan}` + `cockpitImplementation`.
- **Aporte conceptual**: tier 1-4 transversal (A5e Tier / ACKS rarity / CLAN category).
- **Modelo del motor**: cockpit lee `state.world.system`, busca esa key en JSONs, aplica parámetros. **Sin reglas hardcodeadas**.
- Sumar Mausritter/Cairn = agregar entry al JSON, no tocar código.
- 4 preguntas de diseño abiertas (al final del MD) para tu confirmación.

### ITER 5 ✓ (este wake)
- `CHECK_LIST_REVISIONES.md` con todas las decisiones en formato checkbox.
- Este `00_HANDOFF.md` reescrito limpio.
- Loop terminado, sin más wakes programados.

---

## Próximos pasos (cuando despiertes)

### Inmediato (5-15 min)
1. **Abrí `prototipo_v5b.html`** (doble click). Probá cambiar campañas. Probá bajar a Coatépec.
2. **Leé `CHECK_LIST_REVISIONES.md`** y marcá ✅/✏️/❌ rápido.
3. **Decidí Q1-Q4** del ruleset abstraction (4 preguntas de diseño).

### Corto plazo (1-3 horas, V5C)
4. Cargar `reglas/*.json` al startup (hoy V5b no las usa, V5C las dispatchea).
5. Modal de **region entry** para A5e.
6. **Panel de party** (Supply, Fatigue, Strife).
7. **Activity picker** UI.
8. **Light tracker** + spell duration en dungeon.

### Mediano plazo (V5D, mesa real BA)
9. OBR mini-extension para sincronizar.
10. Player view separado.
11. Deploy a `mc-prism.com/cockpit/buenos_aires`.

---

## Costo aproximado de la noche

5 iteraciones × ~50k tokens input + ~15k output cada una = **~325k tokens**. En Sonnet (lo que estoy usando): **~USD $1-2**. Dentro del presupuesto que mencionaste.

---

## Lo que NO hice (deliberadamente)

- **No toqué el prototipo `prototipo_v5.html`** original. Mantengo la historia limpia de versiones.
- **No expandí el bestiario CLAN** ni los POIs Cemanahuac (es contenido, no sistema — lo armás vos despierto).
- **No hice el calendario mexica** completo (mismo motivo).
- **No deployé nada** a Cloudflare (V5D, post tu OK).
- **No iteré sobre decisiones arquitectónicas** dudosas. Las dejé como preguntas en el check list.

---

## Para descansar tranquilo

Si todo sale mal y tenés que tirar la noche a la basura:
- El prototipo v5 original está intacto.
- Los visores ATEM no se tocaron.
- `acks-assistant` no se tocó.
- Solo la carpeta `Cemanahuac/` es nueva.
- `localStorage` del browser solo se afectaría si abriste v5b, y se resetea con el botón "Reset" del header.

Buen día cuando despiertes 🜂
