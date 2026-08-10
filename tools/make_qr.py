# -*- coding: utf-8 -*-
"""生成供 iPad 相机扫描的二维码 PNG。用法: python tools/make_qr.py <URL>"""
import sys, os
import qrcode
from qrcode.image.styledpil import StyledPilImage
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
url = sys.argv[1] if len(sys.argv) > 1 else "https://edliu1105.github.io/star-math/"
out = os.path.join(ROOT, "qrcode.png")

qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H,
                   box_size=14, border=3)
qr.add_data(url)
qr.make(fit=True)
img = qr.make_image(fill_color="#1b1140", back_color="white").convert("RGB")

# 中心贴 app 图标
icon_p = os.path.join(ROOT, "assets", "icon-192.png")
if os.path.exists(icon_p):
    ic = Image.open(icon_p).convert("RGB")
    k = img.size[0] // 5
    ic = ic.resize((k, k), Image.LANCZOS)
    pad = Image.new("RGB", (k + 18, k + 18), "white")
    pad.paste(ic, (9, 9))
    img.paste(pad, ((img.size[0] - pad.size[0]) // 2, (img.size[1] - pad.size[1]) // 2))

# 底部说明条
W = img.size[0]
bar = 130
canvas = Image.new("RGB", (W, img.size[1] + bar), "white")
canvas.paste(img, (0, 0))
d = ImageDraw.Draw(canvas)


def font(sz, bold=True):
    for f in ("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
              "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except Exception:
            continue
    return ImageFont.load_default()


def center(text, y, f, fill):
    w = d.textbbox((0, 0), text, font=f)[2]
    d.text(((W - w) // 2, y), text, font=f, fill=fill)


center("星星回家 · 用 iPad 相机扫一扫", img.size[1] - 10, font(34), "#1b1140")
center(url, img.size[1] + 40, font(24, False), "#5a4f7a")
center("打开后：分享 → 添加到主屏幕", img.size[1] + 82, font(24, False), "#8a7fb0")
canvas.save(out, optimize=True)
print("QR ->", out, "  URL:", url)
