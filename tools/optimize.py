# -*- coding: utf-8 -*-
"""raw/ -> assets/  体积优化 + 边缘去白晕 + 自动裁切 + 图标合成"""
import os, sys, math
from PIL import Image, ImageFilter, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(ROOT, "raw")
AST  = os.path.join(ROOT, "assets")

CHARS = ["wukong","tangseng","bajie","shaseng","bailongma",
         "hulu1","hulu2","hulu3","hulu4","hulu5","hulu6","hulu7","yeye","shejing","xiezijing",
         "ironman","cap","thor","hulkman","widow","hawkeye","spider","spiderblack",
         "ryder","chase","marshall","skye","rubble","zuma","rocky",
         "bluey","bingo","bandit","chilli",
         "peppa","george","daddypig","mummypig","blackpanther"]
PROPS = ["star","gubang_seg","gubang_tip","stone","turtle","icecream","cookie","mudblob",
         "goon","portal","quinjet","basket",
         "gourd_r","gourd_o","gourd_y","gourd_g","gourd_c","gourd_b","gourd_p"]
BGS   = ["bg_sky","bg_monkey","bg_hulu","bg_aveng","bg_paw","bg_bluey","bg_peppa"]

TILEABLE = {"gubang_seg"}          # 需要横向可平铺 -> 不裁切左右


def dehalo(im, rounds=2):
    """去掉抠图残留的白色edge halo：贴着透明区、且接近纯白的像素 -> 透明"""
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for _ in range(rounds):
        a = im.getchannel("A")
        # 透明邻域：把 alpha 做最小值滤波，找出"附近有透明"的像素
        near_transparent = a.filter(ImageFilter.MinFilter(3))
        nt = near_transparent.load()
        ap = a.load()
        kill = []
        for y in range(h):
            for x in range(w):
                if ap[x, y] > 0 and nt[x, y] < 250:
                    r, g, b, al = px[x, y]
                    if r > 232 and g > 232 and b > 232:
                        kill.append((x, y))
        if not kill:
            break
        for x, y in kill:
            r, g, b, al = px[x, y]
            px[x, y] = (r, g, b, 0)
    return im


def autocrop(im, pad_ratio=0.02, keep_x=False):
    a = im.getchannel("A")
    bbox = a.getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    w, h = im.size
    pad = int(max(w, h) * pad_ratio)
    if keep_x:
        l, r = 0, w
    else:
        l = max(0, l - pad); r = min(w, r + pad)
    t = max(0, t - pad); b = min(h, b + pad)
    return im.crop((l, t, r, b))


def fit(im, longest):
    w, h = im.size
    if max(w, h) <= longest:
        return im
    s = longest / float(max(w, h))
    return im.resize((max(1, int(round(w * s))), max(1, int(round(h * s)))), Image.LANCZOS)


def save_png(im, path, colors=256):
    im = im.convert("RGBA")
    # 保留 alpha 的量化（FASTOCTREE 支持 RGBA）
    try:
        q = im.quantize(colors=colors, method=Image.FASTOCTREE)
        q.save(path, optimize=True)
    except Exception:
        im.save(path, optimize=True)


def do_transparent(names, outdir, longest, colors=256, thumbs=None):
    os.makedirs(outdir, exist_ok=True)
    if thumbs:
        os.makedirs(thumbs[0], exist_ok=True)
    made, missing = [], []
    for n in names:
        src = os.path.join(RAW, n + ".png")
        if not os.path.exists(src):
            missing.append(n); continue
        im = Image.open(src).convert("RGBA")
        im = dehalo(im)
        im = autocrop(im, keep_x=(n in TILEABLE))
        big = fit(im, longest)
        save_png(big, os.path.join(outdir, n + ".png"), colors)
        if thumbs:
            save_png(fit(im, thumbs[1]), os.path.join(thumbs[0], n + ".png"), 128)
        made.append(n)
    return made, missing


def do_bg(names, outdir, width=1280, quality=82):
    os.makedirs(outdir, exist_ok=True)
    made, missing = [], []
    for n in names:
        src = os.path.join(RAW, n + ".png")
        if not os.path.exists(src):
            missing.append(n); continue
        im = Image.open(src).convert("RGB")
        w, h = im.size
        if w > width:
            im = im.resize((width, int(round(h * width / float(w)))), Image.LANCZOS)
        im.save(os.path.join(outdir, n + ".jpg"), "JPEG", quality=quality, optimize=True, progressive=True)
        made.append(n)
    return made, missing


def make_icons():
    """apple-touch-icon 等：夜空底 + 星星 + 主角剪影"""
    star_p = os.path.join(AST, "props", "star.png")
    for size in (180, 192, 512):
        base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(base)
        for y in range(size):
            t = y / float(size - 1)
            r = int(0x2b + (0x14 - 0x2b) * t); g = int(0x16 + (0x0a - 0x16) * t); b = int(0x5e + (0x2a - 0x5e) * t)
            d.line([(0, y), (size, y)], fill=(r, g, b, 255))
        import random
        random.seed(7)
        for _ in range(int(size / 4)):
            x, y = random.randrange(size), random.randrange(int(size * .72))
            rr = max(1, size // 190)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 255, 255, 210))
        if os.path.exists(star_p):
            st = Image.open(star_p).convert("RGBA")
            sw = int(size * .66)
            st = st.resize((sw, int(st.size[1] * sw / float(st.size[0]))), Image.LANCZOS)
            base.alpha_composite(st, ((size - st.size[0]) // 2, (size - st.size[1]) // 2))
        # 圆角
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * .22), fill=255)
        out = Image.new("RGB", (size, size), (22, 13, 51))
        out.paste(base.convert("RGB"), (0, 0), mask)
        out.save(os.path.join(AST, "icon-%d.png" % size), optimize=True)
    # maskable（内容居中留边）
    src = Image.open(os.path.join(AST, "icon-512.png")).convert("RGB")
    m = Image.new("RGB", (512, 512), (22, 13, 51))
    s = src.resize((384, 384), Image.LANCZOS)
    m.paste(s, (64, 64))
    m.save(os.path.join(AST, "icon-maskable-512.png"), optimize=True)


def sizeof(d):
    t = 0
    for root, _, fs in os.walk(d):
        for f in fs:
            t += os.path.getsize(os.path.join(root, f))
    return t


if __name__ == "__main__":
    # 注意：角色不再由本脚本生成。委托方指定改用 D:/ClaudeCode/kidmath/assets/char，
    # 由 tools/import_chars.py 导入 —— 这里跑一遍会把它们覆盖回 AI 生成版，所以关掉。
    c, cm = ([], [])
    p, pm = do_transparent(PROPS, os.path.join(AST, "props"), 256, 256)
    b, bm = do_bg(BGS, os.path.join(AST, "bg"))
    do_bg(BGS, os.path.join(AST, "bgthumb"), width=512, quality=78)   # 地图卡专用小图
    print("chars (跳过，见 tools/import_chars.py)  props %d/%d  bg %d/%d" % (len(p), len(PROPS), len(b), len(BGS)))
    if cm or pm or bm:
        print("MISSING:", " ".join(cm + pm + bm))
    if os.path.exists(os.path.join(AST, "props", "star.png")):
        make_icons(); print("icons ok")
    for sub in ("chars", "thumbs", "props", "bg"):
        d = os.path.join(AST, sub)
        if os.path.isdir(d):
            print("  %-7s %6.1f KB  (%d files)" % (sub, sizeof(d) / 1024.0, len(os.listdir(d))))
    print("assets total %.1f KB" % (sizeof(AST) / 1024.0))
