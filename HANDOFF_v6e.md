# HANDOFF v6e — Cockpit Valakhan Wildcard Mode Complete

**Fecha**: 2026-04-30
**Versión live**: V6e
**URL**: https://mc-prism.pages.dev/cockpit
**Repo**: https://github.com/marcoscabobianco-maker/cockpit-valakhan
**Cloudflare last deploy**: `36145f45`

---

## Estado actual: tracker ACKS completo sobre mapa Barrowmaze vectorizado

El cockpit V6e es un tracker de sesión ACKS Imperial Imprint funcional sobre el mapa real del Barrowmaze (módulo Greg Gillespie 4ed Complete) con walls vectorizadas automáticamente desde el PDF.

### Pipeline de la sesión típica de mesa

1. Abrir `https://mc-prism.pages.dev/cockpit` (iPad o desktop).
2. Cargar dungeon Barrowmaze → auto-switchea a modo **Real**.
3. Party arranca en **Sala 74A** (cell 32, 84).
4. Mover con flechitas/WASD: cada paso suma a contador, cruza turn boundary auto.
5. **Hora del día** visible (default 09:00, periodos color-codados).
6. **Tracker visual** con progress bars: antorcha, wandering, rest, raciones.
7. **Roster 11 PCs** con HP/AC/posición/lightBearer.
8. **Click rooms** → modal con desc + treasure del módulo.
9. **DM mode** (tecla G o botón) revela todo.
10. **Shift+click** en DM → coloca trampa.
11. **Wandering trigger** auto cada 2 turnos → banner con monster + botón Combate.
12. **Descanso nocturno** (8h, +1d3 HP, −raciones) cuando es de noche.

### Datos vectorizados desde el PDF

- `maps/barrowmaze_real.webp` (557 KB, 2628×2444): mapa stitched 3×2 limpio.
- `maps/wallmap_barrowmaze.json` (87 KB): 203×219 cells = 44,457 cells, 41% walkable. Sample-based del PDF rendereado.
- `maps/barrowmaze_room_coords.json` (22 KB): 375 rooms con x/y SVG 800×744.
- `maps/barrowmaze_rooms_full.json` (152 KB): 244 rooms keyed con desc/treasure/HD.

### Subsistemas ACKS implementados (Capas A-D)

| Capa | Subsistema | Estado |
|---|---|---|
| A | Mapa Barrowmaze real con walls vectorizadas | ✅ V5x |
| A | LoS Bresenham con bloqueo por walls | ✅ V5v + V5x |
| A | Vista DM toggle prominente + atajo G | ✅ V5y |
| A | Performance optimizada (canvas redraw vs HTML rebuild) | ✅ V5y |
| A | Hora del día + descanso nocturno + raciones | ✅ V5z |
| A | Tracker visual con progress bars | ✅ V5z |
| B | Tabla wandering específica Barrowmaze (1d20) | ✅ V6a |
| B | Banner encuentro estructurado + surprise + distance | ✅ V6a |
| B | Botón → Combate precarga foes | ✅ V6a |
| C | Trampas place + detect + trigger | ✅ V6d |
| D | PC roster con HP/AC/clase/level desde novatos_ravenloft | ✅ V6b |
| D | Formación: vanguardia/medio/retaguardia | ✅ V6b |
| D | Light bearer (toggle 🔥) | ✅ V6b |
| D | Click rooms keyed con desc/treasure | ✅ V6c |

### Subsistemas pendientes (Capas E-F)

- **Saving throws automatizados** por PC con valores reales (P/P, B, P/D, R/R/W, S/S/S).
- **Spell slots** para PCs casters (Silas warlock, Dimitri mage).
- **Hirelings/henchmen** loyalty + morale.
- **XP earned** por sesión (combat HD + treasure 1gp=1xp).
- **Mortal Wounds table** inline (hoy: link al ACKS Assistant).
- **Reaction roll** automatizado (Marcos prefiere mesa por ahora).

---

## Repos y archivos

### Cockpit (HTML único)

