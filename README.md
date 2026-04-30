# Cockpit V5 · Valakhan · ACKS

> Cockpit modular para correr campañas de rol multi-sistema (ACKS · Level Up A5e · CLAN), con worldbook compartido (FarolClub Aurëpos), hex map overland canónico de Valakhan de la Bruma, dungeon image fog-of-war paint-with-finger, y herramientas integradas.

**Mesa activa**: Novatos ONG Cannabis (Marcos, Bs As). 11 PCs. 6 sesiones jugadas. ACKS Imperial Imprint. Setting: Ravenloft 2e adaptado a Valakhan. Position: Sala 74A de Barrowmaze.

## Apps deployadas

- **Cockpit**: https://mc-prism.pages.dev/cockpit.html
- **ACKS Assistant** (Vite/React separado): https://mc-prism.pages.dev/tools/
- **Source code index**: https://mc-prism.pages.dev/src/

## Estructura

```
.
├── prototipo_v5n.html           # Cockpit funcional, single-file iPad-ready (300 KB)
├── prototipo_v5j.html           # Versión anterior (sin fog of war)
├── README.md                    # Este archivo
├── 00_HANDOFF.md                # Estado del proyecto al despertar
├── 01_FORMATOS_PARALELOS.md     # Comparativa con Foundry/Owlbear/A5e/etc.
├── 02_ARQUITECTURA_V5.md        # 3 escalas anidadas, DB vs vista de mesa
├── 03_PROTOTIPO_HTML.md         # Manual de uso del prototipo V5
├── 04_OWLBEAR_DEEP_DIVE.md      # Decisión arquitectónica: stack híbrido
├── 05_LEVEL_UP_A5E.md           # Mapping A5e exploration al cockpit
├── 06_RULESET_ABSTRACTION.md    # Modelo multi-sistema (A5e + ACKS + CLAN)
├── CHECK_LIST_REVISIONES.md     # Decisiones tomadas con checkboxes
├── EXPLICACION_PARA_VOZ.md      # Versión narrativa para lectura en voz alta
├── campaigns/
│   ├── novatos_ravenloft.json   # ★ Campaña activa Valakhan (132 hexes, 26 NPCs, 6 sesiones)
│   ├── cemanahuac.json          # CLAN mesoamericano
│   ├── buenos_aires.json        # Level Up A5e template
│   └── sakkara_acks.json        # ACKS Sinister Stone placeholder
├── rulebooks/
│   └── acks_core.json           # ACKS RAW: movement, light, wilderness, weather, dungeon, market class, mercantile (102 KB)
├── worldbooks/
│   └── farolclub_aurepos.json   # Kanka FarolClub: 121 NPCs, 62 lugares, 9 facciones, 11 sesiones (73 KB)
└── reglas/                      # Abstracción multi-sistema
    ├── turn_loop.json
    ├── encounter_check.json
    ├── weather.json
    ├── dungeon_turn.json
    └── wandering_monster.json
```

## Stack

- HTML autocontenido + JSON inline + JS vanilla (cockpit)
- React + TypeScript + Vite (tools/)
- Cloudflare Pages (deploy)
- LocalStorage (persistencia por campaña)
- Canvas API (fog of war paint-with-finger)
- SVG (hex map overland)

## Setting

**Valakhan de la Bruma**: dominio Ravenloft 2e adaptado por Marcos. Domain del Darklord Caladán (PJ-vampiro de otra mesa, ahora fusionado con el Señor Pantera anterior). Brumas cierran las fronteras.

**Locations canónicas** (mapa físico, escala 1 hex = 3 millas):
- **Stejara** — base del party (centro-este)
- **Ciudadela Sin Sol** — Bellaca + Árbol Gulthias en pozo (centro)
- **Helix** — pueblo entrada Barrowmaze (norte-centro)
- **Long Falls / Arden Vul** — Ardis Vala adaptado (extremo norte)
- **Mota de Ironguard / Castillo Ironguard** — sureste
- **Caladán's + Castleton** — asiento del Darklord (suroeste)
- **Ritornelo** — pueblo de origen del Barón Argus + Lali=Bellaca

