# -*- coding: utf-8 -*-
"""线上冒烟：对正式 URL 做走查 + 断网测试 + 重定向/HTTPS 检查。
用法: python tests/test_live.py https://edliu1105.github.io/star-math/ [--browser webkit]"""
import sys, os, time, argparse, urllib.request, ssl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from playwright.sync_api import sync_playwright
import test_app as TA

ap = argparse.ArgumentParser()
ap.add_argument("url")
ap.add_argument("--browser", default="chromium")
a = ap.parse_args()
BASE = a.url.rstrip("/") + "/"
SHOTS = os.path.join(ROOT, "shots", "live")
os.makedirs(SHOTS, exist_ok=True)
FAILS, PASSES = [], []


def check(c, m):
    (PASSES if c else FAILS).append(m)
    print(("  [OK] " if c else "  [FAIL] ") + m)


print("=" * 60)
print("线上冒烟: %s  [%s]" % (BASE, a.browser))
print("=" * 60)

# --- 1. HTTP 层：200 / HTTPS / 无重定向到个人域名 ---
print("\n=== 1. HTTP ===")
for path in ("", "index.html", "manifest.webmanifest", "sw.js", "assets/icon-192.png"):
    u = BASE + path
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25, context=ssl.create_default_context()) as r:
            final = r.geturl()
            check(r.status == 200, "%-24s -> %d" % (path or "/", r.status))
            check(final.startswith("https://"), "%-24s 最终地址是 HTTPS" % (path or "/"))
            check("behindthepixels" not in final,
                  "%-24s 没有被重定向到个人域名（final=%s）" % (path or "/", final))
    except Exception as e:
        check(False, "%-24s 请求失败: %s" % (path or "/", str(e)[:90]))

# --- 2. 浏览器走查 ---
print("\n=== 2. 走查 ===")
with sync_playwright() as p:
    b = getattr(p, a.browser).launch(headless=True)
    c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True, service_workers="allow")
    c.add_init_script(TA.INIT)
    pg = c.new_page()
    errs = []
    pg.on("console", lambda m: errs.append("console.%s: %s" % (m.type, m.text)) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
    pg.on("requestfailed", lambda r: errs.append("requestfailed: %s" % r.url))

    t0 = time.time()
    pg.goto(BASE, wait_until="load", timeout=45000)
    pg.wait_for_function("window.__ready===true", timeout=25000)
    check(True, "首屏就绪 %.1fs" % (time.time() - t0))
    pg.click("#startBtn", force=True)
    pg.wait_for_selector("#map.on", timeout=8000)
    check(True, "入口按钮进入星空地图")
    pg.screenshot(path=os.path.join(SHOTS, "live-map.png"))

    reg = pg.evaluate("""async ()=>{
      if(!('serviceWorker' in navigator)) return 'no-sw';
      const r = await navigator.serviceWorker.ready.catch(()=>null);
      return r ? (r.active ? 'active' : 'ready') : 'none';
    }""")
    check(reg in ("active", "ready"), "Service Worker 注册成功（%s）" % reg)

    # 解锁全部世界并各玩一关，同时把素材灌进缓存
    TA.set_level(pg, 2)
    pg.reload(); pg.wait_for_function("window.__ready===true", timeout=25000)
    pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on", timeout=8000)
    for w in ("peppa", "paw", "bluey", "hulu", "aveng", "monkey"):
        TA.enter_world(pg, w)
        got = TA.play_session(pg, w, rounds=2, timeout_s=110)
        check(got >= 2, "线上 %s：完成 %d/2 轮" % (w, got))
        pg.screenshot(path=os.path.join(SHOTS, "live-%s.png" % w))
        if pg.query_selector("#stage.on"):
            pg.click("#homeBtn", force=True)
        pg.wait_for_selector("#map.on", timeout=10000)
    check(len(errs) == 0, "线上零 console error / pageerror / 404（%s）" % errs[:3])

    # --- 3. 断网 ---
    print("\n=== 3. 断网离线 ===")
    pg.wait_for_timeout(1500)
    c.set_offline(True)
    pg.reload()
    pg.wait_for_function("window.__ready===true", timeout=25000)
    pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on", timeout=8000)
    check(True, "断网后仍能从缓存启动")
    TA.enter_world(pg, "peppa")
    pg.wait_for_timeout(2500)
    imgs = pg.evaluate("""()=>{const im=[...document.querySelectorAll('#play img, #sceneBg img')];
      return im.length>0 && im.every(x=>x.complete && x.naturalWidth>0);}""")
    check(imgs, "断网后素材从缓存正常显示")
    got = TA.play_session(pg, "peppa", rounds=2, timeout_s=70)
    check(got >= 2, "断网后仍可正常游玩（%d/2 轮）" % got)
    pg.screenshot(path=os.path.join(SHOTS, "live-offline.png"))
    c.set_offline(False)
    b.close()

print("\n" + "=" * 60)
print("通过 %d  失败 %d" % (len(PASSES), len(FAILS)))
for f in FAILS:
    print("  ✗ " + f)
print("截图: " + SHOTS)
sys.exit(1 if FAILS else 0)
