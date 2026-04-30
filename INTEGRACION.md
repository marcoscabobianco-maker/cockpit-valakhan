# INTEGRACIÓN — fixes Fase A para `prototipo_v5n.html`

Marcos: te dejo los cinco archivos para aplicar la limpieza del bestiario y el panel de Market Class. Está pensado como **patch mínimo no-invasivo** — el cockpit sigue siendo un single-file HTML, todo lo nuevo se monta desde dos imports y un cambio puntual en `renderHexInfo()`.

---

## Archivos entregados

| Archivo | Qué es | Dónde va |
|---|---|---|
| `acks_data_clean.json` | Bestiario limpio (49 monstruos con OCR corregido + 54 alias marcados) | Reemplaza el bloque inline `<script id="acks-data">` |
| `settlement_panel.js` | Módulo del panel | Junto al HTML (mismo dir) |
| `settlement_panel.css` | Estilos del panel | Junto al HTML |
| `acks_rulebook_slim.json` | Subset de `rulebooks/acks_core.json` para embeber | Embebido inline como `<script id="acks-rulebook">` |
| `cleanup_report.txt` | Reporte detallado de cambios al bestiario | Para tu archivo de control de cambios |

---

## Paso 1 — Backup

```bash
cd ~/Desktop/Cemanahuac   # o donde tengas el repo local
cp prototipo_v5n.html prototipo_v5n_pre_fasea.html
```

Si algo sale mal, copia ese archivo encima del activo y volvés al estado previo.

---

## Paso 2 — Reemplazar bestiario contaminado

En `prototipo_v5n.html`, buscá esta línea (alrededor de la 676):

```html
<script id="acks-data" type="application/json">{"monsters":{"Giant Ant Queen":{...
```

**Reemplazá todo el contenido entre `<script id="acks-data" type="application/json">` y `</script>`** por el contenido de `acks_data_clean.json`.

**Verificación**: después de reemplazar, abrí el HTML y abrí la consola del navegador (F12). Pegá:

```js
const d = JSON.parse(document.getElementById('acks-data').textContent);
const total = Object.keys(d.monsters).length;
const aliases = Object.values(d.monsters).filter(m => m._alias_of).length;
const dirty = Object.entries(d.monsters).filter(([n,m]) => 
  Object.values(m).some(v => typeof v === 'string' && /Attacks:|Damage:|Speed \(land\):/.test(v))
);
console.log({ total, aliases, dirty: dirty.length });
```

Esperás `{ total: 370, aliases: 54, dirty: 0 }`.

---

## Paso 3 — Sumar el panel de Market Class

### 3a. Copiar archivos al lado del HTML

```
prototipo_v5n.html
settlement_panel.js     ← nuevo
settlement_panel.css    ← nuevo
```

### 3b. Embeber el rulebook slim

En el HTML, **inmediatamente después** del bloque `<script id="worldbook-data" type="application/json">...</script>` (alrededor de la línea 677), agregá:

```html
<script id="acks-rulebook" type="application/json">{CONTENIDO DE acks_rulebook_slim.json}</script>
```

(pegás todo el JSON en una sola línea)

### 3c. Cargar el JS y el CSS

En el `<head>` del HTML (cerca del final del head, antes de `</head>`), agregá:

```html
<link rel="stylesheet" href="settlement_panel.css">
<script src="settlement_panel.js" defer></script>
```

### 3d. Parchar `renderHexInfo()`

Buscá la función `function renderHexInfo()` (alrededor de la línea 927).

**Encontrá esta línea**:

```js
if (h.isDungeon) {
```

**Inmediatamente ANTES de esa línea**, insertá:

```js
  // ─── Settlement Panel (Fase A — market class) ──────────────────────
  if (h.isCity && window.renderSettlementPanel) {
    if (!window.ACKS_RULEBOOK) {
      try {
        window.ACKS_RULEBOOK = JSON.parse(document.getElementById('acks-rulebook').textContent);
      } catch (e) { console.warn('No se pudo cargar acks-rulebook:', e); }
    }
    html += window.renderSettlementPanel(h, state, window.ACKS_RULEBOOK || {});
  }
```