## Sesiones jugadas

- **S1-S3 (Marcos GM)**: Ciudadela Sin Sol → patriarca/abad introducido en S3 mid → guía hacia Barrowmaze
- **S4-S6 (Ale Humérez sustituto, Marcos en México)**: Camino a Helix → Barrowmaze mapas 236→234→Sala 74A. Mongrels intercambio. **Silas Disfigured (2 power checks fallados) leyó tableta → Deck of Many Things → La Luna → 3 deseos. Gastó 1 salvando al grupo. Quedan 2 deseos.** Nadie murió.

## Lore central

- **Bellaca** (= Lali, prometida del Barón Argus, raptada por Señor Pantera anterior) → leucrotta + Árbol Gulthias en pozo de Sunless Citadel. Promete "tesoros detrás de la cascada" (= Ardis Vala / Arden Vul). Vulnerable a llamarla "Lali".
- **Caladán** = Darklord actual, vampiro nosferatu fusionado con el Señor Pantera. Otra mesa.
- **Tablet of Chaos** = en Barrowmaze, custodiada por Keeper of the Tablet, vigilada por Ossithrax Pejorative (Beholder). Cult of Orcus + Cult of Set la buscan.
- **Sinkhole of Evil** = Barrowmaze (+1 HD undead, divine turn -2 penalty)

## Estado al deploy

- **v5t LIVE** con todas las fases A-H. Ver `CHANGELOG.md` para historial detallado.

### Modos disponibles
- 🗺 **Mapa**: hex grid Valakhan (132 hexes, 1 hex = 3 millas), drag-tap para mover, path histórico con marcadores de día (`d35`, `d36`...), río continuo, river overlay, auto-encounter al avanzar watch.
- 🜍 **Dungeon**: room graph + imagen real Cía Zafiro con fog-of-war paint-with-finger (canvas overlay, dedo borra niebla).
- ⚔ **Combate**: tracker con HP/AC/iniciativa, multi-monster from encounter, cargar PCs/foes, mortal wounds calculator (ACKS RAW Combat IV).
- 🎲 **Encuentro**: ACKS RAW por terrain + tabla local + roll distance/surprise/reaction + → Combat directo.
- 👥 **PCs**: 11 PCs con HP overrides, conditions toggleables, level-up, + cargar todos al combate.
- 📚 **Data**: NPCs Aurëpos / Lugares / Facciones / Sesiones / Quests / Combat Ref / 9 Mapas. Click → modal detalle full.
- 📜 **Sesión**: lista sesiones + log live + notas por hex + Notes index global + 3 botones export Markdown.

### Topbar
- Selector campaña (4 opciones) + tag de sistema
- Calendario: día / watch / **luna** (8 fases, click → modal con efectos Ravenloft)
- Botón ▶ Avanzar watch (con auto-encounter check + full-moon warnings)
- Botón **🜂 GM / 👁 Player** (toggle vista)
- Botón **🎲 Auto** (toggle auto-encounter)
- Botón **🛠 Tools ACKS** → abre `/tools/` en pestaña nueva (Vite/React: spells, bestiary, mortal wounds, weather, hireling, treasure, etc.)

### Settlement Panel (en hex panel cuando es ciudad)
- Class I-VI con población, magia max, hirelings/semana, stockpile gp
- 🎲 Tirar hirelings esta semana
- 🎲 Mercantile venture (2d6 supply&demand)
- 📰 Tirar rumor (12 default + 4 Helix-specific + 4 Stejara-specific)
- 🏛 Encuentro distrito (Avenue day/night, Slums, Market, Temple, Docks, Tavern)

## Licencia

Privado / personal / Marcos Cabobianco.

ACKS Imperial Imprint © Autarch LLC. Barrowmaze © Greg Gillespie. Halls of Arden Vul © Richard Barton.
