# -*- coding: utf-8 -*-
"""v6 发布回归：六世界 × L1-L4 全流程（test_app A 段独立跑，B 段旧断言已废弃）"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_app as TA
from playwright.sync_api import sync_playwright

httpd = TA.serve(); time.sleep(0.4)
rc = 1
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for lv in (1, 2, 3, 4):
                ctxb = browser.new_context(viewport={"width": 1180, "height": 820},
                                           has_touch=True, is_mobile=False)
                ctxb.add_init_script(TA.INIT)
                page = ctxb.new_page(); C = TA.Ctx(page)
                page.goto(TA.BASE)
                page.wait_for_function("window.__ready === true", timeout=15000)
                TA.set_level(page, lv); page.reload()
                page.wait_for_function("window.__ready === true", timeout=15000)
                page.click("#startBtn", force=True)
                page.wait_for_selector("#map.on", timeout=6000)
                for w in ("peppa", "paw", "bluey", "hulu", "aveng", "monkey"):
                    page.evaluate("window.__spk=[]")
                    TA.enter_world(page, w)
                    got = TA.play_session(page, w, rounds=5, timeout_s=170)
                    ok = got >= 4
                    TA.check(ok, "L%d %s：5 轮至少完成 4 轮（实际 %d）" % (lv, w, got))
                    print("  [%s] L%d %s (%d/5)" % ("OK" if ok else "FAIL", lv, w, got), flush=True)
                    TA.assert_speech(page, "L%d %s" % (lv, w))
                    if page.query_selector("#stage.on"):
                        page.click("#homeBtn", force=True)
                    page.wait_for_selector("#map.on", timeout=8000)
                TA.check(len(C.errors) == 0, "L%d：零 console error / pageerror（%s）" % (lv, C.errors[:3]))
                ctxb.close()
        finally:
            browser.close()
finally:
    httpd.shutdown()
print("FAILS: %d" % len(TA.FAILS))
for f in TA.FAILS:
    print("  x " + f)
print("errors: none" if not TA.FAILS else "errors: see above")
rc = 1 if TA.FAILS else 0
sys.exit(rc)
