# Check List de Revisiones — Iteración Nocturna 28-29 abril 2026

> Cada decisión que tomé durante la noche, con razón e impacto. Marcá ✅ aprobado / ✏️ modificar / ❌ rechazar.
> Si dejás algo sin marcar, asumo aprobado por defecto al retomar.

## ITER 1 — Owlbear Rodeo deep dive

| # | Decisión | Razón | Impacto | Estado |
|---|---|---|---|---|
| 1.1 | Stack **híbrido**: cockpit standalone + OBR como "vidriera" sincrónica futura | OBR room metadata limit es 16kB, demasiado chico para campaña West Marches con muchas sesiones | Sin migración del prototipo. OBR entra recién en V5D | [ ] |
| 1.2 | Foundry VTT **descartado** | Demasiada complejidad para una mesa chica, requiere licencia + server | No reinvestigarlo a menos que cambien necesidades | [ ] |
| 1.3 | Mini-extension OBR **diferida a V5D** (post-V5C) | Útil pero no crítico hasta tener mesas presenciales con muchos players | Permite avanzar V5C sin bloqueo de OBR | [ ] |

## ITER 2 — Refactor multi-campaña

| # | Decisión | Razón | Impacto | Estado |
|---|---|---|---|---|
| 2.1 | Separar **DB** (JSON externo) de **state** (localStorage) | Marcos pidió explícitamente esa separación | Cada campaña edita data sin tocar HTML | [ ] |
| 2.2 | **Una storage key por campaña**: `v5b_state_<campaignId>` | Cambiar campaña preserva estado de la otra | Multi-campaña simultánea sin colisiones | [ ] |
| 2.3 | **Try fetch + fallback inline** para soportar file:// | Doble click sin servidor sigue funcionando | HTML autocontenido pero permite edit JSON externo | [ ] |
| 2.4 | **Cemanahuac inline en HTML como bundle**, JSONs externos como fuente de verdad | Compromiso entre standalone y editable | Cuando edites JSON, regenerar bundle inline. Pendiente: script de bundle automático | [ ] |
| 2.5 | **3 campañas seedeadas**: cemanahuac, buenos_aires, sakkara_acks | Cubre los 3 sistemas que vas a usar | Sirve de test para multi-sistema desde día 1 | [ ] |
| 2.6 | **Hex 24mi para A5e**, hex 6mi para CLAN/ACKS | A5e usa 24mi/día normal pace; CLAN/ACKS más pequeño | Cada campaña define su `scale.size` | [ ] |

## ITER 3 — Level Up A5e exploration mapping

| # | Decisión | Razón | Impacto | Estado |
|---|---|---|---|---|
| 3.1 | **Region como unidad espacial A5e** (no hex individual) | Es como A5e funciona — "1 activity por region", no por hex | El cockpit tendrá que agrupar hexes en regions cuando sistema sea A5e | [ ] |
| 3.2 | **Tier 1-4 NO ligado a nivel PCs** (West Marches puro) | A5e RAW. Permite que una zona sea peligrosa independiente de quién entra | El cockpit mostrará tier en cada hex como atributo fijo | [ ] |
| 3.3 | **Supply como counter explícito** | A5e RAW: 1 Supply = 1 día de comida/agua para 1 PC | Panel de party tendrá un slider de Supply | [ ] |
| 3.4 | **Fatigue + Strife separados** (no Exhaustion 5e simple) | A5e RAW. Físico vs mental | Tracking per-PC con 6 niveles cada uno | [ ] |
| 3.5 | **Haven como flag de hex** | A5e RAW: solo en haven se recupera fatigue/strife ≥2 | Hex tiene `haven: true` para taberna/fortaleza/cueva-segura | [ ] |
| 3.6 | **14 journey activities canónicas** documentadas en buenos_aires.json | Cubre Trials & Treasures completo | El picker UI será un dropdown de 14 opciones | [ ] |
| 3.7 | **Watches sintéticos para A5e** (Mañana/Tarde/Noche) aunque A5e use días | Compatibilidad multi-sistema en el cockpit | Una sola UI de calendar para todos los sistemas | [ ] |

## ITER 4 — Ruleset abstraction

