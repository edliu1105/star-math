# -*- coding: utf-8 -*-
"""生成带文件名标签的素材接触印像，用于逐张目检。"""
import os, math
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AST = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "shots")
os.makedirs(OUT, exist_ok=True)

try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 20)
except Exception:
    FONT = ImageFont.load_default()


def sheet(folder, name, cell=190, cols=8, bgcolor=(38, 28, 72)):
    d = os.path.join(AST, folder)
    files = sorted(f for f in os.listdir(d) if f.lower().endswith((".png", ".jpg")))
    rows = math.ceil(len(files) / cols)
    W, H = cols * cell, rows * (cell + 28)
    out = Image.new("RGB", (W, H), bgcolor)
    dr = ImageDraw.Draw(out)
    for i, f in enumerate(files):
        r, c = divmod(i, cols)
        x, y = c * cell, r * (cell + 28)
        # 棋盘格底，便于看透明度与白边
        for by in range(0, cell, 16):
            for bx in range(0, cell, 16):
                if ((bx // 16) + (by // 16)) % 2 == 0:
                    dr.rectangle([x + bx, y + by, x + bx + 15, y + by + 15], fill=(72, 60, 110))
        im = Image.open(os.path.join(d, f)).convert("RGBA")
        s = min((cell - 12) / im.size[0], (cell - 12) / im.size[1])
        im = im.resize((max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s))), Image.LANCZOS)
        out.paste(im, (x + (cell - im.size[0]) // 2, y + (cell - im.size[1]) // 2), im)
        dr.rectangle([x, y, x + cell - 1, y + cell - 1], outline=(120, 105, 170))
        label = f.rsplit(".", 1)[0]
        dr.text((x + 6, y + cell + 4), label, fill=(255, 232, 150), font=FONT)
    p = os.path.join(OUT, "sheet-%s.png" % name)
    out.save(p, optimize=True)
    print("%s: %d files -> %s" % (name, len(files), p))


sheet("chars", "chars", cols=8)
sheet("props", "props", cols=7)
sheet("bg", "bg", cell=260, cols=4)
