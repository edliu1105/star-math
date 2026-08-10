# -*- coding: utf-8 -*-
"""第三轮测试修正（codex 4-2 指出的盲区，全部接受）：
   T1 G1 是"读答案后保证点错"，不是随机 → 新增 G1b：固定点屏幕同一位置（第一张卡），
      答案每题重新洗牌，200 轮后断言正确率贴近随机且第三个世界仍锁着
   T2 G5 点的是旧题的数值 → 新增 G5b：固定点第一个按钮位置，反复长按重开门，断言进不去
   T3 set_level 不写 mast/wins，导致 L4 全流程从未进入"符号已解锁"分支 → 补上
   T4 H 组只跑三个世界 → 改成六个世界全跑
   T5 D 组只测整页 scroll → 增加"所有可点目标都在视口内"的断言
"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "test_app.py")
s = io.open(p, encoding="utf-8").read()
n = 0
miss = []


def rep(a, b):
    global s, n
    if a in s:
        s = s.replace(a, b, 1); n += 1
    else:
        miss.append(a[:78].replace("\n", "\\n"))


# T3 set_level 写全掌握字段
rep('''def set_level(page, lv, stars=5, symbols=False):
    page.evaluate("""([lv,stars])=>{
      const d={v:2,plays:0,w:{}};
      ["peppa","paw","bluey","hulu","aveng","monkey"].forEach(id=>{
        d.w[id]={stars:stars,lv:lv,hist:[],seen:1,tries:20,open:1};
      });
      localStorage.setItem("kidmath2.progress.v2", JSON.stringify(d));
    }""", [lv, stars])''',
    '''def set_level(page, lv, stars=5, symbols=None):
    """写入一份"已解锁 + 已有掌握证据"的进度。
    symbols=None 时按 lv 推断：lv>=3 就让符号门也满足，否则 L4 全流程永远进不去
    "符号已解锁"的那些分支（codex 4-2 指出的盲区）。"""
    if symbols is None:
        symbols = lv >= 3
    page.evaluate("""([lv,stars,sym])=>{
      const d={v:2,plays:9,w:{}};
      ["peppa","paw","bluey","hulu","aveng","monkey"].forEach(id=>{
        d.w[id]={stars:stars,lv:lv,hist:[1,1,1,1,1,1,1,1],seen:1,tries:20,open:1,
                 mast:(sym?12:8),wins:2,winAt:8};
      });
      localStorage.setItem("kidmath2.progress.v2", JSON.stringify(d));
    }""", [lv, stars, bool(symbols)])''')

# T4 H 组跑六个世界
rep('''            for w in ("peppa", "paw", "monkey"):
                enter_world(page, w)
                got = play_session(page, w, rounds=3, timeout_s=120)
                check(got >= 3, "无语音时 %s 仍可完整通关（完成 %d/3 轮）" % (w, got))''',
    '''            for w in ("peppa", "paw", "bluey", "hulu", "aveng", "monkey"):
                enter_world(page, w)
                got = play_session(page, w, rounds=2, timeout_s=140)
                check(got >= 2, "无语音时 %s 仍可完整通关（完成 %d/2 轮）" % (w, got))''')

# T5 D 组增加"所有可点目标在视口内"
rep('''                check(over <= 1, "竖屏 %s：页面不滚动（溢出 %dpx）" % (w, over))''',
    '''                check(over <= 1, "竖屏 %s：页面不滚动（溢出 %dpx）" % (w, over))
                oob = page.evaluate("""()=>{
                  const bad=[];
                  document.querySelectorAll('#play .cobj, .zbot .card, .zbot .bigbtn, .zbot button, .dropzone')
                    .forEach(e=>{ const r=e.getBoundingClientRect();
                      if(r.width>0 && (r.left<-2||r.top<-2||r.right>innerWidth+2||r.bottom>innerHeight+2))
                        bad.push(e.className+' '+Math.round(r.left)+','+Math.round(r.bottom)); });
                  return bad;}""")
                check(len(oob) == 0, "竖屏 %s：所有可点目标都在视口内（越界 %s）" % (w, oob[:2]))''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("test_app.py patched", n)
if miss:
    print("MISSED:", miss)

# ---------- G1b / G5b 追加到 test_gates.py ----------
g = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "test_gates.py")
t = io.open(g, encoding="utf-8").read()
anchor = "    # ---------------- G2 / G3 提示后不计证据 ----------------"
extra = '''    # ---------------- G1b 真·随机乱点（固定屏幕位置，答案每题洗牌） ----------------
    print("\\n=== G1b 固定点第一张卡 %d 轮（真随机命中，约 1/4） ===" % (a.rounds * 2))
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
    check(rate < 0.45, "随机命中率停留在随机水平（%.2f < 0.45）" % rate)
    locked = pg.evaluate("()=>document.querySelector('.world[data-w=\\"bluey\\"]').classList.contains('locked')")
    check(locked, "固定位置乱点 %d 次后第三个世界仍然锁着" % done)
    check(w["wins"] < 2, "跨会话掌握窗口不足 2（实际 %d）" % w["wins"])
    check(len(errs) == 0, "G1b 零 pageerror（%s）" % errs[:2])
    c.close()

'''
assert anchor in t
t = t.replace(anchor, extra + anchor, 1)

anchor2 = "    # ---------------- G6 两套字段独立 ----------------"
extra2 = '''    # ---------------- G5b 成人门固定位置反复猜 ----------------
    print("\\n=== G5b 成人门：固定点第一个按钮 + 反复长按重开 ===")
    c = b.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
    c.add_init_script(TA.INIT)
    pg = c.new_page()
    pg.goto(BASE); pg.wait_for_function("window.__ready===true", timeout=15000)
    pg.click("#startBtn", force=True); pg.wait_for_selector("#map.on")
    opened = False
    attempts = 0
    for _ in range(20):
        box = pg.query_selector("#parentDot").bounding_box()
        pg.mouse.move(box["x"] + 20, box["y"] + 20); pg.mouse.down()
        pg.wait_for_timeout(3200); pg.mouse.up()
        if not pg.is_visible("#gateAdult"):
            break
        btns = pg.query_selector_all("#gaOpts button")
        if not btns:
            break
        btns[0].click(force=True)          # 永远点第一个位置
        attempts += 1
        pg.wait_for_timeout(700)
        if pg.is_visible("#panel"):
            opened = True
            break
        # 若门还开着（说明第一题答对了），继续点第一个位置
        if pg.is_visible("#gateAdult"):
            b2 = pg.query_selector_all("#gaOpts button")
            if b2:
                b2[0].click(force=True); attempts += 1
                pg.wait_for_timeout(700)
                if pg.is_visible("#panel"):
                    opened = True
                    break
    check(not opened, "固定位置猜了 %d 次（每次都要重新长按 3 秒）仍未进入家长面板" % attempts)
    c.close()

'''
assert anchor2 in t
t = t.replace(anchor2, extra2 + anchor2, 1)
io.open(g, "w", encoding="utf-8", newline="").write(t)
print("test_gates.py patched (G1b, G5b)")