| # | Decisión | Razón | Impacto | Estado |
|---|---|---|---|---|
| 4.1 | **5 JSONs en `reglas/`**: turn_loop, encounter_check, weather, dungeon_turn, wandering_monster | Granularidad razonable, separa concepts | Pendiente: ¿granularidad correcta? ver Q1 abajo | [ ] |
| 4.2 | Cada regla tiene **`abstract` + `implementations.{a5e,acks,clan}` + `cockpitImplementation`** | Self-documenting, multi-sistema, tracking de pendiente | JSON un poco más grande pero todo en un lugar | [ ] |
| 4.3 | **Tier 1-4 como common denominator transversal** (A5e Tier / ACKS rarity / CLAN category) | Aporte conceptual de la noche | Tablas indexadas por (terrain, tier) en TODAS las campañas | [ ] |
| 4.4 | **Motor parametrizado, no hardcodeado**: cockpit lee `state.world.system` y despacha | Sumar Mausritter/Cairn = sumar entry al JSON, no tocar código | Curva de aprendizaje del modelo, pero escalabilidad infinita | [ ] |
| 4.5 | **Combat NO se abstrae** | Cada sistema tiene combate muy distinto, no es foco del cockpit hexcrawl | Cockpit invoca al combat tracker apropiado (acks-assistant, dnd-beyond, etc.) | [ ] |
| 4.6 | **CLAN modelado como "GM-adjudicated"** en la mayoría de reglas | CLAN no formaliza loops mecánicamente | Cockpit en modo CLAN ofrece tools opcionales pero no fuerza | [ ] |

## Preguntas abiertas (ITER 4)

| # | Pregunta | Mi voto | Tu decisión |
|---|---|---|---|
| Q1 | ¿Granularidad de 5 archivos en `reglas/` es correcta? | **5 está bien**. Podría colapsarse a 3 (turn_loop + encounter + dungeon) o expandirse a 8 (combat, social, etc.) | [ ] |
| Q2 | ¿Tier 1-4 sirve como common denominator o preferís otro modelo (lvl-of-zone numérico continuo)? | **1-4 está bien** para los 3 sistemas actuales. Continuo si sumás más sistemas con granularidades distintas | [ ] |
| Q3 | ¿`cockpitImplementation` adentro de cada JSON o en `reglas/_pending.md` separado? | **Adentro** mientras prototipa. Cuando V5C esté estable, sacar | [ ] |
| Q4 | ¿CLAN se incluye en los JSONs `implementations.clan` (con flags GM-adjudicated) o se queda fuera por ser narrativo? | **Adentro** con flag claro. Permite cambiar a más mecánico si después CLAN evoluciona | [ ] |

## Decisiones meta del proyecto

| # | Decisión | Razón | Impacto | Estado |
|---|---|---|---|---|
| M.1 | **Cemanahuac/** carpeta nueva en Desktop | Las V1-V4 vivían en COWORK web; arrancamos limpio en local | Drive sync pendiente si querés (ahora local-only) | [ ] |
| M.2 | **Stack idéntico a visores ATEM** (HTML autocontenido + JSON + Cloudflare) | Validado por la cultura ATEM, pipeline conocido | Deploy a `mc-prism.com/cockpit` o subdomain en V5D | [ ] |
| M.3 | **No tocar el prototipo `prototipo_v5.html` original** | Mantener historia de iteraciones limpia | `prototipo_v5b.html` es la siguiente. Futuras: v5c, v5d | [ ] |
| M.4 | **Iteración nocturna en `/loop` self-paced** | Marcos autorizó. Computadora prendida + créditos API | Costo aprox: ~$1-2 USD en Sonnet | [ ] |
| M.5 | **Skill `acks-judge` activo durante todo el trabajo** | Marcos lo había configurado para ACKS | Knowledge base de ACKS disponible para ITER 4 abstraction | [ ] |

## Pendientes para V5C (próxima sesión despierto)

Por orden de prioridad:

1. **Probar `prototipo_v5b.html` doble click**: confirmar que abre, cambia campañas, persiste, dungeon funciona.
2. **Decidir Q1-Q4** del ruleset abstraction.
3. **Cargar `reglas/*.json`** en el HTML al startup (hoy V5b no las usa; V5C sí).
4. **Modal de region entry** para A5e.
5. **Panel de party** (Supply, Fatigue, Strife) cuando system === "a5e".
6. **Activity picker** UI.
7. **Light tracker** + spell duration tracker en dungeon.
8. **Editor de mundo desde la UI** (agregar hex, cambiar tier, definir POI sin editar JSON manual).
9. **Bundle script**: regenerar `INLINE_CAMPAIGNS` del HTML cuando se editan los JSONs.
10. **Sync a Cloudflare KV** (pattern de Session Editor) para multi-dispositivo.

## Pendientes para V5D (mesa real BA)

11. **OBR mini-extension** que sincroniza scene+fog con el cockpit.
12. **Player view** (HTML separado, read-only, fog of war).
13. **Auth simple** para que players manden notas/correcciones.
14. **Dominio público** (ej. `mc-prism.com/cockpit/buenos_aires`).
