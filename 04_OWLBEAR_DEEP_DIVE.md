# Owlbear Rodeo — Deep Dive y Decisión de Stack

> ITER 1 de iteración nocturna. 29 abril 2026.
> **Pregunta**: ¿OBR extension o HTML standalone? **Respuesta**: híbrido. Cockpit Judge standalone + OBR como vidriera de sesión sincrónica.

## Lo que aprendí sobre Owlbear Rodeo 2.0

### Arquitectura

- **OBR 1.0** (legacy): peer-to-peer (WebRTC + Socket.IO signaling), data en IndexedDB del browser via Dexie. Frágil: Safari borraba datos sin visitas frecuentes, antivirus barría storage, sync por NAT/firewall fallaba.
- **OBR 2.0** (actual, 2024+): **cloud-hosted**. Cada game-room corre en un sandbox de servidor; al conectarte el cliente consulta DB → te rutea al server con la sesión. **Storage permanente garantizado**, no local-storage frágil.
- Stack del cliente: TypeScript, sigue usando IndexedDB pero ahora como cache local respaldado por cloud.

### Modelo de datos

OBR organiza todo en **3 capas** (importante para entender qué podemos hackear):

1. **Room** — el contenedor más grande. Tiene URL persistente (paid) o random (free). Guarda metadatos globales del room.
2. **Scene** — un mapa dentro de un room. Un room tiene múltiples scenes (ej. wilderness + cada dungeon). Una scene puede tener **múltiples maps lado a lado** (útil para multi-piso).
3. **Item** — un objeto en una scene (token, fog shape, dibujo, marcador). Cada item tiene metadata propia.

### Metadata API (lo que importa para extensions)

OBR expone `setMetadata` / `getMetadata` para los 3 niveles:

```ts
// Room-level
await OBR.room.setMetadata({ "com.cemanahuac.campaign": { day: 12, ... } });
// Scene-level
await OBR.scene.setMetadata({ "com.cemanahuac.fog": { ... } });
// Item-level (cada token, cada hex marker, etc.)
await OBR.scene.items.updateItems([id], (item) => {
  item.metadata["com.cemanahuac.hex"] = { terrain: "selva", encounters: [...] };
});
```

Convención: **reverse-DNS namespacing** (`com.cemanahuac.x`). Sin esto los plugins se pisan.

### Límite crítico: **16kB de room metadata total**

> "Room metadata is intended for small bits of stored data for an extension. In total the room metadata must be under 16kB."
> — docs.owlbear.rodeo

Esto es **el dato más importante del deep dive**. Implicaciones:

- **No podés guardar el state completo de la campaña West Marches en room metadata.** El log de eventos solo, en pocas sesiones, ya supera 16k.
- **Podés guardarlo distribuido en items**. Si cada hex es un item de scene, cada item tiene su propia metadata sin un límite ajustado documentado (aunque la sync entre clientes prefiere payloads chicos).
- **Patrón recomendado**: room metadata = índice + URLs hacia datos pesados. El bulk vive en otro storage (Cloudflare KV, Drive, repo de GitHub).

### Otras APIs útiles

- **Player API**: roles (GM vs player), color, posición del cursor.
- **Tool API**: registrar herramientas custom en la barra (útil para "tirar encounter check").
- **Context Menu API**: items custom en el menú de click derecho ("→ Mover Clan acá").
- **Action Popover**: UI panel custom (donde podríamos meter el panel de "estado de mesa").
- **Dynamic Fog API**: extension oficial provee fog reactivo a líneas de visión (Walls + Lights). El fog "manual" (brush, triangle, hexagon) es nativo, sin extension.
- **Grid types**: square, hexagon (¡sí!), isometric. **OBR soporta hex grid nativamente** — podemos importar nuestro hex map y los tokens se snappean.

### Pricing (al 2026)

| Plan | Precio | Rooms | Storage | Custom URL |
|---|---|---|---|---|
| **Nestling** (free) | $0 | 2 permanentes | 100 MB | No (random) |
| **Fledgling** (paid) | low | 10 | 5 GB | Sí |
| **Bestling** (paid) | mid | 25 | 10 GB | Sí |

