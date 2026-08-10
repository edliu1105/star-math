# -*- coding: utf-8 -*-
"""按委托方指定，用 D:/ClaudeCode/kidmath/assets/char 的角色替换本项目生成的角色。
   这些图已经是 512px、边缘干净的成品，所以不做 dehalo（避免误伤），
   只做自动裁切 + 缩放 + 量化，产出 assets/chars(384px) 与 assets/thumbs(160px)。"""
import io, os, shutil
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = r"D:/ClaudeCode/kidmath/assets/char"
CHARS = os.path.join(ROOT, "assets", "chars")
THUMBS = os.path.join(ROOT, "assets", "thumbs")
BACKUP = os.path.join(ROOT, "raw", "gen_chars_backup")

# 本项目命名 <- 来源文件名
MAP = {
    "wukong": "wukong", "tangseng": "tangseng", "bajie": "bajie",
    "shaseng": "wujing", "bailongma": "bailongma",
    "hulu1": "hulu1", "hulu2": "hulu2", "hulu3": "hulu3", "hulu4": "hulu4",
    "hulu5": "hulu5", "hulu6": "hulu6", "hulu7": "hulu7",
    "yeye": "yeye", "shejing": "shejing", "xiezijing": "xiezijing",
    "ironman": "ironman", "cap": "cap", "thor": "thor", "hulkman": "hulk",
    "widow": "blackwidow", "hawkeye": "hawkeye",
    "spider": "spiderman", "spiderblack": "miles",
    "ryder": "ryder", "chase": "chase", "marshall": "marshall", "skye": "skye",
    "rubble": "rubble", "zuma": "zuma", "rocky": "rocky",
    "bluey": "bluey", "bingo": "bingo", "bandit": "bandit", "chilli": "chilli",
    "peppa": "peppa", "george": "george", "daddypig": "papa", "mummypig": "mama",
    # blackpanther 无来源，先用 AI 占位图，委托方的官方图放 incoming/ 后覆盖
}


def autocrop(im, pad_ratio=0.015):
    a = im.getchannel("A")
    bbox = a.getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    w, h = im.size
    pad = int(max(w, h) * pad_ratio)
    return im.crop((max(0, l - pad), max(0, t - pad), min(w, r + pad), min(h, b + pad)))


def fit(im, longest):
    w, h = im.size
    if max(w, h) <= longest:
        return im
    s = longest / float(max(w, h))
    return im.resize((max(1, int(round(w * s))), max(1, int(round(h * s)))), Image.LANCZOS)


def save_png(im, path, colors=256):
    im = im.convert("RGBA")
    try:
        im.quantize(colors=colors, method=Image.FASTOCTREE).save(path, optimize=True)
    except Exception:
        im.save(path, optimize=True)


if __name__ == "__main__":
    os.makedirs(BACKUP, exist_ok=True)
    missing, done = [], []
    for dst, src in MAP.items():
        p = os.path.join(SRC, src + ".png")
        if not os.path.exists(p):
            missing.append("%s(<-%s)" % (dst, src)); continue
        old = os.path.join(CHARS, dst + ".png")
        if os.path.exists(old) and not os.path.exists(os.path.join(BACKUP, dst + ".png")):
            shutil.copy2(old, os.path.join(BACKUP, dst + ".png"))
        im = Image.open(p).convert("RGBA")
        im = autocrop(im)
        save_png(fit(im, 384), os.path.join(CHARS, dst + ".png"), 256)
        save_png(fit(im, 160), os.path.join(THUMBS, dst + ".png"), 128)
        done.append(dst)
    print("导入 %d / %d" % (len(done), len(MAP)))
    if missing:
        print("缺失:", " ".join(missing))
    def sz(d):
        return sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d)) / 1024.0
    print("chars %.1f KB (%d)  thumbs %.1f KB (%d)" %
          (sz(CHARS), len(os.listdir(CHARS)), sz(THUMBS), len(os.listdir(THUMBS))))
