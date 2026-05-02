# HANDOFF v6k10.9 · Session Sync DM + Players · FINAL FUNCIONAL

**Fecha cierre**: 2026-05-02
**Estado**: ✅ Funcional E2E (movement + sync + roles + wandering/antorcha integrados)
**Live URL**: https://mc-prism.pages.dev/cockpit
**Worker**: https://mc-prism-session.marcoscabobianco.workers.dev
**Última versión**: v6k10.9
**Cache-bust query**: `?v=v6k10p9`

---

## 🎉 Lo que hace funcionar

Permite **2 dispositivos sincronizados en tiempo real** para la misma sesión de juego:

- Setup probado: **desktop DM + iPad Players** y **2 iPads**.
- Latencia: ~1 segundo (polling 800ms).
- Sin login, sin cuentas. Acceso por link/QR.
- TTL automático 8h.

**Vista DM** (desktop o iPad): mapa completo, markers, descripciones, todo.
**Vista Players** (otro dispositivo): solo fog of war + party + tiempo. Sin info DM.

**Ambos roles pueden mover** (V6k10.3 en adelante). El primero que apriete tecla manda el delta. El otro sincroniza en <1s. Eso permite tanto el flujo "el caller players mueve" como el de compromiso "el DM mueve y describe".

---

## 🐛 Recorrido de bugs y fixes (lecciones aprendidas)

Esto fue un proceso iterativo de debug. Para futuro:

| Versión | Bug | Causa raíz | Fix |
|---|---|---|---|
| V6k10 | Inicial | — | Worker + DO + cockpit hookeado |
| V6k10.1 | Players ve markers DM | toggle button visible | force `_markersHidden=true` for players |
| V6k10.2 | Players no se mueve | startX/Y arbitrario (12,8) NO walkable | default a (32,84) = sala_74A_cell real |
| V6k10.3 | DM no puede mover (a veces se quería) | restricción rígida | ambos roles pueden mover; diag panel in-app |
| V6k10.4 | Wallmap nunca cargaba en URL session directa | cockpit lazy-loadea solo via tab Dungeon click | auto-call `gridLoadRealMap()` al boot |
| V6k10.5 | Browser cacheaba session-sync.js viejo | mismo query string `?v=` | bump query a `?v=v6k10p5` |
| V6k10.6 | "¿Estoy en versión live?" — confusión | badge mostraba state version, no sync version | badge multi-línea con SYNC_VERSION + moduleId/sectionId |
| V6k10.7 | Move bloqueado: `_realWallmap not loaded` | **`let _realWallmap` NO se expone como `window._realWallmap`** | flag local `_wallmapReady` set on Promise resolve |
| V6k10.8 | Move falla: `unknown dir down` | **`const GRID_DIRECTIONS` NO está en `window`** | tabla `DIRS` propia en session-sync |
| V6k10.9 | No tira wandering/antorcha | mi override no llamaba `dgAdvance()` | delegar al gridMoveReal original + sync server después |

**Lección clave** (v6k10.7+8): top-level `let` y `const` en módulos JS modernos NO se cuelgan de `window`. Solo `var` lo hace. Si necesitás cross-script access, exponer explícitamente: `window.X = X;`.

---

## 🏗 Arquitectura final

```
┌──────────────────────┐                  ┌─────────────────────────────┐
│  iPad Players        │                  │ Cloudflare Worker           │
│  cockpit?role=       │  polling 800ms   │ mc-prism-session            │
│   players&t=...      │ ◄──────────────► │ DurableObject SessionDO     │
└──────────────────────┘                  │ TTL 8h via alarm            │
                                          │                             │
┌──────────────────────┐                  │  POST   /api/session/create │
│  Desktop o iPad DM   │  polling 800ms   │  GET    /api/session/:id    │
│  cockpit?role=       │ ◄──────────────► │  PATCH  /move (any role)    │
│   dm&t=...           │                  │  POST   /markers (DM)       │
└──────────────────────┘                  │  DELETE /markers/:id (DM)   │
                                          │  PATCH  /section (DM)       │
                                          │  POST   /reset (DM)         │
                                          └─────────────────────────────┘
                                                        ▲
                                                        │ filtering por rol
                                                        │ (markers nunca al players)
```

### Componentes

| Archivo | Ubicación | Función |
|---|---|---|
| `worker.js` + `wrangler.toml` | `mc-prism-deploy/session-sync/` | CF Worker + SessionDO. SQLite-backed (free plan). |
| `session-sync.js` | `mc-prism-deploy/` | Client layer: detecta URL params, polling, override gridMoveReal, hide UI por rol, diag panel. |
| `cockpit.html` (V6k10.9) | `mc-prism-deploy/` | Cockpit + `<script src="session-sync.js?v=v6k10p9">` + dialog crear sesión + botón flotante. |

### Endpoints

| Método | Path | Rol | Body | Acción |
|---|---|---|---|---|
| POST | `/api/session/create` | — | `{moduleId, sectionId, startX?, startY?, partyFtPerTurn?, cellFt?}` | crea sesión, devuelve tokens y paths |
| GET | `/api/session/:id?role=&t=` | both | — | lee state filtrado por rol |
| PATCH | `/api/session/:id/move` | any | `{dx, dy, visible?, seen?}` | mueve party (delta ortogonal de 1) |
| POST | `/api/session/:id/markers` | dm | `{x, y, label?, color?}` | agrega marker |
| DELETE | `/api/session/:id/markers/:markerId` | dm | — | borra marker |
| PATCH | `/api/session/:id/section` | dm | `{sectionId, startX?, startY?, clearMarkers?}` | cambia sección |
| POST | `/api/session/:id/reset` | dm | `{startX?, startY?, clearMarkers?}` | resetea estado |

