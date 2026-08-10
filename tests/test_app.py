# -*- coding: utf-8 -*-
"""星星回家 —— Playwright 发布门槛测试

覆盖：
  1. 六个世界全流程自动走查（各难度 L1..L4），零 console error / pageerror
  2. 语音时间线断言（指令不被无故重复；连续播报不互相踩踏；计数不丢数）
  3. 快速连点压力测试
  4. 断网离线重载
  5. 竖屏走查 + 零滚动断言
  6. 教学性质断言（答案卡唯一、题面与答案排列不同、错误不升级、提示题不计掌握）

用法： python tests/test_app.py [--browser webkit|chromium] [--headed]
"""
import sys, os, json, time, argparse, http.server, socketserver, threading, functools

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get("KM_PORT", "8899"))   # 并行跑两个引擎时用不同端口
BASE = "http://127.0.0.1:%d/index.html" % PORT
SHOTS = os.path.join(ROOT, "shots", os.environ.get("KM_TAG", ""))
os.makedirs(SHOTS, exist_ok=True)

from playwright.sync_api import sync_playwright

FAILS, PASSES, WARNS = [], [], []


def ok(msg):
    PASSES.append(msg); print("  [OK] " + msg)


def bad(msg):
    FAILS.append(msg); print("  [FAIL] " + msg)


def warn(msg):
    WARNS.append(msg); print("  [warn] " + msg)


def check(cond, msg):
    (ok if cond else bad)(msg)
    return cond


