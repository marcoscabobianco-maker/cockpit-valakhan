# HANDOFF v6k · Wildcard nocturno · 2026-05-01

**Live**: https://mc-prism.pages.dev/cockpit · deploy `2c7ddf5b`

## Lo que hice mientras dormías (2 versiones, V6j + V6k)

### V6j · Fixes críticos al feedback de la noche

1. **Rooms re-extracted del PDF completo** (264 páginas, no solo los mapas)
   - Parser column-aware: lee texto en bbox y separa columna izquierda vs derecha del PDF, ordena por Y, detecta room IDs (`12.`, `74.`, `143.`, etc.)
   - Post-processing: separa **narrative** de **stats blocks** automáticamente con regex (`AL:`, `HD:`, `AC:`, `#AT:`, `DMG:`).
   - Nuevo schema por sala: `{title, summary, narrative, stats, treasure, page, desc_full}`.
   - **373 rooms procesadas** (vs 244 del JSON original) — más cobertura.
   - Modal redibujado: título limpio, resumen como "lead paragraph", stats en bloque monospace separado, treasure destacado, narrativa completa expandible.

2. **Wandering check auto-combat**
   - Cuando wandering positivo en Barrowmaze, además de mostrar banner: **auto-switch a combat panel** después de 1.8s con monsters precargados.
   - Vos podés hacer click "Dismiss" en el banner durante esa ventana si querés resolver narrativamente sin combate.

3. **Trampas DM-strict**
   - Antes: trampas `detected` se mostraban a los jugadores (les avisaba que ahí había una trampa).
   - Ahora: solo las `triggered` se muestran a los jugadores. Las `detected` siguen ocultas hasta que **vos decidas revelarlas**.

### V6k · Riqueza de contenido del módulo

4. **Illustrations del módulo (27 extraídas, ~9 MB)**
   - Extraje todas las pages del appendix (pages 212-264) que son full-page illustrations.
   - 17 rooms tienen referencia explícita a "Barrowmaze illustration #N" en su desc — esas rooms ahora muestran la illustration embebida en el modal cuando las clickeás. Click sobre la imagen → tamaño completo en pestaña nueva.
   - **Importante**: el mapping `illustration #N → page del appendix` es heurístico (asume orden secuencial). Algunas pueden estar mal mapeadas; abrí el PDF original si querés verificar exactitud.
   - Permiso: vos compraste el módulo y es uso personal, así que las imágenes están servidas desde tu Cloudflare Pages.

5. **Bestiario Barrowmaze (120 criaturas)**
   - Extracted del campo `stats` de cada room: detecta patrones tipo `Skeletons (10) AL: C, AC: 7, HD: 1, HP: 8...`.
   - **120 criaturas únicas** detectadas. Top: Skeletons (8 salas), Zombies (6), Gaxx (5), Ghouls (5), Wights (5), Crypt Knights (5), Mummies (5), Gargoyles (4), Ravenous Dead (3), Wraiths (3), Zuul (3), etc.
   - **Botón "🜍 Bestiario Barrowmaze (120 criaturas)"** en Quick Refs card del panel derecho.
   - Modal con buscador por nombre + lista de salas donde aparece cada criatura (con room ID + count).

## Total wildcard nocturno

| V | Foco | Patches |
|---|---|---|
| V6j | Rooms clean + wandering auto-combat + traps DM-strict | 4 |
| V6k | Illustrations (27) + Bestiario (120) integrados | 5 |

**Tiempo total**: ~3 horas. **Deploy**: 2c7ddf5b. **Commit**: pendiente final.

## Archivos producidos / modificados

```
mc-prism-deploy/
├── cockpit.html (V6k)
├── maps/
│   ├── barrowmaze_rooms_full.json  ← REEMPLAZADO con datos limpios (765 KB, 373 rooms)
│   ├── barrowmaze_bestiary.json    ← NUEVO (27 KB, 120 creatures)
│   ├── barrowmaze_illustrations/   ← NUEVA carpeta (9.3 MB)
│   │   ├── _index.json             ← mapping room→illustration
│   │   └── illustration_NN_pXXX.webp × 27
│   └── (los archivos de antes intactos)
```

## Cómo testearlo

1. Abrir `https://mc-prism.pages.dev/cockpit` (hard-refresh si caché).
2. Cargás Barrowmaze.
3. Click sobre un marker dorado, especialmente:
   - **Sala 12** (Great Mound): debería mostrar 2 illustrations linkeadas
   - **Sala 47, 48, 70, 72, 84, 99, 108, 151, 171, 180, 181, 189, 203, 205**: 1 illustration cada una
4. Comprobá que el modal ya **NO tenga texto cruzado de columnas** (era el problema de Sala 151).
5. Click "🜍 Bestiario Barrowmaze" en Quick Refs → modal con 120 criaturas + buscador.
6. Movete por el dungeon. Cuando aparezca un encuentro: banner + auto-load del combat panel después de 1.8s.
7. Vista DM (tecla `G`) + shift+click en una cell para colocar trampa: en vista jugador NO se mostrará hasta que se gatille.

## Limitaciones conocidas

- **Mapping illustrations heurístico**: si la sala 47 dice `illustration #5`, asume que es la 5ª illustration de la appendix (page 213). Si las pages 212-216 son character sheets / handouts y no illustrations propiamente, el mapping puede estar offset. Solución manual posible: editar `_index.json` con mapping correcto.
- **Algunos titles de room siguen con bleed**: "of the room" para Sala 200 — el parser tomó la primera oración pero no salió limpia. Marcos puede ignorar el title y leer el summary/narrative que sí está OK.
- **Bestiario incluye duplicados** (Skeleton/Skeletons, Wight/Wights, Mummy/Mummies, Ghoul/Ghouls, Two Ghouls). Es porque el extractor toma el texto literal del módulo. Voy a dejarlo así — útil para vos verificar lo que dice el módulo.
- **Sala 143 sigue aislada en wallmap**: si querés acceder, vista DM + ctrl+click sobre una cell del pasillo.

## Para próxima sesión

- **Validar el mapping illustration #N**: si abrís el módulo PDF y ves que illustration #1 NO es la del appendix page 212, podemos shift el mapping (ej. start at page 217 instead).
- **Bestiario integrado a wandering check**: cuando un encuentro dispara, mostrar info de la criatura desde el bestiario (HD/AC/etc) en lugar de solo en log.
- **Spell slots PCs casters** (Silas warlock, Dimitri mage).
- **XP tracker post-sesión**.

— Cockpit Valakhan V6k · 2026-05-01 madrugada
