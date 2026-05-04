# Roadmap post-V6k10 · Ideas pendientes

**Estado base**: V6k10.12 funcional. Session sync DM + Players con DM como único master de mecánicas.

---

## 🎬 Idea 1: Transición dramática "Sorpresa / Combate"

**Problema**: cuando aparece un monstruo, players lo ve instantáneamente. Falta el efecto cinematográfico.

**Diseño**:
- Cuando DM dispara un encuentro (sea por wandering check positivo o force manual), el client players recibe una "transition flag" en el state.
- Players muestra **fullscreen overlay** durante 2-3 seg con:
  - Animación: "⚔ SORPRESA / COMBATE ⚔" + emoji del monstruo.
  - Color de tinte (rojo para combate, naranja para sorpresa, verde para friendly).
  - Sonido (si querés agregar audio cue).
- Después se levanta el overlay y aparece el monstruo en el mapa o el panel de combate.

**Implementación esbozada**:
- Server agrega field `pendingEvent: {type: 'encounter', monster: 'Skeletons (4)', surprise: true, expiresAt: ts}` al state.
- Players client detecta el campo en applyServerState, muestra overlay, after 2-3s manda PATCH `/api/session/:id/event-ack` para limpiarlo.
- DM puede manualmente trigger via consola o botón: `window.sessionPushEvent({type:'encounter', monster:'...', surprise:true})`.

**Costo estimado**: 30-45 min.

---

## 🕳 Idea 2: Trampas con D8 ACKS Barrowmaze (incluye bottomless pit catastrófico)

**Problema**: actualmente el cockpit detecta traps y trigger pero no usa la tabla D8 específica de Barrowmaze.

**Tabla del módulo** (a confirmar con PDF):
- 1: ?
- 2: ?
- ...
- **8: Bottomless pit** ← catastrófico

**Diseño**:
- Cuando una cell con trap es triggered:
  - DM tira D8 (auto o manual con botón).
  - Si 8: dialog "💀 BOTTOMLESS PIT — ¿qué parte del grupo cae?":
    - Vanguardia (front rank).
    - Mitad (middle / mid-rank).
    - Retaguardia (rear rank).
    - DM elige según narrativa.
  - PCs en la parte que cae quedan **out** (perdidos al pit, recuperables solo con narrativa).
- Otros resultados D8: damage, lock-in, alert monsters, etc. (extraer del módulo).

**Implementación**:
1. Re-extraer tabla D8 de traps Barrowmaze del módulo PDF (página específica).
2. Agregar a `state.dungeon` un trap-type roller.
3. UI dialog DM-only para resolver el "qué parte cae" cuando es pit.
4. Sync resultado al players (visual: PCs marcados como "down/missing").

**Costo estimado**: 1-2h (depende de extracción del módulo).

---

## 🌑 Idea 3: Modo OSCURIDAD TOTAL cuando antorcha=0 (pantalla players negra)

**Problema/Idea**: cuando se les acaba la antorcha (o el DM la apaga por evento narrativo: ventolera, agua, monstruo apaga), los players literalmente quedan **a ciegas**. Solo el DM puede seguir guiando.

**Diseño**:
- DM tiene control sobre flag `state.lightSource` (default: 'torch'/'lit').
- Cuando antorcha=0 o DM toggle a 'dark':
  - Players client: pantalla **completamente negra** (overlay opacity 100%).
  - Aparece texto: "🌑 OSCURIDAD TOTAL — esperá instrucciones del DM".
  - Las flechas siguen funcionando, pero el players no ve dónde se mueven.
  - Si chocan contra una pared, el server retorna el error pero players no ve nada.
- DM sigue viendo todo (puede narrar lo que pasa, tira encuentros, etc.).
- Recuperación: DM toggle a 'lit' → pantalla vuelve.

**Implementación**:
- Server state agrega field `lightSource: 'lit' | 'dark'` (default 'lit').
- Endpoint nuevo: `PATCH /api/session/:id/light` (DM only).
- Players client: si `lightSource === 'dark'`, render `<div class="darkness-overlay">` opacity 1, encima de todo el cockpit.
- DM ve indicador "🌑 Players a ciegas" en su badge.

**Costo estimado**: 45-60 min.

**Nota narrativa**: este feature es un **potenciador dramático real**. Ataque del Vampire Wolves apagando antorchas (cliché clásico de horror), 90% de probabilidad de TPK si se asustan. ESPECTACULAR para usar en momentos clave.

---

## 🎨 Idea 5: AI Image Generation para Eventos (V6k10.16+)

