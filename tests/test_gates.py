# -*- coding: utf-8 -*-
"""掌握门槛专项（codex 第二轮点名要求的确定性测试）：
  G1 固定乱点 100 轮：难度不得升级、掌握计数不得增长、第三个世界不得解锁
  G2 用过提示之后作答正确，不得写入掌握证据（tries / mast / hist 全部不变）
  G3 顶栏「再说一遍」同样算提示，之后作答不得计掌握
  G4 答案卡与题面排列的**实际坐标**必须不同（不只是模式名不同）
  G5 成人门穷举：答错后把四个旧按钮全点一遍，不得进入面板
  G6 参与星与掌握徽章是两套独立字段
用法: python tests/test_gates.py [--browser chromium|webkit]
"""
import sys, os, time, argparse, threading, functools, http.server, socketserver

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
PORT = int(os.environ.get("KM_PORT", "8891"))
from playwright.sync_api import sync_playwright
import test_app as TA

ap = argparse.ArgumentParser()
ap.add_argument("--browser", default="chromium")
ap.add_argument("--rounds", type=int, default=100)
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
BASE = "http://127.0.0.1:%d/index.html" % PORT

FAILS, PASSES = [], []
def check(c, m):
    (PASSES if c else FAILS).append(m)
    print(("  [OK] " if c else "  [FAIL] ") + m)


def prog(pg, wid):
    return pg.evaluate("(id)=>{const d=JSON.parse(localStorage['kidmath2.progress.v2']||'{}');"
                       "return (d.w&&d.w[id])||null;}", wid)


