# Extract JS scripts (excluding application/json + src=) and write to _v6k5_scripts.js
import re

src = open('prototipo_v6k5.html', encoding='utf-8').read()
blocks = re.findall(r'<script([^>]*)>(.*?)</script>', src, flags=re.DOTALL)

js = []
skipped = []
type_pat = re.compile(r"""type=["']([^"']+)["']""")
for attrs, content in blocks:
    if 'src=' in attrs:
        skipped.append(('external', len(content)))
        continue
    m = type_pat.search(attrs)
    if m:
        t = m.group(1).lower()
        if t not in ('text/javascript', 'application/javascript', 'module'):
            skipped.append((t, len(content)))
            continue
    js.append(content)

print(f'JS scripts: {len(js)} | skipped types: {[s[0] for s in skipped]}')
print(f'Total JS chars: {sum(len(s) for s in js):,}')
open('_v6k5_scripts.js', 'w', encoding='utf-8').write('\n;\n'.join(js))
