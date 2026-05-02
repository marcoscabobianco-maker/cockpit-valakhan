# Render UNA pagina del PDF con sus markers detectados encima.
# Si los markers caen exactamente sobre los textos visibles del mapa,
# la extraccion vectorial es correcta y el problema esta en el mapping al stitched.

import fitz
from PIL import Image, ImageDraw, ImageFont
import json
import os

PDF = '_pdfs/Mapas de Barrowmaze 10th Ebook OSR 2022.pdf'
RAW_DATA = '_pdf_extracted_raw.json'

with open(RAW_DATA, encoding='utf-8') as f:
    data = json.load(f)

doc = fitz.open(PDF)

# Render each page at moderate DPI
DPI_SCALE = 2.0  # 2x for clarity
font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 20)

os.makedirs('_pdf_validation', exist_ok=True)

for page_idx in range(6):
    page = doc[page_idx]
    pw, ph = page.rect.width, page.rect.height
    pix = page.get_pixmap(matrix=fitz.Matrix(DPI_SCALE, DPI_SCALE))
    img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    draw = ImageDraw.Draw(img, 'RGBA')

    # Draw markers for all texts on this page that match room ID pattern
    import re
    ROOM_PAT = re.compile(r'^([QDM]?\d{1,3}[A-Za-z]?)$')
    HEADER = {'234','235','236','237','238','239'}
    markers = [e for e in data
               if e['page'] == page_idx + 1
               and ROOM_PAT.match(e['text'])
               and e['text'] not in HEADER
               and not (len(e['text']) == 1 and e['text'].isalpha())]

    for m in markers:
        x = m['x'] * DPI_SCALE
        y = m['y'] * DPI_SCALE
        # Red translucent circle around the detected text
        r = 16
        draw.ellipse((x-r, y-r, x+r, y+r),
                     outline='#ff0000', width=3)
        # No need to overlay text since the PDF already has it

    # Header
    h_box_h = 50
    draw.rectangle((0, 0, img.width, h_box_h), fill=(0, 100, 0, 220))
    draw.text((10, 12),
              f'PDF p.{page_idx+1} (mod {233+page_idx+1}) — {len(markers)} markers detectados (circulos rojos)',
              fill='white', font=font)

    out_path = f'_pdf_validation/pdf_p{page_idx+1}_mod{233+page_idx+1}.jpg'
    img.save(out_path, 'JPEG', quality=80, optimize=True)
    print(f'OK {out_path} ({os.path.getsize(out_path)//1024} KB, {len(markers)} markers)')
