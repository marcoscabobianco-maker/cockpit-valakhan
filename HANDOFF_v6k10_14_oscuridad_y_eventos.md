# HANDOFF v6k10.14 · Oscuridad Total + Transición Sorpresa/Combate

**Fecha**: 2026-05-04 (sprint nocturno con wildcards)
**Estado**: ✅ Funcional, deployed, E2E backend testeado.
**Live URL**: https://mc-prism.pages.dev/cockpit
**Worker**: https://mc-prism-session.marcoscabobianco.workers.dev
**Última versión**: v6k10.14
**Cache-bust query**: `?v=v6k10p14`

---

## 🎯 Lo que se agregó esta noche

### 🌑 Idea 3: Modo Oscuridad Total (V6k10.13)

Cuando el DM toca el botón **🌑 Apagar luz players**, el iPad de los players muestra una pantalla **completamente negra** con texto:
> 🌑 OSCURIDAD TOTAL
> Esperá las instrucciones del DM. Tu antorcha se apagó o algo bloqueó la luz.

El DM sigue viendo todo normal. Mientras la luz está apagada, el DM ve un indicador rojo arriba a la derecha: **🌑 Players a ciegas**.

**Casos de uso narrativos**:
- Antorcha agotada (ahora sí podés simular el horror).
- Ventolera apaga las teas en la cripta.
- Vampire Wolf attack: bestia apaga antorchas (clásico de horror).
- Final dramático de sesión: oscuridad antes del cliffhanger.

Volvés a encender con **☀ Encender luz players** (mismo botón, cambia label).

### 🎬 Idea 1: Transición Sorpresa/Combate/Narrativa (V6k10.14)

3 botones nuevos en el panel DM (esquina inferior derecha):

- **💀 Sorpresa**: prompt te pregunta el monstruo. Players ve **fullscreen overlay rojo** con `💀 SORPRESA · Aparece: Skeletons (4)` durante 4 segundos, después desaparece automáticamente.
- **⚔ Combate**: similar pero rojo oscuro. `⚔ COMBATE · Enemigo: ...`.
- **📜 Custom**: prompt te pide texto + emoji. Para narrativa libre. Color verde, 5 seg.

El DM mismo recibe un toast pequeño confirmando que el evento se envió.

**Cómo se ve en players**:
- Fade-in de 0.4s.
- Background gradiente radial desde el color del evento hacia negro.
- Emoji animado (pulse).
- Título grande con letterspacing.
- Subtítulo descriptivo.
- Después de N segundos (ajustable, default 4-5s), desaparece con fade-out.

---

## 🎮 Cómo usar (paso a paso)

### Setup inicial
1. Abrí https://mc-prism.pages.dev/cockpit en desktop.
2. Hard refresh: **Ctrl+Shift+R**.
3. Botón flotante **🔗 Iniciar sesión compartida** → crea sesión.
4. iPad: scan QR → abre players.
5. Verificá badge `sync v6k10p14` en ambos.

### En sesión

**Esquina inferior izquierda** (DM standalone): botón "🔗 Iniciar sesión compartida" (lo de siempre).

**Esquina inferior derecha** (DM en session): nuevos controles:
```
[🌑 Apagar luz players]
[💀 Sorpresa] [⚔ Combate] [📜 Custom]
```

**Cuándo usar**:
- Players entran a sala con bestia → click 💀 Sorpresa, escribís "Wight (1)".
- DM tira wandering check positivo → click ⚔ Combate, escribís "Skeletons (4)".
- Algo narrativo importante (DM lee descripción dramática) → click 📜 Custom, ponés texto + emoji 🌫.
- Antorcha se apaga / quieren entrar a oscuras → click 🌑 Apagar luz.

---

## 🏗 Cambios técnicos (para futuros sprints)

### Server (worker.js)
Nuevos campos en `SessionState`:
- `lightSource: 'lit' | 'dark'` (default 'lit').
- `pendingEvent: { id, type, title, subtitle, color, emoji, durationMs, pushedAt } | null`.

Nuevos endpoints:
- `PATCH /api/session/:id/light` (DM only): `{ lightSource: 'lit'|'dark' }`.
- `POST /api/session/:id/event` (DM only): event payload.
- `POST /api/session/:id/event/ack` (any role): clears pendingEvent (auto-llamado por client cuando termina el overlay).

