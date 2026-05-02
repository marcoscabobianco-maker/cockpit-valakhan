# Validation batches for v2 coords
from PIL import Image, ImageDraw, ImageFont
import json
import os

src_img = 'maps/barrowmaze_bg_1920.webp'
src_coords = 'maps/barrowmaze_room_coords_v2.json'
out_dir = '_validation_batches_v2'

with open(src_coords, encoding='utf-8') as f:
    coords_data = json.load(f)

svg_w = coords_data['svg_w']
svg_h = coords_data['svg_h']
room_coords = coords_data['room_coords']

base_img = Image.open(src_img).convert('RGB')
img_w, img_h = base_img.size
sx = img_w / svg_w
sy = img_h / svg_h

# Sort: numeric first, then Q, then D
def sort_key(rid):
    if rid[0] == 'Q':
        return (1, int(rid[1:]) if rid[1:].isdigit() else 999, rid)
    if rid[0] == 'D':
        return (2, int(rid[1:]) if rid[1:].isdigit() else 999, rid)
    if rid[0].isdigit():
        # Strip trailing letter for sorting
        m = rid
        if m[-1].isalpha():
            num = int(m[:-1])
            return (0, num, rid)
        return (0, int(m), rid)
    return (3, 999, rid)

sorted_ids = sorted(room_coords.keys(), key=sort_key)
os.makedirs(out_dir, exist_ok=True)

font_main = None
font_header = None
for fp in ['C:/Windows/Fonts/arialbd.ttf']:
    if os.path.exists(fp):
        font_main = ImageFont.truetype(fp, 26)
        font_header = ImageFont.truetype(fp, 36)
        break

BATCH_SIZE = 20
N_BATCHES = 5  # primer 100 rooms numéricos

for batch_idx in range(N_BATCHES):
    start = batch_idx * BATCH_SIZE
    end = min(start + BATCH_SIZE, len(sorted_ids))
    ids_in_batch = sorted_ids[start:end]
    if not ids_in_batch:
        break

    img = base_img.copy()
    draw = ImageDraw.Draw(img, 'RGBA')

    for rid in ids_in_batch:
        pos = room_coords[rid]
        x = pos['x'] * sx
        y = pos['y'] * sy
        # Marker size depends on label length (Q/D/sub-letter)
        r = 28 if len(rid) <= 2 else 32
        draw.ellipse((x-r-3, y-r-3, x+r+3, y+r+3), fill='#000')
        draw.ellipse((x-r-1, y-r-1, x+r+1, y+r+1), fill='#fff')
        draw.ellipse((x-r+2, y-r+2, x+r-2, y+r-2), fill='#f5b342')
        text = rid
        bbox = draw.textbbox((0, 0), text, font=font_main)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((x - tw/2 - bbox[0], y - th/2 - bbox[1]), text, fill='#000', font=font_main)

    draw.rectangle((0, 0, img_w, 78), fill=(0, 0, 0, 235))
    header = f'V2 BATCH {batch_idx+1:02d}/{N_BATCHES}  -  {ids_in_batch[0]} a {ids_in_batch[-1]}  ({len(ids_in_batch)})'
    draw.text((20, 18), header, fill='#7eef87', font=font_header)

    out_path = os.path.join(out_dir, f'v2_batch_{batch_idx+1:03d}.jpg')
    img.save(out_path, 'JPEG', quality=82, optimize=True)
    print(f'OK {out_path} ({os.path.getsize(out_path)//1024} KB)')

print('Done')