> Tu Buenos Aires Mega Campaign no necesitaría más de 1 room (custom URL). El free tier puede llegar a alcanzar — 2 rooms, 100MB. Pero "ningún custom background" implica que los mapas custom requieren tier paid.

Para West Marches con un único room persistente y custom name → **Fledgling** alcanza y sobra.

## Comparación: OBR extension vs HTML standalone

| Eje | OBR extension | HTML standalone (lo que tenemos) |
|---|---|---|
| **Persistencia** | Cloud-managed, automática | Vos definís: localStorage, KV, Drive |
| **Multi-jugador en vivo** | ✅ nativo, real-time | ✗ requiere build |
| **Fog of war** | ✅ nativo + Dynamic Fog | ✓ vos lo escribís (ya lo escribimos) |
| **Hex grid** | ✅ nativo | ✓ vos lo escribís (ya lo escribimos) |
| **Tokens / movimiento** | ✅ nativo | ✗ habría que construir |
| **Mobile / iPad** | ✅ funciona en browser iPad | ✓ HTML autocontenido también |
| **Límite de datos** | 16kB room metadata + items | Sin límite |
| **Costo** | Free hasta 2 rooms; paid para custom URL | $0 |
| **Dependencia de servicio externo** | Sí (OBR puede caer / cambiar precios) | No |
| **Customización visual** | Baja (UI de OBR) | Total (ATEM aesthetic) |
| **Lógica custom (turn loop, encounter, calendar)** | Posible vía extension TS, pero hosting de extension necesario | Trivial, todo inline |
| **Players ven sin instalar nada** | ✅ mandás link de room | ✓ HTML servido por Cloudflare |
| **Sync entre Judge y players** | ✅ instantáneo | ✗ requiere build (Cloudflare WebSocket o Worker) |
| **Curva de aprendizaje** | Media (SDK TypeScript, manifest, hosting) | Baja (vanilla JS) |
| **Aislamiento entre campañas** | Cada room aislada | Una sola URL = una sola campaña (multi-tenancy custom) |

## Hallazgos sorprendentes

1. **OBR no es PWA / no se instala**. Vive en `owlbear.rodeo`. Vos no controlás el build. La "extension" es código tuyo que se inyecta en el cliente OBR cuando un usuario instala tu extension URL en su room. Esto significa: **necesitás hosting para la extension** (no solo para los datos). Cloudflare Pages funciona perfecto.

2. **Las extensions corren en iframe sandboxado**, no en el main thread. Comunican con OBR vía postMessage envuelto en el SDK. Esto **limita lo que pueden hacer**: no pueden tocar el DOM principal, no pueden interceptar inputs nativos. Pueden agregar UI propia (tools, popovers, action menus).

3. **No hay control sobre el render del mapa**. OBR renderiza tokens y fog, vos no. Si querés un render custom (ej. el panel hex side-panel del prototipo, los iconos mexicas, las leyendas de terreno) **eso vive afuera del mapa**, en el popover o en una página propia.

4. **Una extension OBR no puede correr "headless"**. Solo se ejecuta cuando alguien tiene el room abierto. Para tracking entre sesiones (que el calendario avance cuando nadie está conectado) necesitás un backend separado igual.

5. **OBR no tiene nesting de scenes**. Para "wilderness → dungeon" hacés cambio de scene manual. La transición no es nativa, hay que codearla en una extension.

## La decisión: **Híbrido**

Después de masticar todo lo anterior:

### Cockpit del Judge = HTML standalone (lo que tenemos)

- **Sigue siendo source of truth**. Toda la lógica de campaña, calendar, log, ruleset, abstracción multi-sistema vive acá.
- Stack: HTML autocontenido + JSON + localStorage (dev) → Cloudflare Worker + KV (prod, mismo patrón que Session Editor).
- Vos lo abrís en una pestaña dedicada en el iPad, lo usás durante la sesión, sigue corriendo entre sesiones.
- **Sin límites de tamaño**. El log de 50 sesiones pesa lo que pesa.