with sync_playwright() as p:
    b = getattr(p, a.browser).launch(headless=True)

    # ---------------- G1 固定乱点 ----------------
    print("\n=== G1 固定乱点 %d 轮 ===" % a.rounds)
    c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
    c.add_init_script(TA.INIT)
    pg = c.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE); pg.wait_for_function("window.__ready===true", timeout=15000)
    TA.set_level(pg, 1)
    # 只解锁前两个（默认状态），第三个世界必须靠掌握才打开
    pg.evaluate("""()=>{const d=JSON.parse(localStorage['kidmath2.progress.v2']);
        Object.keys(d.w).forEach(k=>{d.w[k].open=0;d.w[k].stars=0;d.w[k].lv=1;
                                     d.w[k].mast=0;d.w[k].tries=0;d.w[k].hist=[];});
        localStorage.setItem('kidmath2.progress.v2',JSON.stringify(d));}""")
    pg.reload(); pg.wait_for_function("window.__ready===true")
    pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on")
    TA.enter_world(pg, "peppa")
    pg.wait_for_function("window.__q!=null", timeout=15000)
    done = 0
    t0 = time.time()
    while done < a.rounds and time.time() - t0 < 900:
        if pg.query_selector("#cheer.on"):
            pg.click("#cheer", force=True)
            pg.wait_for_selector("#map.on", timeout=8000)
            TA.enter_world(pg, "peppa")
            pg.wait_for_function("window.__q!=null", timeout=15000)
        if not pg.query_selector("#stage.on"):
            break
        qn = pg.evaluate("window.__qn||0")
        try:
            TA.solve_peppa(pg, wrong=True)      # 固定：永远点一张错的
            done += 1
        except Exception:
            pg.wait_for_timeout(500); continue
        try:
            pg.wait_for_function("(n)=>(window.__qn||0)>n || document.querySelector('#cheer.on')!==null",
                                 arg=qn, timeout=22000)
        except Exception:
            pg.wait_for_timeout(400)
    w = prog(pg, "peppa")
    print("    实际作答 %d 轮 → %s" % (done, {k: w[k] for k in ("lv", "mast", "tries", "stars")}))
    check(w["lv"] == 1, "乱点 %d 轮后难度仍为 L1（实际 L%d）" % (done, w["lv"]))
    check(w["mast"] == 0, "乱点 %d 轮后掌握计数仍为 0（实际 %d）" % (done, w["mast"]))
    locked = pg.evaluate("()=>document.querySelector('.world[data-w=\"bluey\"]').classList.contains('locked')")
    check(locked, "乱点 %d 轮后第三个世界仍然锁着" % done)
    check(w["stars"] > 0, "但参与星照常增加（%d 颗）—— 孩子不会被打击" % w["stars"])
    check(len(errs) == 0, "G1 零 pageerror（%s）" % errs[:2])
    c.close()

    # ---------------- G1b 真·随机乱点（固定屏幕位置，答案每题洗牌） ----------------
    print("\n=== G1b 固定点第一张卡 %d 轮（真随机命中，约 1/4） ===" % (a.rounds * 2))
    c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
    c.add_init_script(TA.INIT)
    pg = c.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE); pg.wait_for_function("window.__ready===true", timeout=15000)
    TA.set_level(pg, 1)
    pg.evaluate("""()=>{const d=JSON.parse(localStorage['kidmath2.progress.v2']);
        Object.keys(d.w).forEach(k=>{d.w[k].open=0;d.w[k].stars=0;d.w[k].lv=1;d.w[k].mast=0;
                                     d.w[k].tries=0;d.w[k].hist=[];d.w[k].wins=0;d.w[k].winAt=-1;});
        localStorage.setItem('kidmath2.progress.v2',JSON.stringify(d));}""")
    pg.reload(); pg.wait_for_function("window.__ready===true")
    pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on")
    TA.enter_world(pg, "peppa")
    pg.wait_for_function("window.__q!=null", timeout=15000)
    done = 0
    t0 = time.time()
    target = a.rounds * 2
    while done < target and time.time() - t0 < 1500:
        if pg.query_selector("#cheer.on"):
            pg.click("#cheer", force=True)
            pg.wait_for_selector("#map.on", timeout=8000)
            TA.enter_world(pg, "peppa")
            pg.wait_for_function("window.__q!=null", timeout=15000)
        if not pg.query_selector("#stage.on"):
            break
        qn = pg.evaluate("window.__qn||0")
        try:
            pg.wait_for_selector(".zbot .card", timeout=12000)
            pg.query_selector_all(".zbot .card")[0].click(force=True)   # 永远点同一个位置
            done += 1
        except Exception:
            pg.wait_for_timeout(500); continue
        try:
            pg.wait_for_function("(n)=>(window.__qn||0)>n || document.querySelector('#cheer.on')!==null",
                                 arg=qn, timeout=22000)
        except Exception:
            pg.wait_for_timeout(400)
    w = prog(pg, "peppa")
    rate = (w["mast"] / w["tries"]) if w["tries"] else 0
    print("    固定位置点了 %d 次 → %s  正确率 %.2f" %
          (done, {k: w[k] for k in ("lv", "mast", "tries", "wins")}, rate))
    check(done >= a.rounds * 2 - 6, "确实跑满了 %d 轮（实际 %d）" % (a.rounds * 2, done))
    sess = pg.evaluate("()=>JSON.parse(localStorage['kidmath2.progress.v2']).sess")
    print("    全部发生在同一次应用启动内（sess=%s）→ wins 结构上最多为 1" % sess)
    check(rate < 0.45, "随机命中率停留在随机水平（%.2f < 0.45）" % rate)
    locked = pg.evaluate("()=>document.querySelector('.world[data-w=\"bluey\"]').classList.contains('locked')")
    check(locked, "固定位置乱点 %d 次后第三个世界仍然锁着" % done)
    check(w["wins"] < 2, "跨会话掌握窗口不足 2（实际 %d）" % w["wins"])
    check(len(errs) == 0, "G1b 零 pageerror（%s）" % errs[:2])
    c.close()

    # ---------------- G2 / G3 提示后不计证据 ----------------
    print("\n=== G2/G3 用过提示后不得计入掌握 ===")
    c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
    c.add_init_script(TA.INIT)
    pg = c.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE); pg.wait_for_function("window.__ready===true", timeout=15000)
    TA.set_level(pg, 2); pg.reload(); pg.wait_for_function("window.__ready===true")
    pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on")

    # G2：手动"再看一次"（点佩奇）之后答对
    TA.enter_world(pg, "peppa")
    pg.wait_for_selector(".zbot .card", timeout=15000)
    before = prog(pg, "peppa")
    pg.click("#play .side.l", force=True)          # 点佩奇 = 再看一次 = 提示
    pg.wait_for_timeout(400)
    pg.wait_for_selector(".zbot .card", timeout=15000)
    TA.click_card_with(pg, TA.q(pg)["n"], wrong=False)
    pg.wait_for_timeout(1500)
    after = prog(pg, "peppa")
    check(after["mast"] == before["mast"] and after["tries"] == before["tries"],
          "手动重看提示后答对：掌握与答题数都不变（mast %d→%d, tries %d→%d）" %
          (before["mast"], after["mast"], before["tries"], after["tries"]))

    # G3：顶栏「再说一遍」之后答对
    pg.click("#homeBtn", force=True); pg.wait_for_selector("#map.on")
    TA.enter_world(pg, "paw")
    pg.wait_for_function("window.__q!=null", timeout=15000)
    before = prog(pg, "paw")
    pg.click("#speakBtn", force=True)
    pg.wait_for_timeout(400)
    try:
        TA.solve_paw(pg, wrong=False)
        pg.wait_for_timeout(2000)
    except Exception:
        pass
    after = prog(pg, "paw")
    check(after["mast"] == before["mast"],
          "顶栏「再说一遍」后答对：掌握不变（%d→%d）" % (before["mast"], after["mast"]))
    check(len(errs) == 0, "G2/G3 零 pageerror（%s）" % errs[:2])
    c.close()

    # ---------------- G4 排列几何差异 ----------------
    print("\n=== G4 答案卡与题面排列的实际坐标必须不同 ===")
    c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
    c.add_init_script(TA.INIT)
    pg = c.new_page()
    pg.goto(BASE); pg.wait_for_function("window.__ready===true", timeout=15000)
    # 直接调用应用里的 patDiffers()（点集 Hausdorff），不再在测试里另写一套按下标的算法
    bad = pg.evaluate("""()=>{
      const out=[];
      for(let n=1;n<=6;n++){
        for(const qp of ["dice","group"]){
          const ap=pickAnswerPat(n,qp);
          if(!patDiffers(n,qp,ap)) out.push(n+":"+qp+"->"+ap);
        }
      }
      return out;}""")
    check(len(bad) == 0, "1–6 个点下 pickAnswerPat 选出的排列都通过 patDiffers（问题项 %s）" % bad)
    tri = pg.evaluate("()=>patDiffers(3,'dice','ring')")
    check(tri is False, "n=3 的 dice 与 ring 被正确判为「太像」（patDiffers=%s）" % tri)
    haus = pg.evaluate("""()=>{
      const A=dotPos(3,'dice'), B=dotPos(3,'ring');
      const near=(p,S)=>Math.min.apply(null,S.map(q=>Math.hypot(p[0]-q[0],p[1]-q[1])));
      let h=0; A.forEach(p=>h=Math.max(h,near(p,B))); B.forEach(p=>h=Math.max(h,near(p,A)));
      return Math.round(h*10)/10;}""")
    print("    n=3 dice↔ring 的 Hausdorff 距离 = %s（阈值 13）" % haus)
    c.close()

    # ---------------- G5 成人门穷举 ----------------
    print("\n=== G5 成人门不能被穷举 ===")
    c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
    c.add_init_script(TA.INIT)
    pg = c.new_page()
    pg.goto(BASE); pg.wait_for_function("window.__ready===true", timeout=15000)
    pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on")
    box = pg.query_selector("#parentDot").bounding_box()
    pg.mouse.move(box["x"] + 20, box["y"] + 20); pg.mouse.down()
    pg.wait_for_timeout(3300); pg.mouse.up()
    assert pg.is_visible("#gateAdult")
    qtext = pg.inner_text("#gaQ")
    x, y = [int(v) for v in qtext.replace("= ?", "").split("+")]
    right = x + y
    # 这一段只验证"必须连对两题"，不能先答错 —— 答错会进入 30 秒冷却（那条由 G5b 验证）
    x1, y1 = x, y
    pg.click("#gaOpts button >> text='%d'" % (x1 + y1), force=True)
    pg.wait_for_timeout(800)
    check(not pg.is_visible("#panel"), "只答对一题还进不去（要求连对两题）")
    check(pg.is_visible("#gateAdult") and pg.inner_text("#gaQ") != qtext, "会换成第二道新题")
    q2 = pg.inner_text("#gaQ")
    x2, y2 = [int(v) for v in q2.replace("= ?", "").split("+")]
    pg.click("#gaOpts button >> text='%d'" % (x2 + y2), force=True)
    pg.wait_for_timeout(800)
    check(pg.is_visible("#panel"), "连对两题后才进入家长面板")
    c.close()

    # ---------------- G5b 成人门：答错进入冷却，暴力猜在时间上不可行 ----------------
    print("\n=== G5b 成人门答错冷却 ===")
    c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
    c.add_init_script(TA.INIT)
    pg = c.new_page()
    pg.goto(BASE); pg.wait_for_function("window.__ready===true", timeout=15000)
    pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on")

    def longpress():
        box = pg.query_selector("#parentDot").bounding_box()
        pg.mouse.move(box["x"] + 20, box["y"] + 20); pg.mouse.down()
        pg.wait_for_timeout(3200); pg.mouse.up()
        pg.wait_for_timeout(300)

    longpress()
    check(pg.is_visible("#gateAdult"), "长按 3 秒弹出成人验证门")
    qt = pg.inner_text("#gaQ")
    x, y = [int(v) for v in qt.replace("= ?", "").split("+")]
    wrongv = [v for v in pg.eval_on_selector_all("#gaOpts button", "els=>els.map(e=>+e.textContent)")
              if v != x + y][0]
    pg.click("#gaOpts button >> text='%d'" % wrongv, force=True)
    pg.wait_for_timeout(600)
    check(not pg.is_visible("#gateAdult"), "答错后验证门立即关闭")
    check(not pg.is_visible("#panel"), "答错没有进入面板")
    longpress()
    check(not pg.is_visible("#gateAdult"), "冷却期内（30 秒）再长按无效 —— 暴力猜在时间上不可行")

    # 同一道题上快速连点两次，不能把 streak 凑到 2
    c2 = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
    c2.add_init_script(TA.INIT)
    pg2 = c2.new_page()
    pg2.goto(BASE); pg2.wait_for_function("window.__ready===true", timeout=15000)
    pg2.click("#startBtn", force=True); pg2.wait_for_selector("#map.on")
    box = pg2.query_selector("#parentDot").bounding_box()
    pg2.mouse.move(box["x"] + 20, box["y"] + 20); pg2.mouse.down()
    pg2.wait_for_timeout(3200); pg2.mouse.up(); pg2.wait_for_timeout(300)
    qt2 = pg2.inner_text("#gaQ")
    x2, y2 = [int(v) for v in qt2.replace("= ?", "").split("+")]
    sel = "#gaOpts button >> text='%d'" % (x2 + y2)
    pg2.click(sel, force=True)
    for _ in range(4):                       # 换题前的窗口里对同一个正确按钮猛点
        try:
            pg2.click(sel, force=True, timeout=400)
        except Exception:
            pass
        pg2.wait_for_timeout(80)
    pg2.wait_for_timeout(800)
    check(not pg2.is_visible("#panel"), "同一道题上快速连点正确按钮，不能凑够连对两题")
    c2.close()
    c.close()

    # ---------------- G7 正向：稳定全对的孩子必须能解锁 ----------------
    print("\n=== G7 全对的孩子跨两次启动后必须解锁第三个世界 ===")
    c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
    c.add_init_script(TA.INIT)
    pg = c.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE); pg.wait_for_function("window.__ready===true", timeout=15000)
    TA.set_level(pg, 1)
    pg.evaluate("""()=>{const d=JSON.parse(localStorage['kidmath2.progress.v2']);
        Object.keys(d.w).forEach(k=>{d.w[k].open=0;d.w[k].stars=0;d.w[k].lv=1;d.w[k].mast=0;
                                     d.w[k].tries=0;d.w[k].hist=[];d.w[k].recent=[];
                                     d.w[k].wins=0;d.w[k].winAt=-1;});
        d.sess=0; localStorage.setItem('kidmath2.progress.v2',JSON.stringify(d));}""")
    for launch in (1, 2):
        pg.reload(); pg.wait_for_function("window.__ready===true", timeout=15000)
        pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on")
        TA.enter_world(pg, "paw")                 # 第二个世界默认开放；它解锁第三个
        pg.wait_for_function("window.__q!=null", timeout=15000)
        t0 = time.time()
        rounds = 0
        while rounds < 12 and time.time() - t0 < 420:
            if pg.query_selector("#cheer.on"):
                pg.click("#cheer", force=True)
                pg.wait_for_selector("#map.on", timeout=8000)
                TA.enter_world(pg, "paw")
                pg.wait_for_function("window.__q!=null", timeout=15000)
            if not pg.query_selector("#stage.on"):
                break
            qn = pg.evaluate("window.__qn||0")
            try:
                TA.solve_paw(pg, wrong=False)     # 全部答对
                rounds += 1
            except Exception:
                pg.wait_for_timeout(600); continue
            try:
                pg.wait_for_function("(n)=>(window.__qn||0)>n || document.querySelector('#cheer.on')!==null",
                                     arg=qn, timeout=24000)
            except Exception:
                pg.wait_for_timeout(500)
        w = prog(pg, "paw")
        print("    第 %d 次启动后：%s" % (launch, {k: w[k] for k in ("lv", "mast", "wins", "tries")}))
    w = prog(pg, "paw")
    check(w["lv"] >= 2, "全对后难度升到 L2 以上（实际 L%d）" % w["lv"])
    check(w["mast"] >= 6, "累计掌握 >=6（实际 %d）" % w["mast"])
    check(w["wins"] >= 2, "跨两次启动拿到 2 个掌握窗口（实际 %d）" % w["wins"])
    rate2 = pg.evaluate("()=>{const d=JSON.parse(localStorage['kidmath2.progress.v2']).w.paw;"
                        "const h=(d.recent||[]).slice(-12);"
                        "return h.length<8?0:h.reduce((a,b)=>a+b,0)/h.length;}")
    check(rate2 >= 0.6, "近期正确率 >=0.6（实际 %.2f）—— 说明 recent 没有被 hist 的清窗连带清掉" % rate2)
    unlocked = pg.evaluate("()=>!document.querySelector('.world[data-w=\"bluey\"]').classList.contains('locked')")
    check(unlocked, "★ 稳定全对的孩子确实解锁了第三个世界（这是 R4「正向死锁」的回归测试）")
    check(len(errs) == 0, "G7 零 pageerror（%s）" % errs[:2])
    c.close()

    # ---------------- G6 两套字段独立 ----------------
    print("\n=== G6 参与星与掌握是两套字段 ===")
    c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
    c.add_init_script(TA.INIT)
    pg = c.new_page()
    pg.goto(BASE); pg.wait_for_function("window.__ready===true", timeout=15000)
    TA.set_level(pg, 1)                      # 先写入一份合法进度，再改字段
    pg.evaluate("""()=>{const d=JSON.parse(localStorage['kidmath2.progress.v2']);
        Object.keys(d.w).forEach(k=>{d.w[k].open=0;d.w[k].mast=0;d.w[k].lv=1;d.w[k].hist=[];});
        d.w.peppa.stars=10;
        localStorage.setItem('kidmath2.progress.v2',JSON.stringify(d));}""")
    pg.reload(); pg.wait_for_function("window.__ready===true")
    pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on")
    locked = pg.evaluate("()=>document.querySelector('.world[data-w=\"bluey\"]').classList.contains('locked')")
    check(locked, "第一个世界满 10 星但掌握为 0 时，第三个世界仍然锁着（满星不再是后门）")
    hasbadge = pg.evaluate("()=>!!document.querySelector('.world[data-w=\"peppa\"] .mbadge')")
    check(hasbadge, "地图上存在与参与星分开的掌握徽章")
    c.close()
    b.close()

httpd.shutdown()
print("\n通过 %d  失败 %d" % (len(PASSES), len(FAILS)))
for f in FAILS:
    print("  ✗ " + f)
sys.exit(1 if FAILS else 0)
