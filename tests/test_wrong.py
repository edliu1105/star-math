# -*- coding: utf-8 -*-
"""答错路径专项：六个世界 × 两个难度，每轮都故意先答错，
   验证 (a) 零 console error / pageerror，(b) 纠错→复测→最终一定能拿到星星推进。
用法: python tests/test_wrong.py [--browser webkit|chromium]"""
import sys, os, time, argparse, threading, functools, http.server, socketserver

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
PORT = int(os.environ.get("KM_PORT", "8893"))
from playwright.sync_api import sync_playwright
import test_app as TA

ap = argparse.ArgumentParser()
ap.add_argument("--browser", default="chromium")
a = ap.parse_args()

h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
class Q(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    def handle_error(self, *x): pass
class S(h.func):
    def log_message(self, *x): pass
httpd = Q(("127.0.0.1", PORT), functools.partial(S, directory=ROOT))
threading.Thread(target=httpd.serve_forever, daemon=True).start()

SHOTS = os.path.join(ROOT, "shots", "wrong")
os.makedirs(SHOTS, exist_ok=True)
FAILS, PASSES = [], []


def check(c, m):
    (PASSES if c else FAILS).append(m)
    print(("  [OK] " if c else "  [FAIL] ") + m)


with sync_playwright() as p:
    b = getattr(p, a.browser).launch(headless=True)
    for lv in (2, 4):
        print("\n=== 故意答错 · 难度 L%d (%s) ===" % (lv, a.browser))
        c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
        c.add_init_script(TA.INIT)
        pg = c.new_page()
        errs = []
        pg.on("console", lambda m: errs.append("console.%s: %s" % (m.type, m.text)) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
        pg.goto("http://127.0.0.1:%d/index.html" % PORT)
        pg.wait_for_function("window.__ready===true", timeout=15000)
        TA.set_level(pg, lv)
        pg.reload(); pg.wait_for_function("window.__ready===true")
        pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on")
        for w in ("peppa", "paw", "bluey", "hulu", "aveng", "monkey"):
            TA.enter_world(pg, w)
            pg.wait_for_function("window.__q != null", timeout=15000)
            t0 = time.time()
            wrongs = 0
            guard = 0
            while time.time() - t0 < 170 and guard < 40:
                guard += 1
                if not pg.query_selector("#stage.on") or pg.query_selector("#cheer.on"):
                    break
                filled = pg.evaluate("document.querySelectorAll('#dots i.f').length")
                if filled >= 2:
                    break
                qn = pg.evaluate("window.__qn||0")
                try:
                    TA.solve_round(pg, w, deliberately_wrong=True); wrongs += 1
                except Exception:
                    pg.wait_for_timeout(700); continue
                try:
                    pg.wait_for_function(
                        "(n)=>(window.__qn||0)>n || document.querySelector('#cheer.on')!==null",
                        arg=qn, timeout=26000)
                except Exception:
                    pg.wait_for_timeout(700)
            got = pg.evaluate("document.querySelectorAll('#dots i.f').length")
            check(got >= 2, "L%d %s：一直答错也能在 %d 次内拿到 2 颗星并推进（实际 %d 星）" % (lv, w, wrongs, got))
            pg.screenshot(path=os.path.join(SHOTS, "L%d-%s.png" % (lv, w)))
            if pg.query_selector("#stage.on"):
                pg.click("#homeBtn", force=True)
            pg.wait_for_selector("#map.on", timeout=8000)
        check(len(errs) == 0, "L%d 答错路径零 console error（%s）" % (lv, errs[:3]))
        c.close()
    b.close()
httpd.shutdown()

print("\n通过 %d  失败 %d" % (len(PASSES), len(FAILS)))
for f in FAILS:
    print("  ✗ " + f)
sys.exit(1 if FAILS else 0)
