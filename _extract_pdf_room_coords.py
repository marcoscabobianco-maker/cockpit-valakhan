# Extrae todos los textos del PDF de mapas con sus coords (x, y, page).
# Output: _pdf_extracted_raw.json con TODOS los textos (filtrar despues).

import fitz
import json
import re

PDF = '_pdfs/Mapas de Barrowmaze 10th Ebook OSR 2022.pdf'

doc = fitz.open(PDF)

# words returns list of (x0, y0, x1, y1, text, block_no, line_no, word_no)
all_extractions = []
for page_idx, page in enumerate(doc):
    pw, ph = page.rect.width, page.rect.height
    words = page.get_text('words')
    for w in words:
        x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        all_extractions.append({
            'page': page_idx + 1,  # 1-indexed
            'page_w': pw,
            'page_h': ph,
            'text': text,
            'x': round(cx, 2),
            'y': round(cy, 2),
            'x0': round(x0, 2),
            'y0': round(y0, 2),
            'x1': round(x1, 2),
            'y1': round(y1, 2),
            'w': round(x1 - x0, 2),
            'h': round(y1 - y0, 2),
        })

with open('_pdf_extracted_raw.json', 'w', encoding='utf-8') as f:
    json.dump(all_extractions, f, ensure_ascii=False, indent=1)

print(f'Total text fragments: {len(all_extractions)}')
print(f'Page breakdown:')
from collections import Counter
c = Counter(e['page'] for e in all_extractions)
for p in sorted(c):
    print(f'  Page {p}: {c[p]}')

# Quick analysis: room ID candidates
ROOM_PAT = re.compile(r'^([QDM]?\d{1,3}[A-Za-z]?)$')  # Q1, D1, M1, 23, 92A
SUB_PAT = re.compile(r'^[A-F]$')  # A, B, C, D, E, F (sub-areas)

room_candidates = [e for e in all_extractions if ROOM_PAT.match(e['text'])]
sub_candidates = [e for e in all_extractions if SUB_PAT.match(e['text'])]
print(f'\nRoom-like tokens: {len(room_candidates)}')
print(f'Sub-area letters (A-F alone): {len(sub_candidates)}')

# Distinct room IDs
ids = sorted(set(e['text'] for e in room_candidates))
print(f'Distinct room IDs: {len(ids)}')
print(f'Sample first 30: {ids[:30]}')
print(f'Sample last 30: {ids[-30:]}')

# Count by prefix
from collections import defaultdict
by_prefix = defaultdict(list)
for x in ids:
    if x[0] in ('Q', 'D', 'M'):
        by_prefix[x[0]].append(x)
    else:
        by_prefix['NUM'].append(x)
for p, xs in sorted(by_prefix.items()):
    print(f'  Prefix {p}: {len(xs)} | sample: {xs[:8]} ... {xs[-4:]}')
