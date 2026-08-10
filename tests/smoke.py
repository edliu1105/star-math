# -*- coding: utf-8 -*-
"""快速视觉冒烟：进入每个世界截一张图，打印 console error。"""
import sys, os, time, threading, functools, http.server, socketserver, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
PORT = 8897
from playwright.sync_api import sync_playwright
from test_app import INIT, set_level

ap = argparse.ArgumentParser()
ap.add_argument("--lv", type=int, default=1)
ap.add_argument("--browser", default="chromium")
ap.add_argument("--portrait", action="store_true")
ap.add_argument("--tag", default="smoke")
ap.add_argument("--play", action="store_true", help="每个世界先玩一轮再截图")
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

SHOTS = os.path.join(ROOT, "shots")
os.makedirs(SHOTS, exist_ok=True)
errs = []
with sync_playwright() as p:
    b = getattr(p, a.browser).launch(headless=True)
    vp = {"width": 820, "height": 1180} if a.portrait else {"width": 1180, "height": 820}
    c = b.new_context(viewport=vp, has_touch=True)
    c.add_init_script(INIT)
    pg = c.new_page()
    pg.on("console", lambda m: errs.append("console.%s: %s" % (m.type, m.text)) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
    pg.on("requestfailed", lambda r: errs.append("404: %s" % r.url))
    pg.goto("http://127.0.0.1:%d/index.html" % PORT)
    pg.wait_for_function("window.__ready===true", timeout=15000)
    set_level(pg, a.lv)
    pg.reload(); pg.wait_for_function("window.__ready===true")
    pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on")
    pg.wait_for_timeout(700)
    pg.screenshot(path=os.path.join(SHOTS, "%s-map.png" % a.tag))
    for w in ("peppa", "paw", "bluey", "hulu", "aveng", "monkey"):
        pg.click('.world[data-w="%s"]' % w, force=True)
        pg.wait_for_selector("#stage.on", timeout=8000)
        pg.wait_for_function("!document.querySelector('#busy').classList.contains('on')", timeout=15000)
        if w == "peppa":
            pg.wait_for_timeout(2100)
            pg.screenshot(path=os.path.join(SHOTS, "%s-peppa-flash.png" % a.tag))
            pg.wait_for_timeout(2100)
        else:
            pg.wait_for_timeout(4200)
        pg.screenshot(path=os.path.join(SHOTS, "%s-%s.png" % (a.tag, w)))
        over = pg.evaluate("""()=>{const d=document.documentElement,b=document.body;
          return Math.max(d.scrollHeight-d.clientHeight,b.scrollHeight-b.clientHeight,d.scrollWidth-d.clientWidth);}""")
        # 检查是否有物体溢出计数区
        ov = pg.evaluate("""()=>{
          const out=[];
          document.querySelectorAll('#play .cobj, .zbot .card, .zbot .bigbtn').forEach(e=>{
            const r=e.getBoundingClientRect();
            if(r.left< -2||r.top< -2||r.right>innerWidth+2||r.bottom>innerHeight+2)
              out.push(e.className+' '+Math.round(r.left)+','+Math.round(r.top)+','+Math.round(r.right)+','+Math.round(r.bottom));
          });
          return out;}""")
        print("%-7s objs=%-3s scroll=%s outOfView=%s  q=%s" % (
            w, pg.evaluate("document.querySelectorAll('#play .cobj').length"), over,
            (ov[:2] if ov else "-"), pg.evaluate("window.__q")))
        pg.click("#homeBtn", force=True); pg.wait_for_selector("#map.on", timeout=6000)
    b.close()
httpd.shutdown()
print("\nERRORS: %d" % len(errs))
for e in errs[:12]:
    print("  ", e)
