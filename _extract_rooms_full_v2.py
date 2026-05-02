# Re-extrae rooms_full del modulo PDF (264p) usando blocks column-aware.
# Output: barrowmaze_rooms_full_v2.json con IDs reales.

import fitz
import json
import re
from collections import defaultdict

PDF = '_pdfs/Barrowmaze 10th Ebook OSR 2022.pdf'

# Room heading patterns
PATTERNS = [
    (re.compile(r'^(\d{1,3})\.\s+(.{5,})', re.DOTALL), lambda m: m.group(1)),
    (re.compile(r'^(\d{1,3}[A-Z])\.\s+(.{5,})', re.DOTALL), lambda m: m.group(1)),
    (re.compile(r'^Qu[ia]+nt?\s+Crypt\s+(\d+):\s+(.{5,})', re.DOTALL | re.IGNORECASE), lambda m: 'Q' + m.group(1)),
    (re.compile(r'^Quiet\s+Crypt\s+(\d+):\s+(.{5,})', re.DOTALL | re.IGNORECASE), lambda m: 'Q' + m.group(1)),
    (re.compile(r'^Defiled\s+Crypt\s+(\d+):\s+(.{5,})', re.DOTALL | re.IGNORECASE), lambda m: 'D' + m.group(1)),
]

def detect_room(text):
    """Returns (rid, body) or (None, None)."""
    txt = text.strip()
    for pat, key_fn in PATTERNS:
        m = pat.match(txt)
        if m:
            return (key_fn(m), txt)
    return (None, None)

doc = fitz.open(PDF)

# Skip intro+Mounds section (book p.1-60) and appendices
SKIP_PAGES = set(range(0, 63))
SKIP_PAGES.update(range(220, 264))

# Two-pass: first collect ALL block matches per rid, then pick best per rid.
all_matches = defaultdict(list)  # rid -> list of {text, page_pdf, page_book, w, h}
for pidx in range(len(doc)):
    if pidx in SKIP_PAGES:
        continue
    page = doc[pidx]
    blocks = page.get_text('blocks')
    for b in blocks:
        x0, y0, x1, y1, text, blknum, btype = b
        if btype != 0:
            continue
        rid, body = detect_room(text)
        if rid is None:
            continue
        all_matches[rid].append({
            'text': body,
            'page_pdf': pidx + 1,
            'page_book': pidx - 2,
            'w': x1 - x0,
            'h': y1 - y0,
        })

# For adjacency: only count "real room blocks" (height >= 25 AND width >= 200) as neighbors.
# This excludes table entries which have many tiny consecutive numbers.
real_pages_with_rid = {}  # rid -> set of pages where rid has a REAL ROOM block
for rid, matches in all_matches.items():
    real = set(m['page_pdf'] for m in matches if m['h'] >= 22 and m['w'] >= 200)
    real_pages_with_rid[rid] = real

def adjacency_bonus(rid, page_pdf):
    """Count of adjacent numeric rids that ALSO have a real room block on this page."""
    if not rid.isdigit():
        return 0
    n = int(rid)
    score = 0
    for delta in range(-3, 4):
        if delta == 0: continue
        nbr = str(n + delta)
        if nbr in real_pages_with_rid and page_pdf in real_pages_with_rid[nbr]:
            score += 1
    return score

rooms = {}
qd_all = {}
for rid, matches in all_matches.items():
    if rid[0] in ('Q', 'D'):
        room_like = [m for m in matches if m['w'] >= 150 or m['h'] >= 20]
        candidates = room_like if room_like else matches
        qd_all[rid] = sorted(candidates, key=lambda m: m['page_pdf'])
        chosen = min(candidates, key=lambda m: m['page_pdf'])
    else:
        # Score across ALL matches: high adjacency wins, then real, then room-like, then earliest
        def score_match(m):
            adj = adjacency_bonus(rid, m['page_pdf'])
            is_real = 1 if (m['h'] >= 22 and m['w'] >= 200) else 0
            is_room_like = 1 if (m['w'] >= 150 or m['h'] >= 20) else 0
            return (-adj, -is_real, -is_room_like, m['page_pdf'])
        chosen = sorted(matches, key=score_match)[0]
    rooms[rid] = chosen

print(f'Total rooms extracted: {len(rooms)}')

# Breakdown by prefix
by_prefix = defaultdict(list)
for k in rooms:
    if k[0] in 'QDM':
        by_prefix[k[0]].append(k)
    elif k[-1].isalpha() and len(k) > 1:
        by_prefix['NUM+sub'].append(k)
    else:
        by_prefix['NUM'].append(k)
for p, ks in sorted(by_prefix.items()):
    sample = sorted(ks, key=lambda x: (x[0], int(re.search(r'\d+', x).group())))[:8]
    print(f'  {p}: {len(ks)} | sample: {sample}')

# Cross-reference with v8 coords
with open('maps/barrowmaze_room_coords_v8.json', encoding='utf-8') as f:
    coords_v8 = json.load(f)
v8_ids = set(coords_v8['room_coords'].keys())
extracted_ids = set(rooms.keys())

in_both = v8_ids & extracted_ids
only_v8 = v8_ids - extracted_ids
only_text = extracted_ids - v8_ids
print(f'\nIDs in both (coords + descriptions): {len(in_both)}')
print(f'IDs only in v8 coords (no description found): {len(only_v8)}')
if only_v8:
    print(f'  sample: {sorted(only_v8, key=lambda x: (x[0], len(x)))[:20]}')
print(f'IDs only in extracted text (no map marker): {len(only_text)}')
if only_text:
    print(f'  sample: {sorted(only_text)[:20]}')

# Save
output = {
    '_doc': 'Barrowmaze rooms_full v2 - extracted from full module PDF with column-aware blocks. Q/D have all instances.',
    '_source': 'Barrowmaze 10th Ebook OSR 2022.pdf (264 pages)',
    '_method': 'pymupdf get_text(blocks) + heading regex + adjacency bonus for numeric',
    '_count': len(rooms),
    'rooms': {rid: {
        'text': r['text'],
        'page_pdf': r['page_pdf'],
        'page_book': r['page_book'],
        'has_marker': rid in v8_ids,
        'all_instances': [
            {'text': m['text'], 'page_book': m['page_book']}
            for m in qd_all.get(rid, [])
        ] if rid in qd_all else None,
    } for rid, r in rooms.items()}
}
with open('maps/barrowmaze_rooms_full_v3.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=1)
print('\nSaved maps/barrowmaze_rooms_full_v3.json')

# Sample rooms 1-3
print('\n=== Sample room 1 ===')
print(rooms.get('1', {}).get('text', 'MISSING')[:400])
print('\n=== Sample room 5 ===')
print(rooms.get('5', {}).get('text', 'MISSING')[:400])
print('\n=== Sample Q1 ===')
print(rooms.get('Q1', {}).get('text', 'MISSING')[:400])
print('\n=== Sample 151 ===')
print(rooms.get('151', {}).get('text', 'MISSING')[:400])
