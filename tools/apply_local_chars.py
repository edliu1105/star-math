# -*- coding: utf-8 -*-
"""把 incoming/ 里委托方自己提供的角色图接进本地这份应用。

处理流程（每张图自动挑最合适的一档）：
  A. 图片本身已有真实透明通道 → 直接用
  B. 四角泛洪抠图        → 适合白底/浅色纯底
  C. rembg(u2net) 主体分割 → 适合整幅带背景的插画（装了才可用）
  D. OpenCV GrabCut      → rembg 不可用时的兜底
然后统一：去边缘白晕 → 自动裁切 → 缩放到 384px（缩略图 160px）→ 256 色量化。

用法：
  python tools/apply_local_chars.py            应用
  python tools/apply_local_chars.py --revert   还原
  python tools/apply_local_chars.py --only ironman,spider   只处理指定的几个

注意：这个脚本只改本地 assets/，incoming/ 不入 git。
"""
import io, os, sys, shutil, argparse
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(ROOT, "incoming")
CHARS = os.path.join(ROOT, "assets", "chars")
THUMBS = os.path.join(ROOT, "assets", "thumbs")
BEFORE = os.path.join(ROOT, "raw", "chars_before_local")

# incoming 里的文件名 -> 应用内部名（黑豹默认顶掉浩克，可用 --panther-as 改）
NAMES = ["ironman", "spider", "spiderblack", "cap", "thor", "hawkeye", "hulkman", "widow", "blackpanther"]
# 委托方给的文件名不一定和内部名一致，按优先级找别名（越靠前越优先）
ALIAS = {
    "ironman":     ["newironman", "ironman", "iornman"],
    "spider":      ["spider", "spiderman"],
    "spiderblack": ["spiderblack", "miles"],
    "cap":         ["cap", "captain", "captainamerica"],
    "thor":        ["thor"],
    "hawkeye":     ["hawkeye"],
    "hulkman":     ["hulkman", "hulk"],
    "widow":       ["widow", "blackwidow"],
    "blackpanther":["blackpanther", "panther"],
}
EXTS = (".png", ".jpg", ".jpeg", ".webp")


def find(name):
    for stem in ALIAS.get(name, [name]):
        for e in EXTS:
            p = os.path.join(IN, stem + e)
            if os.path.exists(p):
                return p
    return None


def has_alpha(im):
    if im.mode != "RGBA":
        return False
    a = np.array(im.getchannel("A"))
    return (a < 250).mean() > 0.03


def cut_floodfill(im, fuzz=38):
    """四角泛洪：只删与边缘连通、且与角落颜色接近的区域。适合纯色底。"""
    rgb = np.array(im.convert("RGB")).astype(np.int16)
    h, w = rgb.shape[:2]
    corners = [rgb[1, 1], rgb[1, w - 2], rgb[h - 2, 1], rgb[h - 2, w - 2]]
    base = np.median(np.stack(corners), axis=0)
    dist = np.abs(rgb - base).max(axis=2)
    seed = dist <= fuzz
    # 从边缘开始做连通域扩散
    try:
        import cv2
        m = (seed.astype(np.uint8) * 255)
        num, lab = cv2.connectedComponents(m, connectivity=4)
        edge = set(lab[0, :].tolist()) | set(lab[-1, :].tolist()) | \
               set(lab[:, 0].tolist()) | set(lab[:, -1].tolist())
        edge.discard(0)
        bg = np.isin(lab, list(edge))
    except Exception:
        bg = seed
    out = im.convert("RGBA")
    a = np.array(out.getchannel("A"))
    a[bg] = 0
    out.putalpha(Image.fromarray(a))
    return out, bg.mean()


def cut_rembg(im):
    from rembg import remove
    return remove(im.convert("RGBA"))


