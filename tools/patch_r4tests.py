# -*- coding: utf-8 -*-
"""第四轮测试修正（codex R4-4-2 全部接受）：
   F 组：成人门现在要连对两题 → 断言随之更新
   G4：改为直接调用应用里的 patDiffers()，并显式断言 patDiffers(3,'dice','ring')===false
   G1b：断言真的跑满目标轮数，并显式记录"全部发生在同一次启动"
   G5b：成人门答错后有 30 秒冷却 → 改成确定性断言（冷却期内长按无效）
   G7（新增，最重要）：**正向掌握测试** —— 稳定全对的孩子跨两次启动之后必须解锁第三个世界。
       这正是 R4 抓到的"全对却永远解锁不了"那个 bug 的回归测试。
"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------- test_app.py：F 组 ----------------
p = os.path.join(ROOT, "tests", "test_app.py")
s = io.open(p, encoding="utf-8").read()
a = '''            aq = page.inner_text("#gaQ")
            a, b = [int(x) for x in aq.replace("= ?", "").split("+")]
            page.click("#gaOpts button >> text='%d'" % (a + b), force=True)
            page.wait_for_timeout(400)
            check(page.is_visible("#panel"), "答对算式后进入家长面板")'''
b = '''            aq = page.inner_text("#gaQ")
            a, b = [int(x) for x in aq.replace("= ?", "").split("+")]
            page.click("#gaOpts button >> text='%d'" % (a + b), force=True)
            page.wait_for_timeout(700)
            check(not page.is_visible("#panel"), "只答对一题还进不去（要求连对两题）")
            aq2 = page.inner_text("#gaQ")
            a2, b2 = [int(x) for x in aq2.replace("= ?", "").split("+")]
            page.click("#gaOpts button >> text='%d'" % (a2 + b2), force=True)
            page.wait_for_timeout(700)
            check(page.is_visible("#panel"), "连对两题后进入家长面板")'''
assert a in s, "F 组锚点未命中"
s = s.replace(a, b, 1)
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("test_app.py: F 组已更新")

# ---------------- test_gates.py ----------------
g = os.path.join(ROOT, "tests", "test_gates.py")
t = io.open(g, encoding="utf-8").read()

# G4：用应用自己的 patDiffers
old_g4 = '''    bad = pg.evaluate("""()=>{
      const out=[];
      for(let n=1;n<=6;n++){
        for(const qp of ["dice","group"]){
          const ap=pickAnswerPat(n,qp);
          const A=dotPos(n,qp), B=dotPos(n,ap);
          let far=0;
          for(let i=0;i<A.length;i++){
            const d=Math.hypot(A[i][0]-B[i][0],A[i][1]-B[i][1]);
            if(d>14) far++;
          }
          if(far < Math.max(1,Math.ceil(n*0.6))) out.push(n+":"+qp+"->"+ap+"(far="+far+")");
        }
      }
      return out;}""")
    check(len(bad) == 0, "1–6 个点、两种题面排列下答案排列都在几何上明显不同（问题项 %s）" % bad)'''
new_g4 = '''    # 直接调用应用里的 patDiffers()（点集 Hausdorff），不再在测试里另写一套按下标的算法
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
    print("    n=3 dice↔ring 的 Hausdorff 距离 = %s（阈值 13）" % haus)'''
assert old_g4 in t, "G4 锚点未命中"
t = t.replace(old_g4, new_g4, 1)

# G1b：断言跑满 + 同一次启动
old = '''    check(rate < 0.45, "随机命中率停留在随机水平（%.2f < 0.45）" % rate)'''
new = '''    check(done >= a.rounds * 2 - 6, "确实跑满了 %d 轮（实际 %d）" % (a.rounds * 2, done))
    sess = pg.evaluate("()=>JSON.parse(localStorage['kidmath2.progress.v2']).sess")
    print("    全部发生在同一次应用启动内（sess=%s）→ wins 结构上最多为 1" % sess)
    check(rate < 0.45, "随机命中率停留在随机水平（%.2f < 0.45）" % rate)'''
assert old in t
t = t.replace(old, new, 1)

# G5b：改成确定性的冷却断言
old_g5b_start = t.index('    # ---------------- G5b 成人门固定位置反复猜 ----------------')
old_g5b_end = t.index('    # ---------------- G6 两套字段独立 ----------------')
new_g5b = '''    # ---------------- G5b 成人门：答错进入冷却，暴力猜在时间上不可行 ----------------
    print("\\n=== G5b 成人门答错冷却 ===")
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

'''
t = t[:old_g5b_start] + new_g5b + t[old_g5b_end:]

# G7 正向掌握测试
anchor = "    # ---------------- G6 两套字段独立 ----------------"
g7 = '''    # ---------------- G7 正向：稳定全对的孩子必须能解锁 ----------------
    print("\\n=== G7 全对的孩子跨两次启动后必须解锁第三个世界 ===")
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
    unlocked = pg.evaluate("()=>!document.querySelector('.world[data-w=\\"bluey\\"]').classList.contains('locked')")
    check(unlocked, "★ 稳定全对的孩子确实解锁了第三个世界（这是 R4「正向死锁」的回归测试）")
    check(len(errs) == 0, "G7 零 pageerror（%s）" % errs[:2])
    c.close()

'''
assert anchor in t
t = t.replace(anchor, g7 + anchor, 1)
io.open(g, "w", encoding="utf-8", newline="").write(t)
print("test_gates.py: G4/G1b/G5b 更新，新增 G7 正向掌握测试")
