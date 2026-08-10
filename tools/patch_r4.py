# -*- coding: utf-8 -*-
"""第四轮修复（codex R4 的五个技术阻断项）：
   R4-1 [严重] 掌握门正向死锁：recentRate 要 hist>=8，但 hist 每达成一次 4/5 就被清空
        → 拆成两套历史：hist（升降级窗口，会清空） / recent（滚动 12 条，永不清空）
   R4-2 [严重] 成人门可在同一题上快速连点凑够 streak
        → 首次点击同步锁题并禁用全部按钮；答错立即关门并进入 30 秒冷却
   R4-3 [中等] stopScope() 先清本地忙标记、后判忙 → 先存 wasBusy 再清；令牌校验改严格
   R4-4 [中等] 复联计数角标绕过符号门 → 改用 setTag()
"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()
n = 0
miss = []


def rep(a, b):
    global s, n
    if a in s:
        s = s.replace(a, b, 1); n += 1
    else:
        miss.append(a[:78].replace("\n", "\\n"))


# ---------- R4-1 拆成两套历史 ----------
rep("  const mkW=()=>({stars:0,lv:1,hist:[],seen:0,tries:0,open:0,mast:0,wins:0,winAt:-1});",
    "  // hist  = 升/降级的滑动窗口，达成一次窗口就清空\n"
    "  // recent= 近期正确率用的滚动历史，**永不清空** —— 两者混用会让全对的孩子永远算不出正确率\n"
    "  const mkW=()=>({stars:0,lv:1,hist:[],recent:[],seen:0,tries:0,open:0,mast:0,wins:0,winAt:-1});")
rep("        t.hist=Array.isArray(s.hist)?s.hist.filter(v=>v===0||v===1).slice(-16):[];",
    "        t.hist=Array.isArray(s.hist)?s.hist.filter(v=>v===0||v===1).slice(-16):[];\n"
    "        t.recent=Array.isArray(s.recent)?s.recent.filter(v=>v===0||v===1).slice(-12):[];")
rep('''  function recentRate(w){
    const h=w.hist.slice(-10);
    if(h.length<8) return 0;
    return h.reduce((a,b)=>a+b,0)/h.length;
  }''',
    '''  function recentRate(w){
    const h=(w.recent||[]).slice(-12);
    if(h.length<8) return 0;                  // 样本太少不下结论
    return h.reduce((a,b)=>a+b,0)/h.length;
  }''')
rep('''      const w=W(id); w.tries++;
      if(ok) w.mast++;
      w.hist.push(ok?1:0); if(w.hist.length>16) w.hist.shift();''',
    '''      const w=W(id); w.tries++;
      if(ok) w.mast++;
      w.hist.push(ok?1:0); if(w.hist.length>16) w.hist.shift();
      if(!w.recent) w.recent=[];
      w.recent.push(ok?1:0); if(w.recent.length>12) w.recent.shift();   // 这一条永不被清空''')

# ---------- R4-2 成人门 ----------
rep('''  let gaAnswer=0, gaStreak=0;
  function openAdultGate(reset){
    if(reset!==false) gaStreak=0;
    const a=rint(6,9), b=rint(5,9); gaAnswer=a+b;''',
    '''  let gaAnswer=0, gaStreak=0, gaAnswered=false, gaCooldownUntil=0;
  function openAdultGate(reset){
    if(reset!==false) gaStreak=0;
    gaAnswered=false;                       // 每道新题重置"本题已作答"
    const a=rint(6,9), b=rint(5,9); gaAnswer=a+b;''')
rep('''      onTap(btn,()=>{
        if(v===gaAnswer){
          gaStreak++;
          if(gaStreak>=2){ $("#gateAdult").classList.remove("on"); gaStreak=0; openPanel(); return; }
          $("#gaTip").textContent="再答对一题就好。";
          setTimeout(()=>{ if($("#gateAdult").classList.contains("on")) openAdultGate(false); },350);
          return;
        }
        // 答错直接关门：必须重新长按 3 秒才能再试 —— 否则固定位置反复点，每次都有 25% 命中
        gaStreak=0;
        btn.style.background="#ffb3b3";
        setTimeout(()=>{ $("#gateAdult").classList.remove("on"); },350);
      });''',
    '''      onTap(btn,()=>{
        if(gaAnswered) return;              // 本题已作答，后续点击一律无效
        gaAnswered=true;
        // 同步禁用整排按钮：否则换题前的这几百毫秒里还能在同一道题上再点一次凑 streak
        [].forEach.call(box.children,x=>{ x.disabled=true; x.style.opacity=".45"; });
        if(v===gaAnswer){
          gaStreak++;
          if(gaStreak>=2){ $("#gateAdult").classList.remove("on"); gaStreak=0; openPanel(); return; }
          $("#gaTip").textContent="再答对一题就好。";
          setTimeout(()=>{ if($("#gateAdult").classList.contains("on")) openAdultGate(false); },350);
          return;
        }
        // 答错：立刻关门 + 30 秒冷却。这样"固定位置反复猜"在时间成本上不可行。
        gaStreak=0;
        gaCooldownUntil=Date.now()+30000;
        btn.style.background="#ffb3b3";
        $("#gateAdult").classList.remove("on");
      });''')
rep("    pd.addEventListener(\"pointerdown\",e=>{ e.preventDefault(); lp=setTimeout(openAdultGate,3000); },{passive:false});",
    "    pd.addEventListener(\"pointerdown\",e=>{ e.preventDefault();\n"
    "      if(Date.now()<gaCooldownUntil) return;      // 答错后的冷却期内长按无效\n"
    "      lp=setTimeout(openAdultGate,3000); },{passive:false});")
rep('  <div id="gaTip">这是给爸爸妈妈的入口，请连续答对两题。答错会直接关闭，需要重新长按。</div>',
    '  <div id="gaTip">这是给爸爸妈妈的入口，请连续答对两题。答错会直接关闭并冷却 30 秒。</div>')

# ---------- R4-3 stopScope 顺序 + 严格令牌 ----------
rep('''  function releaseChannel(tok){
    if(tok!=null && tok!==chanToken) return;   // 不是当前占用者，忽略
    active=false; activeUntil=0;
  }''',
    '''  function releaseChannel(tok){
    if(tok!==chanToken) return;                // 严格校验：没带令牌也不许释放
    active=false; activeUntil=0;
  }''')
rep('''  function stopScope(){
    epoch++;
    clearCount();
    clearTimers();                                  // 所有 watchdog / 探针一并作废
    if(pendTimer){ clearTimeout(pendTimer); pendTimer=null; }
    if(pendItem&&!pendItem.done){ pendItem.done=true; if(pendItem._to) clearTimeout(pendItem._to); }
    pendItem=null;
    chanToken++;                                    // 让所有在途回调的令牌全部失效
    active=false; activeUntil=0;
    try{ if(engineBusy()){ S.cancel(); lastCancelAt=Date.now(); } }catch(e){}
  }''',
    '''  function stopScope(){
    // 顺序有意为之：**先记下是否在忙**，再清本地状态。
    // 反过来的话，WebKit 原生 speaking/pending 还没更新时本地标记已被清掉，
    // 旧语音就不会被 cancel，会跨世界继续播。
    const wasBusy=engineBusy();
    epoch++;
    clearCount();
    clearTimers();                                  // 所有 watchdog / 探针一并作废
    if(pendTimer){ clearTimeout(pendTimer); pendTimer=null; }
    if(pendItem&&!pendItem.done){ pendItem.done=true; if(pendItem._to) clearTimeout(pendItem._to); }
    pendItem=null;
    chanToken++;                                    // 让所有在途回调的令牌全部失效
    active=false; activeUntil=0;
    try{ if(wasBusy){ S.cancel(); lastCancelAt=Date.now(); } }catch(e){}
  }''')

# ---------- R4-4 复联角标 ----------
rep('''    o.classList.add("counted"); o.querySelector(".tag").textContent=String(ui.counted);
    o.classList.remove("hit"); void o.offsetWidth; o.classList.add("hit");
    SFX.count(ui.counted); numPop(o,ui.counted); Speech.count(cnSeq(ui.counted),"child-count");
    if(ui.counted>=q.n) T.after(700,()=>{ if(ctx.alive()&&!st.done) askTotal(); });
  }
  function askTotal(){
    ctx.answering(true);
    const apat=(ctx.symbols()&&ctx.level()>=4)?"num":pick(ANSWER_PATS.filter(p=>p!=="line"));
    const list=choices(q.n,1,10,4);''',
    '''    o.classList.add("counted"); setTag(o.querySelector(".tag"),ui.counted);
    o.classList.remove("hit"); void o.offsetWidth; o.classList.add("hit");
    SFX.count(ui.counted); numPop(o,ui.counted); Speech.count(cnSeq(ui.counted),"child-count");
    if(ui.counted>=q.n) T.after(700,()=>{ if(ctx.alive()&&!st.done) askTotal(); });
  }
  function askTotal(){
    ctx.answering(true);
    const apat=(ctx.symbols()&&ctx.level()>=4)?"num":pick(ANSWER_PATS.filter(p=>p!=="line"));
    const list=choices(q.n,1,10,4);''')

# 家长面板显示两套历史
rep('''        +"（近期正确率 "+Math.round(Store.rate(w.id)*100)+"%，跨会话窗口 "+Store.wins(w.id)+"/2）"''',
    '''        +"（近期正确率 "+Math.round(Store.rate(w.id)*100)+"%，跨启动掌握窗口 "+Store.wins(w.id)+"/2）"''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
