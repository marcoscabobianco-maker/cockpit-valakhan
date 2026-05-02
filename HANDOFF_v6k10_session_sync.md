# HANDOFF v6k10 · Session Sync DM + Players

**Fecha cierre**: 2026-05-02
**Live URL**: https://mc-prism.pages.dev/cockpit
**Última versión**: v6k10
**Última deploy CF Pages**: e6a7e81c
**Worker session-sync**: https://mc-prism-session.marcoscabobianco.workers.dev

---

## 🎯 Lo que hace V6k10

Permite tener **2 dispositivos sincronizados en tiempo real** (DM + Players) compartiendo la misma sesión de juego, sin cuentas, sin login, sólo con un link/QR.

**Vista DM** (desktop, esta máquina): mapa completo, markers, descripciones, todo. NO mueve.
**Vista Players** (iPad): solo fog of war + party visible, ningún detalle DM. SÍ mueve (el caller).

Cuando los players mueven, el DM lo ve en menos de 1 segundo. Cuando el DM agrega un marker, queda solo en su vista (los players nunca lo reciben — filtrado server-side).

---

## 🚀 Cómo usarlo

1. Abrí https://mc-prism.pages.dev/cockpit en tu desktop.
2. Apretá el botón flotante **🔗 Iniciar sesión compartida** (esquina inferior izquierda).
3. Dialog te pregunta sectionId, startX/Y, party ft/turn, cell ft. Acepta defaults o ajustá.
4. Click **Crear sesión**. Te muestra:
   - URL DM con botón "Abrir aquí" (la abre en esta misma tab).
   - URL Players con QR + botón Copiar.
5. **iPad players**: scan QR (o tipea URL). Se abre el cockpit en modo players.
6. **Caller del party**: usa flechas / WASD / tap para mover en el iPad. El DM ve la posición + tiempo en vivo.
7. **DM**: clickea markers, ve descripciones, todo lo del cockpit normal. Pero NO mueve la party — eso lo controla el caller.

Sesión expira automáticamente a las 8 horas (TTL).

---

## 🏗 Arquitectura

```
┌──────────────────┐                ┌──────────────────────────┐
│  iPad Players    │ ───polling───► │ Cloudflare Worker        │
│  cockpit?role=   │ ◄──state─────  │ mc-prism-session         │
│   players&t=...  │                │ (DurableObject = state)  │
└──────────────────┘                │                          │
                                    │  GET     /api/session/   │
┌──────────────────┐                │  PATCH   /move           │
│  Desktop DM      │ ───polling───► │  POST    /markers        │
│  cockpit?role=   │ ◄──state─────  │  DELETE  /markers/:id    │
│   dm&t=...       │                │  PATCH   /section        │
└──────────────────┘                │  POST    /reset          │
                                    └──────────────────────────┘
                                              ▲
                                              │ filtering por rol
                                              │ (markers nunca al players)
```

### Componentes nuevos

| Archivo | Ubicación | Propósito |
|---|---|---|
| `worker.js` + `wrangler.toml` | `mc-prism-deploy/session-sync/` | Cloudflare Worker con DurableObject. Endpoints `/api/session/...`. TTL 8h via alarms. |
| `session-sync.js` | `mc-prism-deploy/` | Client-side: detecta URL params, hace polling 800ms, override `gridMoveReal` para mandar PATCH al server, hide UI por rol. |
| `cockpit.html` (V6k10) | `mc-prism-deploy/` | Patch al final: `<script src="session-sync.js">` + botón flotante "Iniciar sesión compartida" + dialog de creación con QR. |

### Endpoints del Worker

| Método | Path | Rol | Body | Acción |
|---|---|---|---|---|
| POST | `/api/session/create` | — | `{moduleId, sectionId, startX?, startY?, partyFtPerTurn?, cellFt?}` | Crea sesión, devuelve tokens y paths |
| GET | `/api/session/:id?role=&t=` | both | — | Lee state filtrado por rol |
| PATCH | `/api/session/:id/move` | players | `{dx, dy, visible?, seen?}` | Mueve party |
| POST | `/api/session/:id/markers` | dm | `{x, y, label?, color?}` | Agrega marker |
| DELETE | `/api/session/:id/markers/:markerId` | dm | — | Borra marker |
| PATCH | `/api/session/:id/section` | dm | `{sectionId, startX?, startY?, clearMarkers?}` | Cambia sección |
| POST | `/api/session/:id/reset` | dm | `{startX?, startY?, clearMarkers?}` | Resetea estado |