def cut_grabcut(im, inset=0.06):
    import cv2
    rgb = np.array(im.convert("RGB"))
    h, w = rgb.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    rect = (int(w * inset), int(h * inset), int(w * (1 - 2 * inset)), int(h * (1 - 2 * inset)))
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(rgb, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    out = im.convert("RGBA")
    a = np.array(out.getchannel("A"))
    a[fg == 0] = 0
    out.putalpha(Image.fromarray(a))
    return out


def dehalo(im, rounds=2):
    im = im.convert("RGBA")
    for _ in range(rounds):
        a = im.getchannel("A")
        near = a.filter(ImageFilter.MinFilter(3))
        arr = np.array(im)
        an, aa = np.array(near), arr[:, :, 3]
        light = (arr[:, :, 0] > 232) & (arr[:, :, 1] > 232) & (arr[:, :, 2] > 232)
        kill = (aa > 0) & (an < 250) & light
        if not kill.any():
            break
        arr[:, :, 3][kill] = 0
        im = Image.fromarray(arr, "RGBA")
    return im


def autocrop(im, pad=0.015):
    bbox = im.getchannel("A").getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    w, h = im.size
    p = int(max(w, h) * pad)
    return im.crop((max(0, l - p), max(0, t - p), min(w, r + p), min(h, b + p)))


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


def process(path):
    im = Image.open(path)
    im = im.convert("RGBA")
    how = ""
    if has_alpha(im):
        how = "自带透明通道"
    else:
        cut, ratio = cut_floodfill(im)
        if ratio > 0.12:                      # 泛洪确实去掉了一大片 → 是纯色底
            im, how = cut, "四角泛洪 (去除 %.0f%%)" % (ratio * 100)
        else:
            try:
                im, how = cut_rembg(im), "rembg 主体分割"
            except Exception:
                try:
                    im, how = cut_grabcut(im), "GrabCut 主体分割"
                except Exception as e:
                    how = "抠图失败(%s)，按原图使用" % str(e)[:40]
    im = dehalo(im)
    im = autocrop(im)
    return im, how


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--panther-as", default="blackpanther",
                    help="黑豹用哪个内部名（默认就叫 blackpanther，作为第 9 个复联角色）")
    a = ap.parse_args()

    if a.revert:
        if not os.path.isdir(BEFORE):
            print("没有备份可还原"); sys.exit(1)
        k = 0
        for f in os.listdir(BEFORE):
            if f.startswith("thumb_"):
                shutil.copy2(os.path.join(BEFORE, f), os.path.join(THUMBS, f[6:])); k += 1
            else:
                shutil.copy2(os.path.join(BEFORE, f), os.path.join(CHARS, f)); k += 1
        mk = os.path.join(ROOT, "LOCAL_OVERRIDE.txt")
        if os.path.exists(mk):
            os.remove(mk)
        print("已还原 %d 个文件，LOCAL_OVERRIDE.txt 已移除" % k); sys.exit(0)

    os.makedirs(BEFORE, exist_ok=True)
    only = set(x.strip() for x in a.only.split(",") if x.strip())
    todo = []
    for nm in NAMES:
        p = find(nm)
        if not p:
            continue
        dst = nm
        if nm == "blackpanther":
            if a.panther_as == "none":
                continue
            dst = a.panther_as
        if only and dst not in only and nm not in only:
            continue
        todo.append((dst, p))

    if not todo:
        print("incoming/ 里没有找到可用的图。请先按 incoming/README.txt 放好文件。")
        sys.exit(1)

    for dst, p in todo:
        for d, pre in ((CHARS, ""), (THUMBS, "thumb_")):
            cur = os.path.join(d, dst + ".png")
            bk = os.path.join(BEFORE, pre + dst + ".png")
            if os.path.exists(cur) and not os.path.exists(bk):
                shutil.copy2(cur, bk)
        im, how = process(p)
        save_png(fit(im, 384), os.path.join(CHARS, dst + ".png"), 256)
        save_png(fit(im, 160), os.path.join(THUMBS, dst + ".png"), 128)
        print("%-12s <- %-22s  %s   最终 %dx%d" %
              (dst, os.path.basename(p), how, *fit(im, 384).size))
    # 关键：这些文件覆盖的就是公开部署路径 assets/chars/。
    # 写一个标记，deploy.sh 见到它会直接拒绝推送，必须先 --revert。
    with io.open(os.path.join(ROOT, "LOCAL_OVERRIDE.txt"), "w", encoding="utf-8") as f:
        f.write("本地素材覆盖生效中，以下文件来自 incoming/（委托方自备，非本仓库产出）：\n")
        for dst2, src2 in todo:
            f.write("  %s  <-  %s\n" % (dst2, os.path.basename(src2)))
        f.write("\n公开部署前必须先运行：python tools/apply_local_chars.py --revert\n")
    print("\n完成 %d 个。用 shots/sheet-chars.png 目检（跑 python tools/contact_sheet.py）。" % len(todo))
    print("已写 LOCAL_OVERRIDE.txt —— 在它存在期间 tools/deploy.sh 会拒绝推送。")
    print("还原：python tools/apply_local_chars.py --revert")