---

## ⚙️ Defaults ACKS (V6k10.9)

| Campo | Default V6k10.9 | Notas |
|---|---|---|
| `partyFtPerTurn` | **120** | ACKS exploration speed estándar (Light load) |
| | 90 | si encumbered (heavy armor) |
| | 240 | si carrying light only (no armor) |
| `cellFt` | **10** | 1 cell = 10 ft (estándar dungeon) |
| `startX` | **32** | sala 74A real cell X |
| `startY` | **84** | sala 74A real cell Y |
| `moduleId` | barrowmaze | |
| `sectionId` | bm-upper-01 | |

Una vez creada la sesión, estos valores quedan fijos. Para cambiar: nueva sesión.

---

## 🔧 Cómo usarlo

### Crear sesión (DM)
1. Abrí https://mc-prism.pages.dev/cockpit en tu desktop (o cualquier dispositivo).
2. Botón flotante esquina inferior izquierda: **🔗 Iniciar sesión compartida**.
3. Confirma defaults o ajusta y click "Crear sesión".
4. Te muestra:
   - **DM URL** + botón "Abrir aquí" (recarga esta tab en modo DM).
   - **Players URL** + QR + botón Copiar.

### Conectar iPad Players
- Scan QR con Camera app de iPad → opens Safari directamente.
- O tipear la URL Players manualmente.
- iPad va a iniciar en role=players: ve solo fog + party.

### Caller mueve (recomendado)
- iPad Players: flechas/WASD/touch. Cada move → server → DM ve actualizado en <1s.
- Wandering checks, antorcha agotada, atardecer/noche: todo se dispara automáticamente en el dispositivo que mueve.

### DM mueve (alternativo)
- Desktop DM: mismas teclas. El iPad Players ve el cambio sincronizado.
- Mismos triggers de wandering/antorcha en el dispositivo que mueve.

### Verificación in-app
Badge superior derecho:
- **Línea 1**: `🛡 DM` o `🎲 Players` · `v18 · 12.5min` · `diag`
- **Línea 2**: `sync v6k10p9 · barrowmaze/bm-upper-01 · 98783e00`

Tap **diag** → panel con todos los estados internos (gridState, server state, wallmap loaded, log de eventos).

---

## 📝 Pendientes futuros (no bloqueantes)

1. **Render visual de session markers DM en canvas**: server los manda, falta dibujar pins. ~30 min.
2. **UI DM para placar markers**: actualmente solo via consola `window.sessionAddMarker(x, y, label)`. Agregar Shift+click en canvas para DM. ~30 min.
3. **Wandering/antorcha en el otro dispositivo**: actualmente solo el que mueve dispara los rolls/alerts. Para que ambos los vean, necesitaría broadcasting de eventos vía server. v2.
4. **WebSocket en lugar de polling**: si laggy, migrar. Free tier de DO soporta WebSockets.
5. **Multi-section**: cambiar sectionId mid-session. Implementado en server pero falta UI cliente.
6. **Players online indicator**: ping al server, DM ve estado.

---

## 🔧 Re-deployar

### Worker (cambios en `worker.js` o `wrangler.toml`)
```bash
cd C:/Users/Usuario/COWORK/ATEM/mc-prism-deploy/session-sync
npx wrangler deploy
```

### Cockpit/Pages (cambios en `cockpit.html` o `session-sync.js`)
```bash
cd C:/Users/Usuario/COWORK/ATEM/mc-prism-deploy
npx wrangler pages deploy . --project-name=mc-prism --commit-message="..."
```

**IMPORTANTE**: si modificás `session-sync.js`, hay que **bumpear el query string** de `?v=v6k10p9` a `?v=v6k10p10` etc. en `cockpit.html`. Sino el browser sirve cache vieja.

---

## 🔑 Permisos confirmados (no cambian)

OK sin preguntar:
- ✅ Editar `mc-prism-deploy/` y deploy a CF Pages.
- ✅ Modificar Worker `mc-prism-deploy/session-sync/`.
- ✅ Commit + push a `cockpit-valakhan`.

NO autorizado sin preguntar:
- ❌ Modificar `mc-prism` Next.js.
- ❌ Vercel.
- ❌ Tocar credenciales.

---

## 🎯 Estado final del cockpit Valakhan

| Feature | Estado |
|---|---|
| Mapa Barrowmaze real (5256×4888 stitched) | ✅ |
| Wallmap 90.8% reachable | ✅ |
| Markers reales (391) extraídos del PDF vector (V6k7+v8) | ✅ |
| Descripciones por room (392) extraídas del módulo (V6k8) | ✅ |
| Q/D crypts: todas las instancias (multi-area) | ✅ |
| Anchor-based clustering (rooms 1-13 pegados, V6k9) | ✅ |
| **Session sync DM + Players (V6k10)** | ✅ |
| iPad PWA fullscreen (V6k5) | ✅ |
| Toggle markers (V6k5) | ✅ |
| Tracker tiempo + raciones + rest | ✅ |
| Wandering checks auto + antorcha | ✅ (en dispositivo que mueve) |
| Trampas DM-strict | ✅ |
| Saves auto ACKS + Mortal Wounds | ✅ |
| Bestiario 120 criaturas | ✅ |
| Illustrations 27 | ✅ |

— Cockpit Valakhan v6k10.9 · Session Sync funcional · 2026-05-02