---

## ⚙️ Decisiones clave

1. **Cloudflare Worker + Durable Objects (no Vercel Next.js)**. Razón: el cockpit ya vive en Cloudflare Pages, hay un Worker prevoy (`mc-prism-audio`), y el handoff dice no tocar `mc-prism` Next.js. DOs son perfectos para session state (TTL via alarm, atomic writes, ~$0 free tier).

2. **Filtering server-side**, no client-side. Los markers se borran del response JSON ANTES de mandarlos al players. Si el players abre devtools, no puede ver markers.

3. **Players controlan movimiento, DM es spectator de movimiento**. El DM solo agrega markers / cambia sección / reset. Encaja con el rol de "caller del grupo" en mesa real.

4. **Polling 800ms** (no WebSockets en V1). Estable, simple, ~150 req/min con sólo 2 clientes. Si después necesitamos sub-segundo, migración a SSE/WS no rompe el contrato.

5. **Tokens random 16-hex** distintos por rol. Sin login. Cada sesión tiene 2 tokens (DM y players). El URL los lleva en query string (visible en logs locales — aceptable para uso casero).

6. **TTL 8h via DurableObject alarm**. Sesión se borra sola del storage. Sin cleanup manual.

7. **Movement con delta `{dx,dy}` ortogonal de 1 cell**. Validación server-side `|dx|+|dy|=1`. Race condition-proof.

8. **Server stores `seen`/`visible` pero también acepta el set computado client-side** (porque el cockpit ya tiene la lógica de line-of-sight). Server lo guarda como fuente de verdad para syncs.

---

## 🔧 Cómo redeployar

### Worker (si modificás `worker.js` o `wrangler.toml`)
```bash
cd C:/Users/Usuario/COWORK/ATEM/mc-prism-deploy/session-sync
npx wrangler deploy
```

### Cockpit (Pages)
```bash
cd C:/Users/Usuario/COWORK/ATEM/mc-prism-deploy
npx wrangler pages deploy . --project-name=mc-prism --commit-message="..."
```

---

## 🐛 Debugging

- **Sin sesión activa**: cockpit funciona standalone (modo V6k9 normal). Aparece botón flotante para crear.
- **Sesión activa**: aparece badge top-right con role y status (`v18 · 12.5min` o `error inicial`).
- **Worker logs**: `npx wrangler tail mc-prism-session` desde `session-sync/`.
- **Manual test**: `curl -X POST https://mc-prism-session.marcoscabobianco.workers.dev/api/session/create -H "Content-Type: application/json" -d '{"moduleId":"barrowmaze","sectionId":"bm-upper-01"}'`

---

## 🔑 Permisos confirmados

OK sin preguntar:
- ✅ Editar `mc-prism-deploy/` y deploy a CF Pages.
- ✅ Crear/modificar `mc-prism-deploy/session-sync/` y deploy via wrangler.
- ✅ Commit + push a `cockpit-valakhan`.

NO autorizado sin preguntar:
- ❌ Modificar `mc-prism` Next.js.
- ❌ Tocar credenciales.

---

## 📝 Pendientes / mejoras futuras

1. **Render de markers DM en el canvas**: actualmente los `sessionMarkers` (notas que el DM agrega via `window.sessionAddMarker(x, y, label)`) se reciben en el state pero NO se dibujan visualmente todavía. Hay que hookear `redrawGridRealCanvas` para agregar pins amarillos por cada session marker. Trabajo de ~30 min.

2. **UI DM para placar markers**: actualmente sólo se hace via consola JS. Agregar shift+click en canvas (DM mode) → dialog "label?" → POST `/markers`.

3. **Players online indicator**: ping del players → server registra lastSeen. DM ve "🟢 Players conectado" o "🔴 Players offline". Trivial agregar.

4. **Multi-section**: actualmente el module/section se setea al crear. Si el DM cambia sección via PATCH `/section`, el cockpit client tiene que reload el wallmap nuevo. No implementado todavía.

5. **WebSocket / SSE**: si polling 800ms se siente laggy, migrar a SSE para push-down (server → client). Worker DOs soportan WebSockets nativos.

6. **Ratelimit**: si alguien abusa del create endpoint, bloquear por IP. No critical para uso casero.

— Cockpit Valakhan v6k10 · Session Sync · 2026-05-02
