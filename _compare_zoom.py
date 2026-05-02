# Comparison side-by-side:
# IZQUIERDA: PDF page 3 (mod 236) con sus markers detectados (cofirmacion visual del PDF)
# DERECHA: zoom del cuadrante BOT-LEFT del stitched real con TODOS los markers v3 que caen alli
# Si los patterns coinciden, el mapping v3 es correcto.

import fitz
from PIL import Image, ImageDraw, ImageFont
import json
import re
import os

PDF = '_pdfs/Mapas de Barrowmaze 10th Ebook OSR 2022.pdf'
RAW = '_pdf_extracted_raw.json'
STITCHED = 'maps/barrowmaze_bg_1920.webp'
COORDS_V3 = 'maps/barrowmaze_room_coords_v3.json'

with open(RAW, encoding='utf-8') as f:
    raw = json.load(f)
with open(COORDS_V3, encoding='utf-8') as f:
    v3 = json.load(f)

ROOM_PAT = re.compile(r'^([QDM]?\d{1,3}[A-Za-z]?)$')
HEADER = {'234','235','236','237','238','239'}

# ---- LEFT: PDF page 3 with markers
doc = fitz.open(PDF)
PG_IDX = 2  # page 3
SCALE = 2.0
page = doc[PG_IDX]
pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE))
left_img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
left_w, left_h = left_img.size
draw_l = ImageDraw.Draw(left_img, 'RGBA')

font_label = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 14)
font_header = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 24)

p3_markers = [e for e in raw
              if e['page'] == 3
              and ROOM_PAT.match(e['text'])
              and e['text'] not in HEADER
              and not (len(e['text']) == 1 and e['text'].isalpha())]
for m in p3_markers:
    x = m['x'] * SCALE
    y = m['y'] * SCALE
    r = 14
    draw_l.ellipse((x-r, y-r, x+r, y+r), outline='#00ff00', width=2)

# ---- RIGHT: zoom of bot-left quadrant of stitched (page 3 area) with v3 markers
stitched = Image.open(STITCHED).convert('RGB')
sw, sh = stitched.size
# Bot-left quadrant: x in [0, sw/3], y in [sh/2, sh]
crop_x0, crop_y0 = 0, sh // 2
crop_x1, crop_y1 = sw // 3, sh
right_img = stitched.crop((crop_x0, crop_y0, crop_x1, crop_y1))
right_w, right_h = right_img.size
draw_r = ImageDraw.Draw(right_img, 'RGBA')

svg_w = v3['svg_w']
svg_h = v3['svg_h']
sx = sw / svg_w
sy = sh / svg_h

# Find all markers v3 that fall in bot-left tile
tile_x_min = 0
tile_x_max = svg_w / 3
tile_y_min = svg_h / 2
tile_y_max = svg_h
markers_v3 = []
for rid, c in v3['room_coords'].items():
    if tile_x_min <= c['x'] < tile_x_max and tile_y_min <= c['y'] < tile_y_max:
        markers_v3.append((rid, c['x'], c['y']))

print(f'Markers v3 in bot-left tile: {len(markers_v3)}')
print(f'PDF p3 markers: {len(p3_markers)}')

for rid, x, y in markers_v3:
    px = x * sx - crop_x0
    py = y * sy - crop_y0
    r = 16
    draw_r.ellipse((px-r-2, py-r-2, px+r+2, py+r+2), fill='#000')
    draw_r.ellipse((px-r, py-r, px+r, py+r), fill='#f5b342')
    text = rid
    bbox = draw_r.textbbox((0, 0), text, font=font_label)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    draw_r.text((px - tw/2 - bbox[0], py - th/2 - bbox[1]), text, fill='#000', font=font_label)

# Resize right to match left height
target_h = left_h
ratio = target_h / right_h
right_resized = right_img.resize((int(right_w * ratio), target_h), Image.LANCZOS)

# Combine side-by-side with header
HDR_H = 50
total_w = left_w + 30 + right_resized.width
total_h = target_h + HDR_H
combo = Image.new('RGB', (total_w, total_h), 'white')
draw_c = ImageDraw.Draw(combo)
draw_c.text((10, 14), 'PDF p.3 (mod 236) - circulos verdes = markers detectados',
            fill='black', font=font_header)
draw_c.text((left_w + 40, 14), 'STITCHED bot-left - markers v3 mapeados',
            fill='black', font=font_header)
combo.paste(left_img, (0, HDR_H))
combo.paste(right_resized, (left_w + 30, HDR_H))
combo.save('_compare_v3_p3.jpg', 'JPEG', quality=82)
print(f'Saved _compare_v3_p3.jpg ({os.path.getsize("_compare_v3_p3.jpg")//1024} KB)')
