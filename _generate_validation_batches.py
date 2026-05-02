# Genera imagenes de validacion por batch para confirmar markers del cockpit.
# Cada batch dibuja N markers (dorado grande con numero) sobre el mapa real.

from PIL import Image, ImageDraw, ImageFont
import json
import os

src_img = 'maps/barrowmaze_bg_1920.webp'
src_coords = 'maps/barrowmaze_room_coords.json'
out_dir = '_validation_batches'

with open(src_coords, encoding='utf-8') as f:
    coords_data = json.load(f)

svg_w = coords_data['svg_w']
svg_h = coords_data['svg_h']
room_coords = coords_data['room_coords']

base_img = Image.open(src_img).convert('RGB')
img_w, img_h = base_img.size
sx = img_w / svg_w
sy = img_h / svg_h

print(f'Image: {img_w}x{img_h}, scale x={sx:.3f} y={sy:.3f}')

sorted_ids = sorted(room_coords.keys(), key=lambda x: int(x))
print(f'Total IDs: {len(sorted_ids)}')

os.makedirs(out_dir, exist_ok=True)

font_main = None
font_header = None
for fp in ['C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/arial.ttf']:
    if os.path.exists(fp):
        font_main = ImageFont.truetype(fp, 32)
        font_header = ImageFont.truetype(fp, 38)
        break
if not font_main:
    font_main = ImageFont.load_default()
    font_header = ImageFont.load_default()

BATCH_SIZE = 20
N_BATCHES = 5  # rooms 1-100

for batch_idx in range(N_BATCHES):
    start = batch_idx * BATCH_SIZE
    end = min(start + BATCH_SIZE, len(sorted_ids))
    ids_in_batch = sorted_ids[start:end]
    if not ids_in_batch:
        break

    img = base_img.copy()
    draw = ImageDraw.Draw(img, 'RGBA')

    # Draw markers
    for rid in ids_in_batch:
        pos = room_coords[rid]
        x = pos['x'] * sx
        y = pos['y'] * sy
        r = 30
        # Outer black ring
        draw.ellipse((x-r-3, y-r-3, x+r+3, y+r+3), fill='#000')
        # White contrast
        draw.ellipse((x-r-1, y-r-1, x+r+1, y+r+1), fill='#fff')
        # Inner gold
        draw.ellipse((x-r+2, y-r+2, x+r-2, y+r-2), fill='#f5b342')
        # Number centered
        text = rid
        bbox = draw.textbbox((0, 0), text, font=font_main)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((x - tw/2 - bbox[0], y - th/2 - bbox[1]), text, fill='#000', font=font_main)

    # Top header
    draw.rectangle((0, 0, img_w, 70), fill=(0, 0, 0, 235))
    header = f'BATCH {batch_idx+1:02d}/05  -  Rooms {ids_in_batch[0]} a {ids_in_batch[-1]}  ({len(ids_in_batch)} markers)'
    draw.text((20, 14), header, fill='#f5b342', font=font_header)

    out_path = os.path.join(out_dir, f'validation_batch_{batch_idx+1:03d}.jpg')
    img.save(out_path, 'JPEG', quality=82, optimize=True)
    size_kb = os.path.getsize(out_path) // 1024
    print(f'OK {out_path} ({size_kb} KB)')

print('Done')