Eso es todo el cambio en HTML/JS. El resto del cockpit sigue funcionando igual.

---

## Paso 4 — Probar

Abrí el HTML doble-click. En la campaña activa Valakhan:

1. Click en hex **Helix** (5,2). Tendrías que ver el panel completo: Class V, ~600 hab, magia hasta nivel 2, hirelings 1d6/sem, mercado con 250 gp loanable funds, dropdown con todos los settlements destino.
2. Click en **🎲 Tirar hirelings**. Aparece un número.
3. Elegí **Glastonville** en el dropdown de mercantile, click en **🎲 Tirar venture**. Aparece resultado 2d6 + mods + verdict (Outraged / Reluctant / Standard / Eager / Frenzy) con multiplicador.
4. Click en hex **Caladán's** (3,9). El panel debería mostrar la marca **⚔ Hostil**.
5. Click en hex **Stejara** (7,6). Panel completo. Verificá que el dropdown de destino NO incluye Stejara (origen) pero sí Helix, Old Adwenn, Caladán's, etc.

### Si aparece el panel "⚠ sin market class"

Eso es porque ese settlement (en el JSON de la campaña) tiene `isCity: true` pero no tiene `marketClass`. En tu data está pasando con **Gosterwick** y **Castleton**. Si querés que aparezcan datos derivados, agregales `marketClass` en `campaigns/novatos_ravenloft.json`. Sugerencia razonable según tamaño relativo:

- Gosterwick → V (es vecino de Helix, similar)
- Castleton → IV (es asiento de un castillo grande)

---

## Paso 5 — Diff resumido

Lo que cambia en `prototipo_v5n.html`:

| Cambio | Líneas afectadas |
|---|---|
| Reemplazar bloque `acks-data` | ~676 |
| Insertar `acks-rulebook` slim | después de ~677 |
| Insertar `<link>` y `<script>` en head | head antes de `</head>` |
| Parchar `renderHexInfo()` | dentro de la función, antes de `if (h.isDungeon)` |

Ningún cambio toca: combat tracker, dungeon mode, fog of war, calendario, sesiones, encounter rolls, treasure parser. Si algo de eso se rompe, no fue por este patch.

---

## Notas críticas

- **El rulebook slim solo trae `settlements` y `mercantile`**. Si en algún momento querés que el panel también consulte `wilderness` o `weather` del rulebook completo, podés cambiar la slim por el rulebook entero (98 KB) o cargarlo por fetch. Hoy no hace falta.
- **Las distancias se calculan en hexes**, no en millas. Tu campaña usa hex = 3 mi, así que multiplicar por 3 da millas reales si necesitás. La estimación de "días de viaje" usa heurística aproximada (1 día ≈ 8 hex de 3mi a pace normal); ajustala si te queda baja.
- **Los modificadores de mercantile son los del rulebook ACKS RB Ch.8 supply_demand_mechanic**. Los modificadores adicionales por "shortage de vecinos" y "surplus de vecinos" del rulebook NO están implementados todavía — requieren tracking de qué tiene shortage cada hex, y eso es Fase B.
- **El log de eventos**: si tu cockpit tiene una función global `logEvent(string)`, el panel la va a llamar al tirar hirelings o ventures. Si no existe, no falla — simplemente no loggea.

---

## Si querés revertir

Cualquiera de los tres cambios es independiente:

- **Bestiario sucio de nuevo**: pegá el bloque `acks-data` desde tu backup `prototipo_v5n_pre_fasea.html`.
- **Sin panel**: borrá el `<link>` y `<script>` del head, y el bloque insertado en `renderHexInfo()`. El cockpit vuelve al estado previo sin reiniciar nada.
- **Sin rulebook embebido**: borrá el `<script id="acks-rulebook">`. El panel mostrará "⚠ sin market class" pero no rompe el cockpit.

---

Cuando lo apliques avisame qué settlements le falta `marketClass`, y si tirás un par de mercantile ventures de prueba mandame el resultado para ver si los modificadores te cierran. La regla 2d6 de ACKS es austera; si te parece que da resultados raros respecto a lo que vos esperás, probablemente haya que sumar los modificadores de neighbors-with-shortage que dejé pendientes.
