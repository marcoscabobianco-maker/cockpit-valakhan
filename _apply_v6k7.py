# V6k7: switch a coords_v8 (con table-row/col strict-consecutive detection)
# que arregla rooms 1-8 amontonados.

import re
import sys

SRC = 'prototipo_v6k6.html'
DST = 'prototipo_v6k7.html'

with open(SRC, encoding='utf-8') as f:
    src = f.read()

def patch(s, old, new, expected=1):
    n = s.count(old)
    if n != expected:
        print(f'PATCH FAILED: {old[:80]!r}', file=sys.stderr)
        sys.exit(1)
    return s.replace(old, new, expected)

# Title + version
src = patch(src,
    '<title>Cockpit v6k6 · Valakhan ATEM Farol Club</title>',
    '<title>Cockpit v6k7 · Valakhan ATEM Farol Club</title>'
)
src = patch(src,
    '  const _COCKPIT_VERSION = "v6k6";',
    '  const _COCKPIT_VERSION = "v6k7";'
)

# Switch to v8 coords
src = patch(src,
    "const BARROWMAZE_ROOMS_COORDS_SRC = 'maps/barrowmaze_room_coords_v3.json' + _CACHE_BUST;",
    "const BARROWMAZE_ROOMS_COORDS_SRC = 'maps/barrowmaze_room_coords_v8.json' + _CACHE_BUST;"
)

# Diagnostic overlay V6k6 -> V6k7
src = patch(src,
    "  ctx.fillText('🛠 V6k6 · Mobile=' + ((typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE) ? 'YES' : 'no'), 16, 14);",
    "  ctx.fillText('🛠 V6k7 · Mobile=' + ((typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE) ? 'YES' : 'no'), 16, 14);"
)

# Update modal message: not "v6k6" anymore
src = patch(src,
    "    modal += '<b>Sala '+rid+' (PDF vector — V6k6)</b><br><br>';",
    "    modal += '<b>Sala '+rid+' (PDF vector — V6k7 con table fix)</b><br><br>';"
)

with open(DST, 'w', encoding='utf-8') as f:
    f.write(src)
print(f'OK: wrote {DST} ({len(src):,} chars)')