### OBR Custom Room = vidriera de sesión sincrónica

- Cuando hay sesión, abrís OBR en una segunda pestaña (o los players lo abren en sus dispositivos).
- Importás los maps necesarios (wilderness regional, dungeon de la noche).
- El fog of war es nativo de OBR.
- Los tokens los movés en OBR (mejor UX que en el cockpit).
- **OBR es la "TV de la mesa"**, el cockpit es **tu workstation tras bambalinas**.

### Pegamento entre los dos: una mini-extension OBR

Una extension simple que:

1. **Lee la URL del cockpit** (ej. `mc-prism.com/cemanahuac/api/state`) y muestra en una popover de OBR el estado de mesa actual: día, watch, encounter table del terreno, próximas alertas.
2. **Permite "anotar evento"** desde OBR: el GM aprieta un botón en OBR y el evento se manda al cockpit (POST a Cloudflare Worker).
3. **Marca tokens con color por facción** leyendo NPCs del cockpit.
4. **Listo**. No tratamos de replicar la lógica del cockpit dentro de OBR.

Esto es un hosting chiquito (~50 líneas de TS, manifest, deploy a Cloudflare Pages) y lo dejamos para V5C/V5D. Por ahora, **con copy-paste manual entre cockpit y OBR alcanza**.

### Por qué este híbrido

- **Aprovecha lo que cada uno hace mejor**. OBR es excelente vidriera multi-player, malísimo cockpit GM-only. Standalone es excelente cockpit, malísimo vidriera multi-player.
- **No depende críticamente de OBR**. Si OBR cierra o sube precios, perdés la vidriera, no el cockpit.
- **Escalable**. Mañana podés cambiar OBR por otra cosa (Foundry, Roll20, una vidriera HTML propia) sin tocar el cockpit.
- **Tu Buenos Aires Mega Campaign con A5e no necesita más que esto**. Cockpit corre en tu laptop / iPad, OBR corre en el browser de los players, ambos miran al mismo state via dos paths.

## Plan de migración

**No hay migración**. El prototipo standalone sigue siendo la base. OBR entra en V5D cuando arranquen sesiones presenciales con muchos players y necesites la vidriera. Mientras tanto:

- ITER 2: refactor multi-campaña sigue siendo correcto.
- ITER 3 (A5e): correcto.
- ITER 4 (ruleset abstraction): correcto.
- ITER 5: agregar un punto en el check-list "decidir si querés OBR ahora o esperar a V5D".

## Lo que NO investigué (pendiente para más adelante)

- Foundry VTT como alternativa (ya descartado por complejidad, pero por si cambia el viento).
- Custom self-hosted VTT (Maptool, FreeVTT, Excalibur) → probablemente también descartar por overhead de mantenerlos.
- Encounter+ y otras OBR extensions populares — ver si reusamos lógica en vez de hacer todo desde cero (especialmente Smoke & Spectre para fog dinámico).

## Sources

- [APIs | Owlbear Rodeo Documentation](https://docs.owlbear.rodeo/extensions/apis/)
- [Metadata | Owlbear Rodeo Documentation](https://docs.owlbear.rodeo/extensions/reference/metadata/)
- [Room API | Owlbear Rodeo Documentation](https://docs.owlbear.rodeo/extensions/apis/room/)
- [Scenes | Owlbear Rodeo Documentation](https://docs.owlbear.rodeo/docs/scenes/)
- [OBR Pricing](https://www.owlbear.rodeo/pricing)
- [OBR 2.0 Dev Log 6 (architecture)](https://blog.owlbear.rodeo/owlbear-rodeo-2-0-dev-log-6/)
- [OBR SDK on GitHub](https://github.com/owlbear-rodeo/sdk)
- [OBR SDK Tutorials](https://github.com/owlbear-rodeo/sdk-tutorials)
- [Dynamic Fog Reference](https://docs.owlbear.rodeo/extensions/reference/dynamic-fog/)
- [State of the Rodeo — Subscriptions](https://blog.owlbear.rodeo/state-of-the-rodeo-lets-talk-about-subscriptions/)
