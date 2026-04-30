/* settlement_panel.js — Panel de Market Class para cockpit-valakhan
 *
 * Uso desde prototipo_v5n.html:
 *   1. Cargar este archivo y settlement_panel.css en <head>
 *   2. En renderHexInfo(), si h.isCity, llamar:
 *        html += renderSettlementPanel(h, state, ACKS_RULEBOOK);
 *      (donde ACKS_RULEBOOK = el JSON del rulebook acks_core.json,
 *       opcionalmente embebido o cargado por fetch)
 *   3. Las funciones rollHirelings/rollMercantile/showItemsForClass son globales
 *      y se invocan desde botones onclick.
 *
 * Dependencias: window.rollDice(spec), window.escapeHTML(s), window.state,
 *               window.HEX_INDEX, window.MARKET_CLASSES (el rulebook).
 *
 * Marcos Cabobianco / cockpit-valakhan / 2026-04-29
 */

(function () {
  'use strict';

  // ───────────────────────────────────────────────────────────────────────
  // Datos derivados de ACKS Core RB Ch.8 — Visiting Settlements
  // ───────────────────────────────────────────────────────────────────────
  // Estos valores complementan settlements.market_classes del rulebook.
  // Se mantienen acá porque son derivados (no directamente en el RB JSON).
  const MARKET_DERIVED = {
    I:   { magicMaxLevel: 6, hirelingsPerWeek: '1d6+30', specialistsAvail: 'all',
           magicItemTypes: ['scrolls','potions','wands','rings','rods','staffs','swords','armor','misc'],
           urbanEncounter: '1-in-6', stockpileGP: '1d6×100,000' },
    II:  { magicMaxLevel: 5, hirelingsPerWeek: '1d6+15', specialistsAvail: 'all',
           magicItemTypes: ['scrolls','potions','wands','rings','rods','swords','armor','misc'],
           urbanEncounter: '1-in-6', stockpileGP: '1d6×25,000' },
    III: { magicMaxLevel: 4, hirelingsPerWeek: '1d6+9', specialistsAvail: 'most',
           magicItemTypes: ['scrolls','potions','rings','swords','armor','misc'],
           urbanEncounter: '1-in-8', stockpileGP: '1d6×5,000' },
    IV:  { magicMaxLevel: 3, hirelingsPerWeek: '1d6+3', specialistsAvail: 'common only',
           magicItemTypes: ['scrolls','potions','swords','armor'],
           urbanEncounter: '1-in-10', stockpileGP: '1d6×1,250' },
    V:   { magicMaxLevel: 2, hirelingsPerWeek: '1d6', specialistsAvail: 'rare',
           magicItemTypes: ['scrolls','potions'],
           urbanEncounter: '1-in-12', stockpileGP: '1d6×250' },
    VI:  { magicMaxLevel: 1, hirelingsPerWeek: '1d3', specialistsAvail: 'almost none',
           magicItemTypes: ['scrolls'],
           urbanEncounter: '1-in-20', stockpileGP: '1d6×50' }
  };

  // Estimación de población urbana por market class (mid-range)
  const POP_ESTIMATE = {
    I: 100000, II: 30000, III: 8000, IV: 2500, V: 600, VI: 150
  };

  // ───────────────────────────────────────────────────────────────────────
  // Helpers
  // ───────────────────────────────────────────────────────────────────────
  function getMarketClass(hex) {
    return (hex && hex.marketClass) ? String(hex.marketClass).trim().toUpperCase() : null;
  }

  function getRulebookData(rulebook, marketClass) {
    if (!rulebook || !marketClass) return null;
    return (rulebook.settlements && rulebook.settlements.market_classes
            && rulebook.settlements.market_classes[marketClass]) || null;
  }

  function distanceHexes(a, b) {
    // Distancia hexagonal en offset coords (offset cube conversion)
    const ax = a.col, az = a.row - (a.col - (a.col & 1)) / 2, ay = -ax - az;
    const bx = b.col, bz = b.row - (b.col - (b.col & 1)) / 2, by = -bx - bz;
    return (Math.abs(ax - bx) + Math.abs(ay - by) + Math.abs(az - bz)) / 2;
  }

  function listSettlementsInWorld(world) {
    const hexes = (world && world.hexes) || [];
    return hexes.filter(h => h.isCity).map(h => ({
      name: h.name, col: h.col, row: h.row,
      marketClass: getMarketClass(h),
      hostile: !!h.hostile
    }));
  }

  // ───────────────────────────────────────────────────────────────────────
  // Render principal
  // ───────────────────────────────────────────────────────────────────────
  window.renderSettlementPanel = function (hex, state, rulebook) {
    if (!hex || !hex.isCity) return '';
    const mc = getMarketClass(hex);
    const rb = getRulebookData(rulebook, mc);
    const der = mc ? MARKET_DERIVED[mc] : null;

    if (!mc || !rb || !der) {
      return '<div class="settlement-panel">'
           + '<div class="sp-section sp-warn">⚠ Settlement sin market class definido. '
           + 'Asignar marketClass en el JSON de la campaña (I-VI) para ver datos derivados.</div>'
           + '</div>';
    }

    const popEst = POP_ESTIMATE[mc];
    const hexId = hex.col + ',' + hex.row;

    let html = '<div class="settlement-panel" data-hex="' + hexId + '">';

    // ── Header ──────────────────────────────────────────────────────────
    html += '<div class="sp-header">';
    html += '<div class="sp-title">🏛 ' + window.escapeHTML(rb.label || ('Class ' + mc)) + '</div>';
    html += '<div class="sp-subtitle">Población ~' + popEst.toLocaleString('es-AR')
         + ' · ' + (rb.families || '?') + ' familias</div>';
    if (hex.hostile) {
      html += '<div class="sp-hostile">⚔ Hostil al party</div>';
    }
    html += '</div>';

    // ── Servicios ───────────────────────────────────────────────────────
    html += '<div class="sp-section">';
    html += '<div class="sp-section-title">⚒ Servicios disponibles</div>';
    html += '<div class="sp-row"><span class="sp-key">Magia hasta:</span> <b>nivel ' + der.magicMaxLevel + '</b></div>';
    html += '<div class="sp-row"><span class="sp-key">Specialists:</span> ' + der.specialistsAvail + '</div>';
    html += '<div class="sp-row"><span class="sp-key">Items mágicos:</span> ';
    html += der.magicItemTypes.join(', ');
    html += '</div>';
    html += '<div class="sp-row sp-doc">' + window.escapeHTML(rb.services || '') + '</div>';
    html += '</div>';

    // ── Hirelings ───────────────────────────────────────────────────────
    html += '<div class="sp-section">';
    html += '<div class="sp-section-title">🤝 Hirelings disponibles</div>';
    html += '<div class="sp-row"><span class="sp-key">Por semana:</span> <b>' + der.hirelingsPerWeek + '</b></div>';
    html += '<button class="sp-btn" onclick="rollHirelingsForHex(\'' + hexId + '\')">🎲 Tirar hirelings disponibles esta semana</button>';
    html += '<div class="sp-result" id="sp-hirelings-' + hexId + '"></div>';
    html += '</div>';

    // ── Mercado ─────────────────────────────────────────────────────────
    html += '<div class="sp-section">';
    html += '<div class="sp-section-title">💰 Mercado y finanzas</div>';
    if (rb.loanable_funds_gp != null) {
      html += '<div class="sp-row"><span class="sp-key">Loanable funds:</span> ' + Number(rb.loanable_funds_gp).toLocaleString('es-AR') + ' gp</div>';
    }
    if (rb.investment_opportunities_gp != null) {
      html += '<div class="sp-row"><span class="sp-key">Investment opp.:</span> ' + Number(rb.investment_opportunities_gp).toLocaleString('es-AR') + ' gp</div>';
    }
    html += '<div class="sp-row"><span class="sp-key">Stockpile aprox:</span> ' + der.stockpileGP + ' gp</div>';

    // Mercantile cargo data
    const merc = rulebook.mercantile && rulebook.mercantile.baseline_cargo_by_class
                  && rulebook.mercantile.baseline_cargo_by_class[mc];
    if (merc) {
      html += '<div class="sp-row"><span class="sp-key">Cargo base:</span> ' + Number(merc.cargo_st).toLocaleString('es-AR') + ' st</div>';
      html += '<div class="sp-row"><span class="sp-key">Peaje:</span> ' + merc.toll_cp_per_st + ' cp/st · <span class="sp-key">tarifa:</span> ' + merc.tariff_pct + '%</div>';
    }
    html += '</div>';

    // ── Mercantile venture ──────────────────────────────────────────────
    const others = listSettlementsInWorld(state.world)
      .filter(s => !(s.col === hex.col && s.row === hex.row) && s.marketClass);

    if (others.length > 0) {
      html += '<div class="sp-section">';
      html += '<div class="sp-section-title">🐎 Mercantile venture</div>';
      html += '<div class="sp-row sp-doc">Comprar acá, vender en otro mercado. Tira 2d6 + modificadores.</div>';
      html += '<select id="sp-merc-dest-' + hexId + '" class="sp-select">';
      html += '<option value="">— Elegir destino —</option>';
      others.forEach(s => {
        const dist = distanceHexes(hex, s);
        html += '<option value="' + s.col + ',' + s.row + '">'
             + window.escapeHTML(s.name) + ' (Class ' + s.marketClass + ', ' + dist + ' hex)'
             + (s.hostile ? ' ⚔' : '')
             + '</option>';
      });
      html += '</select>';
      html += '<button class="sp-btn" onclick="rollMercantileFromHex(\'' + hexId + '\')">🎲 Tirar venture</button>';
      html += '<div class="sp-result" id="sp-merc-' + hexId + '"></div>';
      html += '</div>';
    }

    // ── Encuentros urbanos ──────────────────────────────────────────────
    html += '<div class="sp-section sp-section-compact">';
    html += '<div class="sp-row"><span class="sp-key">Urban enc check:</span> ' + der.urbanEncounter + ' por hora · ';
    html += '<span class="sp-key">districts:</span> Avenue, Slums, Temple, Market, Bohemian, Foreign Quarter</div>';
    html += '</div>';

    html += '</div>'; // /.settlement-panel
    return html;
  };

  // ───────────────────────────────────────────────────────────────────────
  // Acciones globales (invocadas desde onclick)
  // ───────────────────────────────────────────────────────────────────────
  window.rollHirelingsForHex = function (hexId) {
    const el = document.getElementById('sp-hirelings-' + hexId);
    if (!el) return;
    const hex = window.HEX_INDEX[hexId];
    if (!hex) return;
    const mc = getMarketClass(hex);
    const der = MARKET_DERIVED[mc];
    if (!der) { el.textContent = 'Sin market class.'; return; }
    const n = window.rollDice(der.hirelingsPerWeek);
    el.innerHTML = '<b>' + n + ' hirelings</b> disponibles esta semana <span class="sp-doc">(' + der.hirelingsPerWeek + ')</span>'
                + '<div class="sp-doc" style="margin-top:4px;">Asignar clases con tabla de specialist/henchman recruitment ACKS RB Ch.3.</div>';
    if (window.logEvent) window.logEvent('Hirelings disponibles ' + (hex.name || hexId) + ': ' + n);
  };

  window.rollMercantileFromHex = function (hexId) {
    const sel = document.getElementById('sp-merc-dest-' + hexId);
    const out = document.getElementById('sp-merc-' + hexId);
    if (!sel || !out) return;
    const destId = sel.value;
    if (!destId) { out.textContent = 'Elegí un destino primero.'; return; }
    const origin = window.HEX_INDEX[hexId];
    const dest   = window.HEX_INDEX[destId];
    if (!origin || !dest) { out.textContent = 'Hex no encontrado.'; return; }

    const mcA = getMarketClass(origin);
    const mcB = getMarketClass(dest);
    const classOrder = { I: 1, II: 2, III: 3, IV: 4, V: 5, VI: 6 };

    // Modificadores ACKS JJ Ch.2 — Mercantile Ventures supply_demand_mechanic
    let mods = 0;
    const modList = [];
    if (mcB === 'I' || mcB === 'II') { mods += 1; modList.push('+1 destino Class I/II'); }
    if (classOrder[mcA] && classOrder[mcB] && classOrder[mcA] < classOrder[mcB]) {
      mods += 1; modList.push('+1 Class A → Class B (más alta a más baja)');
    }
    if (mcA === mcB) { mods -= 1; modList.push('-1 mismo class'); }
    if (classOrder[mcA] && classOrder[mcB] && classOrder[mcA] > classOrder[mcB]) {
      mods -= 1; modList.push('-1 Class B → Class A (retorno)');
    }

    const r1 = window.rollDice('1d6'), r2 = window.rollDice('1d6');
    const total = r1 + r2 + mods;

    let result, mult;
    if (total <= 2)      { result = 'Outraged refusal — no se puede vender'; mult = 0; }
    else if (total <= 5) { result = 'Reluctant purchase';       mult = 0.5; }
    else if (total <= 8) { result = 'Standard market';          mult = 1.0; }
    else if (total <= 11){ result = 'Eager market';             mult = 1.2; }
    else                 { result = 'Frenzy';                   mult = 1.5; }

    const dist = distanceHexes(origin, dest);
    const days = Math.max(1, Math.round(dist / 24)); // aprox 1 watch/hex en escala 6mi → 24mi/día

    out.innerHTML = '<div class="sp-merc-result">'
      + '<div><b>2d6 = ' + r1 + '+' + r2 + ' = ' + (r1+r2) + '</b> · mods <b>' + (mods>=0?'+':'') + mods + '</b> · total <b>' + total + '</b></div>'
      + '<div class="sp-merc-verdict">' + result + ' · <b>×' + mult + '</b> baseline</div>'
      + '<div class="sp-doc" style="margin-top:4px;">Mods aplicados: ' + (modList.length ? modList.join(', ') : 'ninguno')
      + '<br>Ruta: ' + (origin.name||hexId) + ' → ' + (dest.name||destId)
      + ' · ' + dist + ' hex · ~' + days + ' día(s) viaje</div>'
      + '</div>';

    if (window.logEvent) {
      window.logEvent('Mercantile venture ' + (origin.name||hexId) + ' → ' + (dest.name||destId)
                      + ': 2d6=' + (r1+r2) + (mods>=0?'+':'') + mods + '=' + total + ' (' + result + ', ×' + mult + ')');
    }
  };

  // Exponer constantes para que el cockpit las consulte si quiere
  window.MARKET_DERIVED = MARKET_DERIVED;
  window.MARKET_POP_ESTIMATE = POP_ESTIMATE;

})();