### Client (session-sync.js)
Nuevas funciones expuestas:
```js
window.sessionToggleLight(lightSource?)   // toggle si no se pasa arg
window.sessionPushEvent({type, title, subtitle, color, emoji, durationMs})
window.sessionPushSurprise(monster?)      // preset rojo, 4s
window.sessionPushCombat(monster?)        // preset rojo oscuro, 4s
window.sessionPushNarrative(text, emoji?) // preset verde, 5s
```

Overlays inyectados al body:
- `#session-dark-overlay` (display:none por defecto, fullscreen negro).
- `#session-event-overlay` (display:none, gradient + emoji + título).
- `#session-dm-controls` (panel flotante DM-only).
- `#session-dm-light-indicator` (badge "🌑 Players a ciegas" cuando dark).

CSS animaciones inyectadas:
- `pulseEmoji` (emoji del evento pulsa cada 0.6s).
- `fadeInEvent` (0.4s al aparecer).

---

## ✅ Tests E2E (verde, ya verificado backend)

```
✓ Create session → lightSource:lit + pendingEvent:null
✓ DM PATCH /light dark → lightSource:dark
✓ Players GET → ve lightSource:dark (markers field NO presente)
✓ Players intenta /light → 403 "Only DM can toggle light"
✓ DM POST /event {type:'surprise',title:'SORPRESA',...} → event guardado
✓ Players GET → ve pendingEvent
✓ POST /event/ack → pendingEvent cleared
```

Pendiente verificar visual con vos:
- [ ] Hard refresh ambos dispositivos.
- [ ] DM ve panel inferior derecho con 4 botones.
- [ ] Click 🌑 → players pantalla negra inmediata.
- [ ] Click 💀 Sorpresa → players ve overlay 4s.
- [ ] Click ⚔ Combate → players ve overlay 4s.
- [ ] Click 📜 Custom → players ve overlay 5s con texto custom.

---

## 📝 Pendiente (para tu día libre o próximo sprint)

### Idea 1 — trigger automático
Actualmente el DM dispara los eventos manualmente. Para auto-trigger cuando `dgAdvance` materializa un encuentro: hay que hookear a `dgRollBarrowmazeEncounter()` o similar y disparar `sessionPushSurprise(monsterName)` automáticamente. Bajo riesgo, ~30 min, pero requiere identificar el hook exacto en el cockpit.

### Idea 2 — Trampas D8 ACKS Barrowmaze
Sin tocar todavía. Necesita:
1. Extracción de la tabla D8 del módulo (página específica del PDF).
2. Confirmación con vos de qué dice cada entrada (especialmente 8 = bottomless pit).
3. Dialog DM-only "qué parte cae" (vanguardia/mitad/retaguardia) para PCs.
4. Sync resultado al players (visual: PCs marcados como out/missing).

### Idea 4 — Solo Play Mode
Sin tocar. Necesita decisiones UX con vos:
- ¿Qué se oculta hasta que la party "se compromete"?
- ¿Cómo se materializan encuentros automáticos?
- ¿Modo narrativo de descripciones (sin stats)?

---

## 🔧 Re-deploy si hace falta

```bash
# Worker (si modificás worker.js o wrangler.toml)
cd C:/Users/Usuario/COWORK/ATEM/mc-prism-deploy/session-sync
npx wrangler deploy

# Pages (si modificás cockpit.html o session-sync.js)
cd C:/Users/Usuario/COWORK/ATEM/mc-prism-deploy
npx wrangler pages deploy . --project-name=mc-prism

# IMPORTANTE: si modificás session-sync.js, bumpear el query string en cockpit.html
# (ej: ?v=v6k10p14 → ?v=v6k10p15)
```

---

## 🎮 Quick reference de comandos JS (DM consola)

Si los botones del panel DM no son suficientes, podés usar consola:

```js
// Apagar luz
window.sessionToggleLight('dark')
// Encender luz
window.sessionToggleLight('lit')
// Toggle (alterna)
window.sessionToggleLight()

// Push evento sorpresa
window.sessionPushSurprise('Wight (1)')

// Push combate
window.sessionPushCombat('Skeletons (4)')

// Custom narrativa
window.sessionPushNarrative('Sentís un olor a putrefacción', '🌫')

// Custom completo
window.sessionPushEvent({
  type: 'surprise',
  title: '☠ MUERTE',
  subtitle: 'Aldric Voss recibe un golpe crítico',
  color: '#000',
  emoji: '☠',
  durationMs: 6000,
})
```

— Cockpit Valakhan v6k10.14 · Oscuridad + Eventos · 2026-05-04 (sprint nocturno)
