# V6k9: switch a coords v10 (anchor-based — rooms 2,3,5,6 cerca del 1)

import re, sys
SRC = 'prototipo_v6k8.html'
DST = 'prototipo_v6k9.html'
src = open(SRC, encoding='utf-8').read()

def patch(s, old, new, expected=1):
    n = s.count(old)
    if n != expected:
        print(f'PATCH FAIL ({n}): {old[:70]!r}', file=sys.stderr)
        sys.exit(1)
    return s.replace(old, new, expected)

src = patch(src, '<title>Cockpit v6k8 · Valakhan ATEM Farol Club</title>',
                 '<title>Cockpit v6k9 · Valakhan ATEM Farol Club</title>')
src = patch(src, '  const _COCKPIT_VERSION = "v6k8";',
                 '  const _COCKPIT_VERSION = "v6k9";')
src = patch(src,
    "const BARROWMAZE_ROOMS_COORDS_SRC = 'maps/barrowmaze_room_coords_v9.json' + _CACHE_BUST;",
    "const BARROWMAZE_ROOMS_COORDS_SRC = 'maps/barrowmaze_room_coords_v10.json' + _CACHE_BUST;")
src = patch(src,
    "  ctx.fillText('🛠 V6k8 · Mobile=' + ((typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE) ? 'YES' : 'no'), 16, 14);",
    "  ctx.fillText('🛠 V6k9 · Mobile=' + ((typeof _IS_MOBILE !== 'undefined' && _IS_MOBILE) ? 'YES' : 'no'), 16, 14);")

open(DST, 'w', encoding='utf-8').write(src)
print(f'OK: wrote {DST} ({len(src):,} chars)')
