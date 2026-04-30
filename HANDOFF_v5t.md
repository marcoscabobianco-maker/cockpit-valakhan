# Handoff v5t → próxima sesión

**Fecha**: 2026-04-30
**Estado**: v5t LIVE en https://mc-prism.pages.dev/cockpit.html
**Repo**: https://github.com/marcoscabobianco-maker/cockpit-valakhan (commit aec2004)
**Marcos**: 11 PCs en Sala 74A de Barrowmaze, sesión 6 jugada por Ale Humérez (sustituto), Marcos vuelve a tomar el mando.

## Para la próxima sesión de Claude Code: prompt de arranque

```
Continuá cockpit-valakhan. Lee:
- https://raw.githubusercontent.com/marcoscabobianco-maker/cockpit-valakhan/main/README.md
- https://raw.githubusercontent.com/marcoscabobianco-maker/cockpit-valakhan/main/CHANGELOG.md
- https://raw.githubusercontent.com/marcoscabobianco-maker/cockpit-valakhan/main/HANDOFF_v5t.md

Working dir local: C:/Users/Usuario/Desktop/Cemanahuac/
Deploy: cd C:/Users/Usuario/COWORK/ATEM/mc-prism-deploy && npx wrangler pages deploy . --project-name=mc-prism

Wrangler ya está logueado. GitHub gh CLI ya está logueado como marcoscabobianco-maker.
```

## Contexto rápido (lo crítico)

### Mesa activa: Novatos ONG Cannabis
- 11 PCs (ver `campaigns/novatos_ravenloft.json`)
- ACKS Imperial Imprint
- Setting: **Valakhan** (Ravenloft 2e adaptado por Marcos)
- 6 sesiones jugadas: S1-S3 Marcos (Sunless Citadel), S4-S6 Ale Humérez sustituto (Barrowmaze m236→m234→Sala 74A)
- **Silas (warlock) tiene 2 deseos pendientes** del Deck of Many Things (sacó La Luna en S6, gastó 1)
- **Hector Risco** desaparecido en pozo de Bellaca (S2)
- 6º día calendario: día 35

### Stack
- HTML único `prototipo_v5t.html` (430 KB) con todo inline (campaigns, ACKS data, worldbook)
- Despliegue: Cloudflare Pages → `mc-prism.pages.dev/cockpit.html`
- Para tools pesados: ACKS Assistant (Vite/React) en `mc-prism.pages.dev/tools/`
- Persistencia: localStorage por campaña

### Patrón de iteración
1. Backup: `cp prototipo_v5t.html prototipo_v5t_pre_X.html`
2. Crear `_apply_faseX.py` con re.sub patches al HTML
3. Run: `PYTHONIOENCODING=utf-8 python _apply_faseX.py`
4. Validar: `node --check _check_*.js`
5. Deploy: `cp prototipo_v5u.html mc-prism-deploy/cockpit.html && npx wrangler pages deploy ...`
6. Commit + push: `git add ... && git commit -m "..." && git push`

## Cosas pedidas por Marcos pendientes (orden de prioridad)

### 🔴 Alta prioridad
1. **Marcadores de PC individuales sobre el mapa Cía Zafiro** (no solo el "C" del party global). Cada PC con un dot+nombre que el GM puede mover separadamente. Pedido explícito en sesión 2026-04-30.
2. **Nombre del Patriarca/Abad** introducido por Marcos en S3 mid-session que guió al party hacia Barrowmaze. Pendiente confirmar nombre — dejar como "patriarca_abad" placeholder en NPCs.

### 🟡 Media prioridad
3. **Atlas mapas Barrowmaze** del PDF cuando se muevan más allá de la zona Cía Zafiro (extraer páginas 230+ del PDF como imágenes y agregarlas al MAPS_INDEX).
4. **Calendar enriquecido con festividades** de Aurëpos / Ravenloft (ej. Sabbath de la luna llena).
5. **Inventario simple por PC** (lista de items, gold).

### 🟢 Baja prioridad / nice-to-have
6. **Path planeado vs path histórico** (preview del camino antes de mover, estilo Crusader Kings 3).
7. **NPC quick-generator** integrado (más simple que ir a /tools/).
8. **Multi-sesión turn tracker** en dungeon (qué pasó turno por turno).

## Cosas que NO hay que hacer (Marcos lo dijo explícitamente)

- ❌ Long/short rest (ACKS NO usa eso, es 5e)
- ❌ Reimplementar Spells/Bestiary/MagicItems en el cockpit (ya están en `/tools/` Assistant)
- ❌ Vectorizar pasillos del Barrowmaze (Marcos prefiere paint-with-finger sobre la imagen)
- ❌ Long/short rest (lo repito porque es importante: ACKS NO tiene)

## Decisiones arquitectónicas tomadas

1. **Stack híbrido**: cockpit standalone (mapa/sesión/PCs) + ACKS Assistant separado (spells/bestiary). NO mergear.
2. **iPad-first**: botones grandes (44x44 mín), touch targets, single-file 100% offline-capable.
3. **GM/Player toggle global**: Player mode oculta info GM, dungeon canvas no editable.
4. **Multi-campaña**: 4 JSONs en `campaigns/`. Default: novatos_ravenloft.
5. **Worldbook compartido**: `farolclub_aurepos.json` (Kanka export, 121 NPCs/62 lugares/9 facciones). Aplica a múltiples campañas del mismo continente Aurëpos.

## Archivos clave (para que la próxima sesión sepa dónde mirar)

| Path | Qué es |
|---|---|
| `prototipo_v5t.html` | Cockpit actual LIVE (430 KB) |
| `campaigns/novatos_ravenloft.json` | Mesa activa (132 hexes, 26 NPCs, 6 sessions, 11 PCs) |
| `worldbooks/farolclub_aurepos.json` | Worldbook Kanka (121 NPCs, 62 lugares) |
| `rulebooks/acks_core.json` | ACKS RAW completo (102 KB) |
| `acks_data_clean.json` | Bestiario limpio (370 monstruos, embebido en cockpit) |
| `acks_rulebook_slim.json` | Subset settlements + mercantile |
| `settlement_panel.js/.css` | Panel Market Class (inlined en cockpit) |
| `cockpit-imgs/` | 9 mapas (Cía Zafiro, Wensley, Aurëpos, etc.) |
| `CHANGELOG.md` | Historia v5 → v5t completa |

## Bug conocidos / cosas que verificar próxima sesión

1. Chrome MCP de Claude bloquea localhost por permisos (necesita aprobación manual). Usar Bash `start ""` para abrir browser default.
2. El HTML monolítico está cerca de su límite manejable (~430 KB). Si crece más, considerar mover algo a fetch lazy.
3. Settlement panel muestra "⚠ sin market class" en hexes con `isCity: true` pero sin `marketClass`. Resuelto para Gosterwick (V) y Castleton (IV).

## Status del context window al cerrar

- ~85-90% del límite de 1M tokens en esta sesión
- Marcos ya tiene wrangler logueado, gh CLI logueado, deploy funcionando
- Nada que rehacer manualmente — todo continuable

---

**Buena cacería al próximo Claude que lea esto.** El proyecto está en un estado **muy operacional**: 6 fases (A-H) deployed, 17+ commits en GitHub, 18 archivos JSON estructurados, 1 cockpit funcional, 1 ACKS Assistant secundario.

Marcos espera continuar con **marcadores PC individuales** como prioridad 1.
