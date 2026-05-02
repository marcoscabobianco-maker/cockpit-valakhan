# Render las 6 paginas del PDF como thumbnails y armar grid 3x2 deducido.
# Compara contra el stitched real para confirmar layout.

import fitz
from PIL import Image
import os

PDF = '_pdfs/Mapas de Barrowmaze 10th Ebook OSR 2022.pdf'
STITCHED = 'maps/barrowmaze_bg_1920.webp'

# Hipotesis: layout 3x2 = [234, 235, 238] / [236, 237, 239]
# PDF page 1 = module 234, page 2 = module 235, etc.
# Layout (PDF page 1-indexed): [1, 2, 5] / [3, 4, 6]
LAYOUT = [
    [1, 2, 5],
    [3, 4, 6],
]

doc = fitz.open(PDF)

# Render each page at low DPI for thumbnails
TILE_W, TILE_H = 400, 520
thumbs = {}
for page_idx in range(6):
    page = doc[page_idx]
    pix = page.get_pixmap(matrix=fitz.Matrix(TILE_W / page.rect.width, TILE_H / page.rect.height))
    img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    thumbs[page_idx + 1] = img.resize((TILE_W, TILE_H))

# Build hypothesis grid
grid_w = TILE_W * 3
grid_h = TILE_H * 2
grid = Image.new('RGB', (grid_w, grid_h), 'white')
from PIL import ImageDraw, ImageFont
font = None
for fp in ['C:/Windows/Fonts/arialbd.ttf']:
    if os.path.exists(fp):
        font = ImageFont.truetype(fp, 24)
        break

draw = ImageDraw.Draw(grid)
for row, row_pages in enumerate(LAYOUT):
    for col, pdf_page in enumerate(row_pages):
        x = col * TILE_W
        y = row * TILE_H
        grid.paste(thumbs[pdf_page], (x, y))
        # Label
        module_page = 233 + pdf_page
        label = f'PDF p.{pdf_page} (mod {module_page})'
        # Box behind text
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.rectangle((x+5, y+5, x+15+tw, y+15+th), fill='red')
        draw.text((x+10, y+10), label, fill='white', font=font)

grid.save('_layout_hypothesis.jpg', 'JPEG', quality=82)
print(f'Hypothesis grid: {grid_w}x{grid_h}')

# Also resize stitched to same dims for visual comparison
stitched = Image.open(STITCHED).convert('RGB')
print(f'Stitched original: {stitched.size}')
stitched_resized = stitched.resize((grid_w, grid_h), Image.LANCZOS)
stitched_resized.save('_stitched_thumb.jpg', 'JPEG', quality=82)
print(f'Stitched thumb: {stitched_resized.size}')

# Side-by-side comparison
combo = Image.new('RGB', (grid_w * 2 + 20, grid_h + 50), 'white')
draw_c = ImageDraw.Draw(combo)
draw_c.text((10, 10), 'HYPOTHESIS (PDF 6 pages in 3x2 grid)', fill='black', font=font)
draw_c.text((grid_w + 30, 10), 'REAL STITCHED (barrowmaze_bg_1920)', fill='black', font=font)
combo.paste(grid, (0, 50))
combo.paste(stitched_resized, (grid_w + 20, 50))
combo.save('_layout_comparison.jpg', 'JPEG', quality=82)
size_kb = os.path.getsize('_layout_comparison.jpg') // 1024
print(f'Comparison: {combo.size} ({size_kb} KB)')