**Concepto** (de Marcos, post V6k10.15): cuando el DM ingresa el texto de un evento (sorpresa/combate/narrativa), el sistema **genera automáticamente una imagen** ilustrando la escena, vía API de un image generator.

**Diseño**:
- Server agrega field opcional `pendingEvent.imageUrl: string | null`.
- Cuando DM pushea evento, se trigger un fetch async a una API de generación:
  - **Opción Gemini (Imagen)**: `https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-...`
  - **Opción OpenAI (DALL-E 3)**: `https://api.openai.com/v1/images/generations`
  - **Opción Stable Diffusion local**: si tenés GPU, comfyui o A1111 self-hosted en tu red.
- Prompt construido del título + subtítulo + style hints ("oscuro, dungeon medieval, OSR illustration, atmospheric").
- Mientras genera (~5-15 seg), el overlay players muestra spinner "🎨 generando ilustración...".
- Cuando termina, la imagen aparece en el overlay sobre el background dramático.

**Pros**:
- Inmersión brutal — players ven la escena visualmente.
- DM no necesita preparar arte previo.
- Cada sesión genera arte único.

**Contras / consideraciones**:
- API key del DM (no players) — debería estar en config local del worker, NO hardcoded.
- Costo: DALL-E 3 ~$0.04/imagen, Imagen ~$0.02. Si DM saca 20 eventos/sesión = ~$0.4-0.8 sesión. Aceptable.
- Latencia: 5-15 seg. El overlay debería poder mostrar texto inmediato + imagen cuando llega.
- Calidad / coherencia: prompts genéricos pueden producir imágenes off-tone. Style guide ayuda.

**Implementación esbozada**:
1. Agregar `IMAGE_API_KEY` como variable secreta del Worker (`wrangler secret put IMAGE_API_KEY`).
2. Endpoint nuevo opcional: `POST /api/session/:id/event` con flag `generateImage:true` → server llama API → updates pendingEvent.imageUrl.
3. Players client: si pendingEvent.imageUrl, mostrar `<img>` en el overlay.
4. UI DM: checkbox "🎨 Generar ilustración" en los prompts de sorpresa/combate.
5. Fallback: si la API falla o demora demasiado, mostrar overlay sin imagen.

**Costo estimado**: 2-3h (worker call API + UI + manejo async).

**Decisión recomendada**: cuando Marcos quiera, evaluar primero qué API usar (Gemini Imagen tiene buen pricing y calidad). Probar con un solo evento manual antes de integrar al UI.

---

## 🎲 Idea 4: Solo Play Mode (V6k11+)

**Concepto**: jugar la dungeon sin DM presente. El cockpit hace de DM automático.

**Features**:
- Mapa con fog of war (como players).
- Markers ocultos hasta que la party "se compromete" entrando a la cell.
- Descripciones de room **narrativas** (no mecánicas) — sin stats de monstruos, sin trap detected, hasta que se trigger.
- Wandering checks automáticos.
- Trampas auto-trigger.
- Encuentros auto-resolved (cockpit tira initiative + applicable rules).
- Modal de room solo aparece **AL ENTRAR** (no al hover/click).

**Implementación**:
- Nuevo `role=solo` (en URL: `?role=solo`).
- Backend: server tracks state como hoy + flag de "solo mode".
- Frontend: filtros más estrictos que players + auto-resolutions:
  - Wandering: cockpit tira automáticamente y muestra resultado (incluyendo idea 1: transición dramática).
  - Trap: auto-trigger con D8 (idea 2).
  - Antorcha → oscuridad (idea 3): auto.
- UI narrativa: para room descriptions, usar la versión "narrative" extraída del módulo (sin stats), guardar versión "complete" para post-juego.

**Posibilidad de producto**: esto es un Roguelike tabletop digital. Hay demanda real. Vale prototypearlo primero solo, después monetizar.

**Costo estimado**: 4-6h (plantilla básica). Iterativo después.

---

## 📅 Plan sugerido para mañana (día libre)

Si hay tiempo y ganas:
1. **Reparar Idea 3** (oscuridad total) primero — es el más visualmente impactante con menos código (~45min).
2. Probar V6k10.12 + idea 3 con sesión solitaria en 2 dispositivos.
3. Si queda tiempo, prototipo de Idea 4 (solo play) — cargar el cockpit con `?role=solo` y ver qué falta esconder.

Si no hay ganas: descansar. El sprint de hoy fue intenso (~14 versiones V6k10 → V6k10.12 + bugs scope let/const + arquitectura completa session sync).

— Cockpit Valakhan · Roadmap post V6k10.12 · 2026-05-02