- Working dir: `C:\Users\Usuario\Desktop\Cemanahuac\`
- Archivos:
  - `prototipo_v5u.html` — base previa a wildcard
  - `prototipo_v5v.html`, `prototipo_v5w.html`, `prototipo_v5x.html`, `prototipo_v5y.html`, `prototipo_v5z.html`
  - `prototipo_v6a.html`, `prototipo_v6b.html`, `prototipo_v6c.html`, `prototipo_v6d.html`, `prototipo_v6e.html` ← LIVE
  - `_apply_v5*.py`, `_apply_v6*.py` — patches reproducibles
  - `maps/barrowmaze_bg_1280.webp`, `maps/barrowmaze_bg_1920.webp`, `maps/barrowmaze_room_coords.json`
  - `campaigns/_barrowmaze_rooms_full.json`, `campaigns/novatos_ravenloft.json`

### Deploy folder (Cloudflare Pages)

- Working dir: `C:\Users\Usuario\COWORK\ATEM\mc-prism-deploy\`
- Archivos críticos:
  - `cockpit.html` ← V6e
  - `maps/barrowmaze_real.webp`, `maps/wallmap_barrowmaze.json`
  - `maps/barrowmaze_room_coords.json`, `maps/barrowmaze_rooms_full.json`
  - `tools/` — ACKS Assistant Vite/React separado
  - `index.html` — ATEM Session Editor (CDI S01)

### Sandbox (mc-prism Next.js, no en repo cockpit)

- `C:\Users\Usuario\CODE\mc-prism\sandbox\barrowmaze-assembly\` — pipeline stitching
- `C:\Users\Usuario\CODE\mc-prism\sandbox\walls-extraction\` — pipeline vectorización walls

---

## Atajos de teclado V6e

| Tecla | Acción |
|---|---|
| `WASD` / Flechas | Mover party 1 cell |
| `G` | Toggle Vista DM ↔ Vista jugadores |
| `T` | +1 turno (actividad libre) |
| `shift+click` cell | Colocar trampa (solo en modo DM) |
| Click marker dorado | Modal con info de la sala |

---

## Próximos pasos sugeridos

1. **Más tablas wandering del Barrowmaze**: actualmente hay una sola tabla genérica para Levels 1-3. Extraer del módulo las tablas específicas por área (Antechamber, Mounds, niveles 2-3).
2. **Mortal wounds inline** desde el ACKS Assistant (es uno de los componentes más usados; integrarlo evita el round-trip a /tools/).
3. **Saves automatizados**: cada PC tiene saves por clase. Cuando una trampa o spell pide save, tirar 1d20 ≥ target del PC afectado.
4. **Spell slots tracking** para Silas (warlock) y Dimitri (mage).
5. **XP tracker** post-sesión con import del bestiary y treasure capturados.
6. **Notas de sesión** linkeadas al log de eventos (export markdown ya existe en ACKS).

---

## Bugs/limitaciones conocidos

- **Cells de pasillos delgados** pueden quedar mal clasificadas (1 px de error en sampling). Solución futura: padding 3×3 sample.
- **Wandering check tabla Barrowmaze** es genérica (1d20 con 8 entries). El módulo tiene tablas por nivel/área.
- **Mortal wound al llegar a 0 HP** solo loguea aviso; no tira en la tabla. Hay que ir al ACKS Assistant manualmente.
- **Reaction roll y surprise** no automatizan combat: solo informan. Marcos prefiere tirar en mesa.
- **PC roster** no tiene saves ni spell slots todavía (Capa E pendiente).

---

## Cambios totales en wildcard mode (V5z → V6e)

| Versión | Patches | Tamaño HTML | Foco |
|---|---|---|---|
| V5z | 7 | 487 KB | Tiempo + raciones + descanso nocturno |
| V6a | 4 | 494 KB | Encuentro pipeline + tabla |
| V6b | 3 | 502 KB | PC roster + formación |
| V6c | 5 | 508 KB | Click rooms keyed |
| V6d | 8 | 517 KB | Trampas |
| V6e | 2 | 520 KB | Quick refs + ACKS link |

**Total wildcard**: 29 patches, +33 KB HTML, 5 deploys (v5z, v6c intermedio, v6e final).

---

— Cockpit Valakhan V6e · 2026-04-30
