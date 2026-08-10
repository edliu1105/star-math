# -*- coding: utf-8 -*-
"""单世界单难度深度调试：打印每一步的题目、DOM、语音时间线。
用法: python tests/debug_world.py hulu 4"""
import sys, os, time, threading, functools, http.server, socketserver

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
PORT = 8896
from playwright.sync_api import sync_playwright
import test_app as TA

W = sys.argv[1] if len(sys.argv) > 1 else "hulu"
LV = int(sys.argv[2]) if len(sys.argv) > 2 else 4

h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
class Q(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    def handle_error(self, *x): pass
class S(h.func):
    def log_message(self, *x): pass
httpd = Q(("127.0.0.1", PORT), functools.partial(S, directory=ROOT))
threading.Thread(target=httpd.serve_forever, daemon=True).start()

errs = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
    c.add_init_script(TA.INIT)
    pg = c.new_page()
    pg.on("console", lambda m: errs.append("console.%s: %s" % (m.type, m.text)) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
    pg.goto("http://127.0.0.1:%d/index.html" % PORT)
    pg.wait_for_function("window.__ready===true", timeout=15000)
    TA.set_level(pg, LV)
    pg.reload(); pg.wait_for_function("window.__ready===true")
    pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on")
    TA.enter_world(pg, W)
    pg.evaluate("window.__spk=[]")

    t0 = time.time()
    for step in range(14):
        if not pg.query_selector("#stage.on"):
            print("  << 已离开舞台"); break
        if pg.query_selector("#cheer.on"):
            print("  << 通关庆祝"); break
        filled = pg.evaluate("document.querySelectorAll('#dots i.f').length")
        info = pg.evaluate("""()=>({
          q: window.__q,
          zones: document.querySelectorAll('.dropzone').length,
          cobj: document.querySelectorAll('#play .cobj').length,
          cards: document.querySelectorAll('.zbot .card').length,
          btn: (()=>{const b=document.querySelector('.zbot .bigbtn'); return b?(b.disabled?'disabled':'ready'):'none';})(),
          slots: document.querySelectorAll('.zbot > div > div').length
        })""")
        print("[%5.1fs] step%-2d 星=%d %s" % (time.time() - t0, step, filled, info))
        info_qn = pg.evaluate("window.__qn||0")
        try:
            TA.solve_round(pg, W)
        except Exception as e:
            print("      solve 异常: %s" % str(e).split("\n")[0][:120])
            pg.wait_for_timeout(900); continue
        try:
            pg.wait_for_function("(n)=>(window.__qn||0)>n || document.querySelector('#cheer.on')!==null",
                                 arg=info_qn, timeout=24000)
            got = pg.evaluate("document.querySelectorAll('#dots i.f').length")
            print("      -> %s (%.1fs)" % ("得星" if got > filled else "未得星→复测", time.time() - t0))
        except Exception:
            print("      -> 超时")
            pg.wait_for_timeout(800)

    print("\n--- 语音时间线 ---")
    for e in pg.evaluate("window.__spk"):
        print("  %6dms  overlap=%-5s sinceCancel=%-6s %s" % (e["t"], e["overlap"], e["since_cancel"], e["text"][:52]))
    b.close()
httpd.shutdown()
print("\nERRORS:", len(errs))
for e in errs[:10]:
    print("  ", e)