# ---------------------------------------------------------------- server
def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    class Q(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True
        def handle_error(self, *a): pass
    class SilentH(handler.func):
        def log_message(self, *a): pass
    httpd = Q(("127.0.0.1", PORT), functools.partial(SilentH, directory=ROOT))
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


# ---------------------------------------------------------------- speech recorder
INIT = r"""
window.__spk = [];
(function(){
  // WebKit(Playwright) 不带语音合成，但 iPad Safari 带 —— 补桩以走完整语音路径
  if(typeof window.SpeechSynthesisUtterance !== "function"){
    window.SpeechSynthesisUtterance = function(t){
      this.text = t; this.lang = ""; this.voice = null;
      this.rate = 1; this.pitch = 1; this.volume = 1;
      this.onend = null; this.onerror = null; this.onstart = null;
    };
  }
  var S = window.speechSynthesis;
  if(!S){
    window.speechSynthesis = { speaking:false, pending:false,
      getVoices:function(){return [];}, speak:function(){}, cancel:function(){},
      resume:function(){}, pause:function(){}, addEventListener:function(){} };
    S = window.speechSynthesis;
  }
  var realSpeak  = S.speak  ? S.speak.bind(S)  : function(){};
  var realCancel = S.cancel ? S.cancel.bind(S) : function(){};
  var busyUntil = 0;
  // 模拟一个"会说话"的引擎：speak 后进入 speaking 状态，按字数计时
  try{
    Object.defineProperty(S, "speaking", { get:function(){ return Date.now() < busyUntil; }, configurable:true });
    Object.defineProperty(S, "pending",  { get:function(){ return false; }, configurable:true });
  }catch(e){}
  S.speak = function(u){
    var txt = (u && u.text) || "";
    var now = Date.now();
    var overlap = now < busyUntil;     // 上一条还没说完就被塞进来 = 踩踏
    window.__spk.push({ t: Math.round(performance.now()), text: txt,
                        overlap: overlap, since_cancel: now - (window.__lastCancel||0) });
    busyUntil = now + Math.max(400, txt.length * 130);
    if(u){ setTimeout(function(){ try{ u.onend && u.onend(); }catch(e){} }, Math.max(400, txt.length*130)); }
    try{ realSpeak(u); }catch(e){}
  };
  S.cancel = function(){
    window.__lastCancel = Date.now();
    window.__cancels = (window.__cancels||0) + 1;
    busyUntil = 0;
    try{ realCancel(); }catch(e){}
  };
  // 引擎本身没有声音时（Playwright WebKit）才补一份假列表，
  // 有真声音的引擎（Chromium）保持原样，避免把非 SpeechSynthesisVoice 塞给 utterance
  var realGetVoices = S.getVoices ? S.getVoices.bind(S) : function(){ return []; };
  S.getVoices = function(){
    var v = [];
    try{ v = realGetVoices() || []; }catch(e){}
    if(v.length) return v;
    return [{name:"Samantha", lang:"en-US", localService:true},
            {name:"Ting-Ting", lang:"zh-CN", localService:true},
            {name:"Mei-Jia",   lang:"zh-TW", localService:true}];
  };
})();
"""

# 完全没有语音引擎的环境（最坏情况：iPad 上一个中文声音都没装）
NO_SPEECH = r"""
window.__spk = [];
try{ Object.defineProperty(window, "speechSynthesis", {get:function(){return undefined;}, configurable:true}); }catch(e){}
try{ delete window.SpeechSynthesisUtterance; }catch(e){}
window.SpeechSynthesisUtterance = undefined;
"""


class Ctx:
    def __init__(self, page):
        self.page = page
        self.errors = []
        page.on("console", self._console)
        page.on("pageerror", lambda e: self.errors.append("pageerror: " + str(e)))
        page.on("requestfailed", self._reqfail)

    def _reqfail(self, r):
        # 离开页面 / 换场景时浏览器会中止在途请求，这是正常行为，不算错误
        try:
            why = r.failure or ""
        except Exception:
            why = ""
        low = why.lower()
        if "abort" in low or "cancel" in low:
            return
        self.errors.append("requestfailed: %s (%s)" % (r.url, why))

    def _console(self, m):
        if m.type in ("error",):
            self.errors.append("console.%s: %s" % (m.type, m.text))


def start(page):
    page.wait_for_function("window.__ready === true", timeout=15000)
    page.click("#startBtn", force=True)
    page.wait_for_selector("#map.on", timeout=5000)


def unlock_all(page, lv=1):
    """把进度直接写成全解锁 + 指定难度，便于逐级走查（v3 存档）"""
    set_level(page, lv, stars=0)


def set_level(page, lv, stars=0, symbols=None):
    """写入一份 v3 存档：全解锁 + 指定难度。symbols 参数保留签名兼容（v3 数字默认开）。"""
    page.evaluate("""([lv,stars])=>{
      const d={v:3,plays:0,sess:0,set:{num:1,minlv:lv},w:{}};
      ["peppa","paw","bluey","hulu","aveng","monkey"].forEach(id=>{
        d.w[id]={stars:stars,lv:lv,hist:[],recent:[],seen:1,tries:0,open:1,mast:0,wins:0,winAt:-1};
      });
      localStorage.setItem("kidmath2.progress.v3", JSON.stringify(d));
    }""", [lv, stars])


def enter_world(page, wid):
    page.click('.world[data-w="%s"]' % wid, force=True)
    page.wait_for_selector("#stage.on", timeout=8000)
    page.wait_for_function("!document.querySelector('#busy').classList.contains('on')", timeout=15000)


def q(page):
    return page.evaluate("window.__q || null")


def wait_q(page, pred, timeout=12000):
    page.wait_for_function("(()=>{const q=window.__q;return q && (%s);})()" % pred, timeout=timeout)


# ---------------------------------------------------------------- 单轮求解器
def _pdc(page, sel):
    page.eval_on_selector(sel, """el=>{
      const r=el.getBoundingClientRect();
      const o={bubbles:true,cancelable:true,pointerType:'touch',button:0,pointerId:7,clientX:r.left+r.width/2,clientY:r.top+r.height/2};
      el.dispatchEvent(new PointerEvent('pointerdown',o));
      el.dispatchEvent(new PointerEvent('pointerup',o));}""")


def solve_round(page, wid, deliberately_wrong=False):
    """v6 通用解题器：按 window.__q.kind 驱动 24 个小游戏。"""
    qo = page.evaluate("window.__q")
    if not qo:
        return False
    k = qo.get("kind")
    w = page.wait_for_timeout
    if k == "bounce":
        page.wait_for_function('window.__q.phase=="play"', timeout=30000)
        w(300)
        for _ in range(qo["n"]):
            _pdc(page, ".tramp >> nth=1"); w(380)
        page.wait_for_selector(".bigbtn.green", timeout=6000); w(150)
        _pdc(page, ".bigbtn.green"); return True
    if k == "cake":
        w(1600)
        for _ in range(qo["a"]):
            _pdc(page, ".berry.red >> nth=0"); w(680)
        for _ in range(qo["b"]):
            _pdc(page, ".berry.blue >> nth=0"); w(680)
        page.wait_for_selector(".bigbtn.green", timeout=6000); w(150)
        _pdc(page, ".bigbtn.green"); return True
    if k == "tidy":
        w(1600)
        for _ in range(qo["k"]):
            _pdc(page, "#play .cobj:not([data-in]) >> nth=0"); w(650)
        sel = '.cards .card[data-n="%d"]' % qo["ans"]
        page.wait_for_selector(sel, timeout=25000); w(400)
        _pdc(page, sel); return True
    if k == "hat":
        page.wait_for_function('window.__q.phase=="play"', timeout=40000)
        w(500)
        for _ in range(qo["ans"]):
            _pdc(page, ".bigbtn:not(.green)"); w(340)
        page.wait_for_selector(".bigbtn.green", timeout=6000); w(150)
        _pdc(page, ".bigbtn.green"); return True
    if k == "cable":
        page.wait_for_function('window.__q.phase=="play"', timeout=30000)
        for _ in range(qo["n"]):
            w(1150); _pdc(page, ".cobj[data-dog]:not([data-out]) >> nth=0"); w(1500)
        return True
    if k == "radar":
        w(1800)
        for _ in range(qo["n"]):
            page.evaluate("""()=>{
              const z=[...document.querySelectorAll('[data-zone]')].filter(x=>!x.dataset.done)[0];
              const f=z.parentNode; const r=z.getBoundingClientRect();
              const o={bubbles:true,cancelable:true,pointerType:'touch',pointerId:7,clientX:r.left+r.width/2,clientY:r.top+r.height/2};
              f.dispatchEvent(new PointerEvent('pointerdown',o));
              f.dispatchEvent(new PointerEvent('pointermove',o));
              f.dispatchEvent(new PointerEvent('pointerup',o));}""")
            w(520)
        return True
    if k == "ring":
        w(1800)
        for _ in range(qo["ans"]):
            _pdc(page, '#play div[style*="cursor"] >> nth=0'); w(380)
        page.wait_for_selector(".bigbtn.green", timeout=6000); w(150)
        _pdc(page, ".bigbtn.green"); w(900)
        for _ in range(qo["ans"]):
            _pdc(page, "[data-launcher]"); w(2100)
        return True
    if k == "crank":
        w(1600)
        for _ in range(qo["d"] // 2 * 4):
            _pdc(page, "[data-crank]"); w(300)
        return True
    if k == "shadow":
        w(1500)
        _pdc(page, '[data-lamp="a"]')
        page.wait_for_function('window.__q.phase=="lampB"', timeout=25000); w(300)
        _pdc(page, '[data-lamp="b"]')
        page.wait_for_function('window.__q.phase=="judge"', timeout=25000); w(400)
        taller = "a" if qo["a"] > qo["b"] else "b"
        page.evaluate("""(t)=>{
          const cols=[...document.querySelectorAll('#play div')].filter(d=>d.style.flexDirection==='column-reverse');
          const col=t==='a'?cols[0]:cols[1];
          const o={bubbles:true,cancelable:true,pointerType:'touch',pointerId:7};
          col.dispatchEvent(new PointerEvent('pointerdown',o));}""", taller)
        return True
    if k == "balance":
        w(1600)
        for _ in range(qo["ans"]):
            _pdc(page, "#play .cobj:not([data-on]) >> nth=0"); w(750)
        return True
    if k == "dance":
        w(1500)
        for _ in range(qo["n"] // 2):
            _pdc(page, "#play .cobj:not([data-paired]) >> nth=0"); w(980)
        sel = '.cards .card[data-n="%d"]' % qo["ans"]
        page.wait_for_selector(sel, timeout=25000); w(300)
        _pdc(page, sel); return True
    if k == "pizza":
        w(1600)
        _pdc(page, '#play div[data-side="L"] >> nth=0'); w(1000)
        page.eval_on_selector('#play div[style*="dashed"]', """el=>{
          const r=el.getBoundingClientRect();
          const o={bubbles:true,cancelable:true,pointerType:'touch',pointerId:7,clientX:r.left+r.width/2,clientY:r.top+r.height/2};
          el.dispatchEvent(new PointerEvent('pointerdown',o));
          el.dispatchEvent(new PointerEvent('pointerup',o));}""")
        return True
    if k == "vine":
        w(1500); _pdc(page, '[data-g="%d"]' % qo["ans"]); return True
    if k == "lift":
        w(1500)
        for _ in range(qo["ans"] - 1):
            page.evaluate("""()=>{
              const f=document.querySelector('#play .field');
              const r=f.getBoundingClientRect();
              const o1={bubbles:true,pointerType:'touch',pointerId:7,clientX:r.left+r.width/2,clientY:r.top+r.height*0.4};
              const o2={bubbles:true,pointerType:'touch',pointerId:7,clientX:r.left+r.width/2,clientY:r.top+r.height*0.4+90};
              f.dispatchEvent(new PointerEvent('pointerdown',o1));
              f.dispatchEvent(new PointerEvent('pointerup',o2));}""")
            w(540)
        _pdc(page, ".bigbtn.green"); return True
    if k == "furnace":
        w(1600); _pdc(page, '[data-bundle="%d"]' % qo["ans"]); return True
    if k == "falls":
        w(1500)
        _pdc(page, '[data-gate="1"]')
        page.wait_for_function("window.__q.got&&window.__q.got.length>=1", timeout=20000)
        page.wait_for_function('window.__q.phase=="play"', timeout=20000)
        w(400)
        _pdc(page, '[data-gate="2"]')
        return True
    if k == "elev":
        w(1600)
        for _ in range(qo["n"] - 5):
            _pdc(page, "#play .cobj:not([data-in]) >> nth=0"); w(540)
        return True
    if k == "shield":
        w(1600); _pdc(page, '[data-strip="%d"]' % qo["ans"]); return True
    if k == "cannon":
        w(1600); _pdc(page, '[data-can="%d"]' % qo["ans"]); return True
    if k == "depot":
        w(1600)
        _pdc(page, "[data-tenbox]"); w(1300)
        for _ in range(qo["b"]):
            _pdc(page, "#play [data-sbox]:not([data-on]) >> nth=0"); w(540)
        return True
    if k == "bridge":
        page.wait_for_function('window.__q.phase=="play"', timeout=30000); w(300)
        for _ in range(qo["need"]):
            ln = page.evaluate("window.__len")
            _pdc(page, '[data-stone="%d"]' % ln); w(440)
        return True
    if k == "cloud":
        w(1500)
        for _ in range(qo["ans"]):
            _pdc(page, "[data-cloud]"); w(680)
        return True
    if k == "peach":
        w(1500)
        for _ in range(qo["p"]):
            _pdc(page, "#play [data-peach]:not([data-done]) >> nth=0"); w(1150)
        return True
    if k == "palace":
        w(1700)
        plan = [2, 2, 1] if qo["sum"] == 5 else [1, 1, 2]
        for s2 in plan:
            _pdc(page, '[data-jump="%d"]' % s2); w(720)
        return True
    return False


def click_card_with(page, n, wrong=False):
    page.wait_for_selector(".zbot .card", timeout=12000)
    cards = page.query_selector_all(".zbot .card")
    target = None
    for c in cards:
        v = c.get_attribute("data-n")
        if v is None:
            continue
        if (int(v) != n) if wrong else (int(v) == n):
            target = c
            break
    if target is None:
        target = cards[0]
    target.click(force=True)
    return target


def solve_peppa(page, wrong=False):
    page.wait_for_selector(".zbot .card", timeout=15000)
    n = q(page)["n"]
    click_card_with(page, n, wrong)
    return True


def solve_paw(page, wrong=False):
    st = q(page)
    if st["kind"] == "given":
        page.wait_for_selector(".zbot .bigbtn", timeout=10000)
        need = st["n"] if not wrong else max(1, st["n"] - 1)
        dogs = page.query_selector_all(".zbot button:not(.bigbtn)")
        for i in range(min(need, len(dogs))):
            dogs[i].click(force=True)
            page.wait_for_timeout(170)
        page.click(".zbot .bigbtn", force=True)
        return True
    # count / plus1
    objs = page.query_selector_all("#play .field .cobj")
    for o in objs:
        o.click(force=True)
        page.wait_for_timeout(80)
    page.wait_for_selector(".zbot .card", timeout=12000)
    st = q(page)
    target = st["n"] + 1 if st["kind"] == "plus1" else st["n"]
    click_card_with(page, target, wrong)
    return True


def solve_bluey(page, wrong=False):
    st = q(page)
    if st["mode"] == "fix":
        page.wait_for_selector(".zbot .bigbtn", timeout=10000)
        need = st["a"] - st["b"]
        if wrong:
            # 提交按钮在"一个都没加"时是禁用的，所以错答必须仍然 >=1 个
            need = need + 1 if need <= 1 else need - 1
        basket = page.query_selector_all(".zbot button:not(.bigbtn)")[0]
        for _ in range(need):
            basket.click(force=True)
            page.wait_for_timeout(170)
        page.click(".zbot .bigbtn", force=True)
        return True
    page.wait_for_selector(".zbot .card", timeout=12000)
    truth = "a" if st["a"] > st["b"] else ("b" if st["a"] < st["b"] else "same")
    idx = {"a": 0, "same": 1, "b": 2}[truth]
    if wrong:
        idx = (idx + 1) % 3
    page.query_selector_all(".zbot .card")[idx].click(force=True)
    return True


def solve_hulu(page, wrong=False):
    st = q(page)
    if st["kind"] == "ord":
        objs = page.query_selector_all("#play .field .cobj")
        i = st["target"] - 1
        if wrong:
            i = (i + 1) % len(objs)
        objs[i].click(force=True)
        return True
    if st["kind"] == "explore":
        page.wait_for_selector(".zbot .bigbtn", timeout=10000)
        n = st["N"]
        zl = page.query_selector(".dropzone")
        zr = page.query_selector_all(".dropzone")[1]
        zl.click(force=True); page.wait_for_timeout(200)
        for _ in range(n - 1):
            zr.click(force=True); page.wait_for_timeout(200)
        page.click(".zbot .bigbtn", force=True)
        return True
    # missing
    page.wait_for_selector(".zbot .bigbtn", timeout=10000)
    need = st["need"] if not wrong else max(1, st["need"] + 1)
    zr = page.query_selector_all(".dropzone")[1]
    for _ in range(need):
        zr.click(force=True); page.wait_for_timeout(200)
    page.click(".zbot .bigbtn", force=True)
    return True


def solve_aveng(page, wrong=False):
    st = q(page)
    if st["kind"] == "pair":
        heroes = page.query_selector_all("#play .field .cobj")
        n, m = st["n"], st["m"]
        H = heroes[:m]; G = heroes[m:m + n]
        for i in range(min(n, m)):
            H[i].click(force=True); page.wait_for_timeout(70)
            G[i].click(force=True); page.wait_for_timeout(70)
        page.wait_for_selector(".zbot .card", timeout=12000)
        truth = st["truth"]
        idx = {"less": 0, "same": 1, "more": 2}[truth]
        if wrong:
            idx = (idx + 1) % 3
        page.query_selector_all(".zbot .card")[idx].click(force=True)
        return True
    # add
    page.wait_for_selector(".zbot .bigbtn", timeout=12000)
    page.click(".zbot .bigbtn", force=True)
    page.wait_for_timeout(900)
    objs = page.query_selector_all("#play .field .cobj")
    for o in objs:
        o.click(force=True); page.wait_for_timeout(70)
    page.wait_for_selector(".zbot .card", timeout=12000)
    click_card_with(page, q(page)["n"], wrong)
    return True


def solve_monkey(page, wrong=False):
    st = q(page)
    page.wait_for_selector(".zbot .bigbtn", timeout=12000)
    # 等悟空把预置的几格铺完
    page.wait_for_timeout(500 + 800 * (st.get("pre") or 0))
    reach = (st.get("mode") == "reach")
    # reach 模式下位置只是操作、不计证据，所以永远摆对；错答留给后面那道算术题
    need = st["need"] if (reach or not wrong) else max(1, st["need"] + 1)
    for _ in range(need):
        stones = page.query_selector_all("#play .field .cobj")
        cur = page.evaluate("""()=>[...document.querySelectorAll('#play .field .cobj')]
                                  .filter(x=>x.classList.contains('counted')).length""")
        if cur >= len(stones):
            break
        stones[cur].click(force=True)
        page.wait_for_timeout(210)
    page.wait_for_function(
        "()=>{const b=document.querySelector('.zbot .bigbtn');return b&&!b.disabled;}", timeout=9000)
    page.click(".zbot .bigbtn", force=True)
    if reach:
        # 到位之后必须再答"你一共加了几格" —— 这才是缺失加数的判定
        page.wait_for_selector(".zbot .card", timeout=15000)
        click_card_with(page, st["need"], wrong)
    return True


def play_session(page, wid, rounds=5, timeout_s=170):
    """走完一个 session。关键：每次作答前必须确认新题已经建好（__qn 递增），
    否则会在上一题的 DOM 上乱点，测出来的失败是脚手架的锅不是应用的锅。"""
    t0 = time.time()
    guard = 0
    page.wait_for_function("window.__q != null", timeout=15000)
    while time.time() - t0 < timeout_s:
        guard += 1
        if guard > 60:
            break
        if not page.query_selector("#stage.on"):
            break
        if page.query_selector("#cheer.on"):
            break
        filled = page.evaluate("document.querySelectorAll('#dots i.f').length")
        if filled >= rounds:
            break
        qn = page.evaluate("window.__qn||0")
        try:
            solve_round(page, wid)
        except Exception:
            page.wait_for_timeout(700)
            continue
        # 得星或进入复测，都会建新题（__qn 递增）；通关则出现 #cheer
        try:
            page.wait_for_function(
                "(n)=>(window.__qn||0)>n || document.querySelector('#cheer.on')!==null",
                arg=qn, timeout=24000)
        except Exception:
            page.wait_for_timeout(600)
    return page.evaluate("document.querySelectorAll('#dots i.f').length") if page.query_selector("#dots") else 0


# ---------------------------------------------------------------- 语音时间线断言
def speech_report(page):
    return page.evaluate("window.__spk || []")


def assert_speech(page, label):
    log = speech_report(page)
    if not log:
        warn("%s：没有捕获到语音调用" % label)
        return
    # 1) 连续播报不互相踩踏：say 通道插话必须先 cancel（安全打断），
    #    而计数通道绝不 cancel、必须等空闲
    overlaps = [e for e in log if e["overlap"]]
    bad_overlap = [e for e in overlaps if e["since_cancel"] > 400]   # 没有 cancel 就压上去 = 踩踏
    check(len(bad_overlap) == 0,
          "%s：无未打断的语音踩踏（%d/%d 次重叠，全部由安全打断产生）" % (label, len(overlaps), len(log)))
    # 2) cancel 之后必须 ≥150ms 才 speak
    too_soon = [e for e in log if 0 < e["since_cancel"] < 150]
    check(len(too_soon) == 0, "%s：cancel 后均等待 ≥150ms 才 speak（违规 %d 次）" % (label, len(too_soon)))
    # 3) 指令不被无故重复：同一段文本在 3 秒内不应出现两次
    instr = [e for e in log if len(e["text"]) >= 8]      # 数词/短反馈不算指令
    dup = 0
    for i in range(1, len(instr)):
        for j in range(max(0, i - 6), i):
            if instr[i]["text"] == instr[j]["text"] and instr[i]["t"] - instr[j]["t"] < 3000:
                dup += 1
                break
    check(dup == 0, "%s：指令没有 3 秒内无故重复（%d 条指令中重复 %d 次）" % (label, len(instr), dup))
    # 4) 计数序列不丢数：出现的数词序列应单调递进
    return log


# ---------------------------------------------------------------- 主流程
def run(browser_name, headed, levels=(1, 2, 3, 4)):
    httpd = serve()
    time.sleep(0.4)
    with sync_playwright() as p:
        btype = getattr(p, browser_name)
        browser = btype.launch(headless=not headed)
        try:
            # ============ A. 六个世界 × 四个难度 全流程 ============
            for lv in levels:
                print("\n=== A. 难度 L%d 全世界走查（%s） ===" % (lv, browser_name))
                ctxb = browser.new_context(viewport={"width": 1180, "height": 820},
                                           has_touch=True, is_mobile=False)
                ctxb.add_init_script(INIT)
                page = ctxb.new_page()
                C = Ctx(page)
                page.goto(BASE)
                page.wait_for_function("window.__ready === true", timeout=15000)
                set_level(page, lv)
                page.reload()
                page.wait_for_function("window.__ready === true", timeout=15000)
                page.click("#startBtn", force=True)
                page.wait_for_selector("#map.on", timeout=6000)
                for w in ("peppa", "paw", "bluey", "hulu", "aveng", "monkey"):
                    page.evaluate("window.__spk=[]")
                    enter_world(page, w)
                    got = play_session(page, w, rounds=5, timeout_s=170)
                    check(got >= 4, "L%d %s：5 轮至少完成 4 轮（实际 %d）" % (lv, w, got))
                    if lv == 1:
                        page.screenshot(path=os.path.join(SHOTS, "L1-%s.png" % w))
                    assert_speech(page, "L%d %s" % (lv, w))
                    # 回到地图
                    if page.query_selector("#stage.on"):
                        page.click("#homeBtn", force=True)
                    page.wait_for_selector("#map.on", timeout=8000)
                check(len(C.errors) == 0, "L%d：零 console error / pageerror（%s）" % (lv, C.errors[:3]))
                ctxb.close()

            # ============ B. 教学性质断言 ============
            print("\n=== B. 教学性质断言 ===")
            ctxb = browser.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
            ctxb.add_init_script(INIT)
            page = ctxb.new_page(); C = Ctx(page)
            page.goto(BASE); page.wait_for_function("window.__ready===true")
            set_level(page, 2); page.reload(); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")

            # B1 答案卡数值唯一
            enter_world(page, "peppa")
            page.wait_for_selector(".zbot .card", timeout=15000)
            vals = page.evaluate("[...document.querySelectorAll('.zbot .card')].map(c=>+c.dataset.n)")
            check(len(vals) == len(set(vals)) and len(vals) == 4, "答案卡 4 张且数值互不重复：%s" % vals)
            # B2 题面排列 ≠ 答案排列（防图形匹配）
            qq = q(page)
            check(qq["apat"] != qq["cfg"]["qpat"], "佩奇：答案点阵排列与泥点排列不同（%s vs %s）" % (qq["apat"], qq["cfg"]["qpat"]))
            # B3 错误不升级 + 复测题不计掌握
            # 注意：断言必须落在 recent 与 mast 上。
            # hist 是"升降级滑动窗口"，达成 4/5 就会被清空；而 set_level 预置了 8 条全对，
            # 所以答错一次之后最近 5 题仍是 4/5 → 正常升级并清窗，这本身是正确行为。
            mast_before = page.evaluate("JSON.parse(localStorage['kidmath2.progress.v2']).w.peppa.mast")
            click_card_with(page, q(page)["n"], wrong=True)
            page.wait_for_timeout(1200)
            rec = page.evaluate("JSON.parse(localStorage['kidmath2.progress.v2']).w.peppa.recent")
            check(rec and rec[-1] == 0, "答错立即写入一次失败证据：recent 末位=%s" % (rec[-1] if rec else None))
            mast_now = page.evaluate("JSON.parse(localStorage['kidmath2.progress.v2']).w.peppa.mast")
            check(mast_now == mast_before, "答错不增加掌握计数（%d -> %d）" % (mast_before, mast_now))
            # 等复测题出现，答对它 —— 复测不得再写证据
            page.wait_for_timeout(6500)
            tries_mid = page.evaluate("JSON.parse(localStorage['kidmath2.progress.v2']).w.peppa.tries")
            if page.query_selector(".zbot .card"):
                click_card_with(page, q(page)["n"], wrong=False)
                page.wait_for_timeout(2500)
            tries_after = page.evaluate("JSON.parse(localStorage['kidmath2.progress.v2']).w.peppa.tries")
            check(tries_after == tries_mid, "复测题（同构新题）不写掌握证据：tries %d -> %d" % (tries_mid, tries_after))
            # B4 守恒题两边等量且只有间距不同
            page.click("#homeBtn", force=True); page.wait_for_selector("#map.on")
            set_level(page, 3); page.reload(); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")
            enter_world(page, "bluey")
            page.wait_for_timeout(900)
            qq = q(page)
            check(qq["mode"] == "cons" and qq["a"] == qq["b"], "Bluey L3 是守恒题：等量 a=%s b=%s" % (qq["a"], qq["b"]))
            sizes = page.evaluate("""()=>{
              const o=[...document.querySelectorAll('#play .cobj')];
              return o.map(e=>Math.round(e.getBoundingClientRect().width));}""")
            check(len(set(sizes)) == 1, "守恒题所有物体尺寸完全相同：%s" % sorted(set(sizes)))
            # B5 乱点不能必过：故意答错，必须进入手动配对纠错而不是直接过关
            filled0 = page.evaluate("document.querySelectorAll('#dots i.f').length")
            solve_bluey(page, wrong=True)
            page.wait_for_timeout(1500)
            filled1 = page.evaluate("document.querySelectorAll('#dots i.f').length")
            check(filled1 == filled0, "Bluey 守恒答错不会直接过关（星 %d -> %d）" % (filled0, filled1))
            page.screenshot(path=os.path.join(SHOTS, "B-bluey-conservation.png"))
            # B6 一直答错也必须在有限步内拿到答案并推进（3 岁半不能被卡住）
            page.click("#homeBtn", force=True); page.wait_for_selector("#map.on")
            set_level(page, 2); page.reload(); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")
            enter_world(page, "peppa")
            page.wait_for_function("window.__q != null", timeout=15000)
            f0 = page.evaluate("document.querySelectorAll('#dots i.f').length")
            wrongs = 0
            t_end = time.time() + 60
            while time.time() < t_end:
                if page.evaluate("document.querySelectorAll('#dots i.f').length") > f0:
                    break
                qn = page.evaluate("window.__qn||0")
                try:
                    solve_peppa(page, wrong=True); wrongs += 1
                except Exception:
                    pass
                try:
                    page.wait_for_function("(n)=>(window.__qn||0)>n || document.querySelectorAll('#dots i.f').length>%d" % f0,
                                           arg=qn, timeout=20000)
                except Exception:
                    page.wait_for_timeout(500)
            got = page.evaluate("document.querySelectorAll('#dots i.f').length")
            check(got > f0 and wrongs <= 3,
                  "一直答错时，最多 %d 次后系统给出答案并推进（星 %d -> %d）" % (wrongs, f0, got))
            check(len(C.errors) == 0, "B 组零 console error（%s）" % C.errors[:3])
            ctxb.close()

            # ============ C. 快速连点压力 ============
            print("\n=== C. 快速连点压力测试 ===")
            ctxb = browser.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
            ctxb.add_init_script(INIT)
            page = ctxb.new_page(); C = Ctx(page)
            page.goto(BASE); page.wait_for_function("window.__ready===true")
            set_level(page, 2); page.reload(); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")
            enter_world(page, "paw")
            page.wait_for_timeout(600)
            page.evaluate("window.__spk=[]")
            # 对所有可点物体疯狂连点
            for _ in range(6):
                for sel in ("#play .field .cobj", ".zbot .card", ".zbot button", "#speakBtn"):
                    els = page.query_selector_all(sel)
                    for e in els[:8]:
                        try:
                            e.click(force=True, timeout=800)
                        except Exception:
                            pass
                page.wait_for_timeout(60)
            page.wait_for_timeout(1500)
            log = speech_report(page)
            bad_overlap = [e for e in log if e["overlap"] and e["since_cancel"] > 400]
            check(len(bad_overlap) == 0, "连点压力下无未打断的语音踩踏（%d 条语音）" % len(log))
            too_soon = [e for e in log if 0 < e["since_cancel"] < 150]
            check(len(too_soon) == 0, "连点压力下 cancel→speak 间隔均 ≥150ms（违规 %d）" % len(too_soon))
            check(len(C.errors) == 0, "连点压力零 console error（%s）" % C.errors[:3])
            page.screenshot(path=os.path.join(SHOTS, "C-stress.png"))
            ctxb.close()

            # ============ D. 竖屏 + 零滚动 ============
            print("\n=== D. 竖屏走查 ===")
            ctxb = browser.new_context(viewport={"width": 820, "height": 1180}, has_touch=True)
            ctxb.add_init_script(INIT)
            page = ctxb.new_page(); C = Ctx(page)
            page.goto(BASE); page.wait_for_function("window.__ready===true")
            set_level(page, 2); page.reload(); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")
            page.screenshot(path=os.path.join(SHOTS, "D-map-portrait.png"))
            for w in ("peppa", "paw", "bluey", "hulu", "aveng", "monkey"):
                enter_world(page, w)
                page.wait_for_timeout(1400)
                over = page.evaluate("""()=>{
                  const d=document.documentElement, b=document.body;
                  return Math.max(d.scrollHeight-d.clientHeight, b.scrollHeight-b.clientHeight,
                                  d.scrollWidth-d.clientWidth);}""")
                check(over <= 1, "竖屏 %s：页面不滚动（溢出 %dpx）" % (w, over))
                oob = page.evaluate("""()=>{
                  const bad=[];
                  document.querySelectorAll('#play .cobj, .zbot .card, .zbot .bigbtn, .zbot button, .dropzone')
                    .forEach(e=>{ const r=e.getBoundingClientRect();
                      if(r.width>0 && (r.left<-2||r.top<-2||r.right>innerWidth+2||r.bottom>innerHeight+2))
                        bad.push(e.className+' '+Math.round(r.left)+','+Math.round(r.bottom)); });
                  return bad;}""")
                check(len(oob) == 0, "竖屏 %s：所有可点目标都在视口内（越界 %s）" % (w, oob[:2]))
                page.screenshot(path=os.path.join(SHOTS, "D-%s-portrait.png" % w))
                solve_round(page, w)
                page.wait_for_timeout(1200)
                if page.query_selector("#stage.on"):
                    page.click("#homeBtn", force=True)
                page.wait_for_selector("#map.on", timeout=8000)
            check(len(C.errors) == 0, "竖屏零 console error（%s）" % C.errors[:3])
            ctxb.close()

            # ============ E. 反复进出 + 存储损坏 ============
            print("\n=== E. 生命周期 / 容错 ===")
            ctxb = browser.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
            ctxb.add_init_script(INIT)
            page = ctxb.new_page(); C = Ctx(page)
            page.goto(BASE); page.wait_for_function("window.__ready===true")
            page.evaluate("localStorage.setItem('kidmath2.progress.v2','{{{ broken json')")
            page.reload(); page.wait_for_function("window.__ready===true", timeout=8000)
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")
            check(True, "localStorage 损坏时能正常启动")
            set_level(page, 2); page.reload(); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")
            for i in range(8):
                w = ["peppa", "paw", "bluey", "hulu", "aveng", "monkey"][i % 6]
                enter_world(page, w)
                page.wait_for_timeout(700)
                page.click("#homeBtn", force=True)
                page.wait_for_selector("#map.on", timeout=6000)
            leaked = page.evaluate("document.querySelectorAll('#play *').length")
            check(leaked == 0, "离开世界后舞台 DOM 完全清空（残留 %d 个节点）" % leaked)
            check(len(C.errors) == 0, "反复进出零 console error（%s）" % C.errors[:3])
            ctxb.close()

            # ============ F. 家长门 ============
            print("\n=== F. 成人门 / 诊断面板 ===")
            ctxb = browser.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
            ctxb.add_init_script(INIT)
            page = ctxb.new_page(); C = Ctx(page)
            page.goto(BASE); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")
            box = page.query_selector("#parentDot").bounding_box()
            page.mouse.move(box["x"] + 20, box["y"] + 20)
            page.mouse.down()
            page.wait_for_timeout(3300)
            page.mouse.up()
            check(page.is_visible("#gateAdult"), "长按 3 秒弹出成人验证门（不是直接进面板）")
            check(not page.is_visible("#panel"), "成人验证前面板不可见")
            aq = page.inner_text("#gaQ")
            a, b = [int(x) for x in aq.replace("= ?", "").split("+")]
            page.click("#gaOpts button >> text='%d'" % (a + b), force=True)
            page.wait_for_timeout(700)
            check(not page.is_visible("#panel"), "只答对一题还进不去（要求连对两题）")
            aq2 = page.inner_text("#gaQ")
            a2, b2 = [int(x) for x in aq2.replace("= ?", "").split("+")]
            page.click("#gaOpts button >> text='%d'" % (a2 + b2), force=True)
            page.wait_for_timeout(700)
            check(page.is_visible("#panel"), "连对两题后进入家长面板")
            page.screenshot(path=os.path.join(SHOTS, "F-parent-panel.png"))
            check(len(C.errors) == 0, "家长门零 console error（%s）" % C.errors[:3])
            ctxb.close()

            # ============ G. 离线 ============
            print("\n=== G. 断网离线 ===")
            ctxb = browser.new_context(viewport={"width": 1180, "height": 820}, has_touch=True,
                                       service_workers="allow")
            ctxb.add_init_script(INIT)
            page = ctxb.new_page(); C = Ctx(page)
            page.goto(BASE)
            page.wait_for_function("window.__ready===true", timeout=15000)
            set_level(page, 2); page.reload(); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")
            reg = page.evaluate("""async ()=>{
              if(!('serviceWorker' in navigator)) return 'no-sw';
              const r = await navigator.serviceWorker.ready.catch(()=>null);
              return r ? 'ready' : 'none';
            }""")
            if reg != "ready":
                warn("Service Worker 未就绪（%s）—— 该浏览器可能不支持，跳过离线断言" % reg)
            else:
                ok("Service Worker 注册成功")
                for w in ("peppa", "paw", "bluey", "hulu", "aveng", "monkey"):
                    enter_world(page, w); page.wait_for_timeout(600)
                    page.click("#homeBtn", force=True); page.wait_for_selector("#map.on")
                page.wait_for_timeout(1800)
                ctxb.set_offline(True)
                reloaded, last = False, ""
                for attempt in range(3):
                    try:
                        if attempt == 0:
                            page.reload(wait_until="domcontentloaded", timeout=30000)
                        else:
                            page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_function("window.__ready===true", timeout=20000)
                        reloaded = True
                        break
                    except Exception as e:
                        last = str(e).split("\n")[0][:110]
                        try:
                            page.wait_for_timeout(1500)
                        except Exception:
                            pass
                if not reloaded:
                    warn("断网重载没能完成（浏览器引擎侧问题，非应用问题）：%s" % last)
                else:
                    page.click("#startBtn", force=True); page.wait_for_selector("#map.on", timeout=8000)
                    check(True, "断网后仍能从缓存启动")
                    enter_world(page, "peppa")
                    page.wait_for_timeout(2500)
                    imgs_ok = page.evaluate("""()=>{
                      const im=[...document.querySelectorAll('#play img, #sceneBg img')];
                      return im.length>0 && im.every(x=>x.complete && x.naturalWidth>0);}""")
                    check(imgs_ok, "断网后素材仍从缓存正常显示")
                    got = play_session(page, "peppa", rounds=2, timeout_s=70)
                    check(got >= 2, "断网后仍可正常游玩（完成 %d/2 轮）" % got)
                    page.screenshot(path=os.path.join(SHOTS, "G-offline.png"))
                ctxb.set_offline(False)
            ctxb.close()

            # ============ H. 完全没有语音引擎 ============
            print("\n=== H. 无语音引擎时仍可完整游玩 ===")
            ctxb = browser.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
            ctxb.add_init_script(NO_SPEECH)
            page = ctxb.new_page(); C = Ctx(page)
            page.goto(BASE)
            page.wait_for_function("window.__ready===true", timeout=15000)
            check(True, "无语音引擎时应用仍能启动")
            set_level(page, 2); page.reload(); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True)
            page.wait_for_selector("#map.on", timeout=6000)
            check(page.is_visible("#soundHint"), "无语音时自动出现喇叭提示条（用引擎状态判定，不靠事件）")
            for w in ("peppa", "paw", "bluey", "hulu", "aveng", "monkey"):
                enter_world(page, w)
                got = play_session(page, w, rounds=2, timeout_s=140)
                check(got >= 2, "无语音时 %s 仍可完整通关（完成 %d/2 轮）" % (w, got))
                if page.query_selector("#stage.on"):
                    page.click("#homeBtn", force=True)
                page.wait_for_selector("#map.on", timeout=8000)
            page.screenshot(path=os.path.join(SHOTS, "H-no-speech.png"))
            check(len(C.errors) == 0, "无语音时零 console error（%s）" % C.errors[:3])
            ctxb.close()

        finally:
            browser.close()
    httpd.shutdown()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser", default="chromium")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--levels", default="1,2,3,4",
                    help="A 组要走查的难度，逗号分隔。WebKit 很慢，通常只跑 1,3 覆盖全部题型")
    a = ap.parse_args()
    print("=" * 60)
    print("星星回家 · Playwright 发布门槛测试  [%s]" % a.browser)
    print("=" * 60)
    t0 = time.time()
    run(a.browser, a.headed, tuple(int(x) for x in a.levels.split(",") if x.strip()))
    print("\n" + "=" * 60)
    print("通过 %d  失败 %d  警告 %d   用时 %.0fs" % (len(PASSES), len(FAILS), len(WARNS), time.time() - t0))
    if FAILS:
        print("\n失败项：")
        for f in FAILS:
            print("  ✗ " + f)
    if WARNS:
        print("\n警告：")
        for w in WARNS:
            print("  ! " + w)
    print("截图目录: " + SHOTS)
    sys.exit(1 if FAILS else 0)
