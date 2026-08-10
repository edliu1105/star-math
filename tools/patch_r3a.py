# -*- coding: utf-8 -*-
"""第三轮修复 A 组（iOS 语音四条 + 两处抢点 + 成人门 + 徽章）：
   R3-6.1 say() 判忙用的是原生 busy()，绕过了本地 active → 统一用 engineBusy()
   R3-6.2 两条通道共用一个 active/activeUntil；stopScope() 不清 watchdog
          → 每条 utterance 带 {epoch, token}，回调只释放匹配的 token；所有 timeout 登记后统一清除
   R3-6.3 顶栏重播走各游戏的 Speech.say()，绕过了受控 replay()
          → repeat() 改为返回文本，由顶栏统一 replay()
   R3-6.4 补说发声后 firstOk 不更新 → 补说项带 isFirst 标记
   R3-4.1 花果山预置动画期间可抢点；Bluey 新增物体删除监听只查 st.done
   R3-2.1 成人门答错后仍可固定位置反复猜 → 答错立即关门，需重新长按；并要连答两题
   R3-3.2 掌握徽章 4 格封顶但门槛是 6 → 改成 6 格
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


# ---------- 6.2 通道 token + timeout 登记 ----------
rep('''  let active=false, activeUntil=0;      // 本地忙标记：不能只信 WebKit 的 speaking/pending
  let epoch=0;                          // 路由作用域，换世界即作废旧的一切''',
    '''  let active=false, activeUntil=0;      // 本地忙标记：不能只信 WebKit 的 speaking/pending
  let chanToken=0;                      // 通道令牌：只有持有当前令牌的回调才能释放通道
  let epoch=0;                          // 路由作用域，换世界即作废旧的一切
  const timers=new Set();               // 所有 watchdog / 探针，换 scope 时统一清掉
  function later(fn,ms){ const id=setTimeout(()=>{ timers.delete(id); fn(); },ms); timers.add(id); return id; }
  function clearTimers(){ timers.forEach(clearTimeout); timers.clear(); }''')

rep('''  function holdChannel(text){ active=true; activeUntil=Date.now()+Math.max(2500,(text||"").length*380); }
  function releaseChannel(){ active=false; activeUntil=0; }''',
    '''  /** 占用通道并返回本次的令牌；释放时必须带回同一个令牌，
      否则旧 utterance 的 onend 会把新世界正在说的那句"释放"掉。 */
  function holdChannel(text){
    active=true; activeUntil=Date.now()+Math.max(2500,(text||"").length*380);
    return ++chanToken;
  }
  function releaseChannel(tok){
    if(tok!=null && tok!==chanToken) return;   // 不是当前占用者，忽略
    active=false; activeUntil=0;
  }''')

# ---------- 6.1 say() 用 engineBusy ----------
rep('''    const item={id,text,opt,done:false,ep:epoch}; pendItem=item;
    if(busy()){''',
    '''    const item={id,text,opt,done:false,ep:epoch}; pendItem=item;
    if(engineBusy()){                     // 必须"原生状态 或 本地标记"取或，否则本地 active 形同虚设''')

# ---------- fire(): token + later() + 补说标记 ----------
rep('''    const u=mk(item.text,item.opt);
    const fin=()=>{ if(!item.done){ releaseChannel(); finish(item); } };
    u.onend=fin; u.onerror=fin;
    item._to=setTimeout(fin, Math.max(2500,item.text.length*380));  // 军规3 超时兜底
    holdChannel(item.text);                            // 立刻占用通道，不等 WebKit 状态位
    try{ S.speak(u); }catch(e){ fin(); }
    setTimeout(()=>{                                    // 军规3 轮询判定
      if(item.ep!==epoch) return;
      if(busy()){ engineSeen=true; hideHint(); if(item.id===1) markFirstOk(); }
      if(item.id===1){ firstProbed=true; if(!firstOk) showHint(); }
      notify();
    },450);''',
    '''    const u=mk(item.text,item.opt);
    const tok=holdChannel(item.text);                  // 立刻占用通道，不等 WebKit 状态位
    const fin=()=>{ if(!item.done){ releaseChannel(tok); finish(item); } };
    u.onend=fin; u.onerror=fin;
    item._to=later(fin, Math.max(2500,item.text.length*380));  // 军规3 超时兜底
    try{ S.speak(u); }catch(e){ fin(); }
    later(()=>{                                        // 军规3 轮询判定
      if(item.ep!==epoch) return;
      const isFirst=(item.id===1)||item.opt.isFirst===true;
      if(busy()){ engineSeen=true; hideHint(); if(isFirst) markFirstOk(); }
      if(isFirst){ firstProbed=true; if(!firstOk) showHint(); }
      notify();
    },450);''')

# ---------- 计数通道：带 token ----------
rep('''      const u=mk(t,{rate:.95});
      let released=false;
      const rel=()=>{ if(released) return; released=true; releaseChannel();
        if(ep===epoch && cntLatest!=null && !cntTimer) cntTimer=setTimeout(flush,40); };
      u.onend=u.onerror=rel;
      holdChannel(t);
      try{ S.speak(u); }catch(e){ rel(); }
      // 计数通道也要有 watchdog：WebKit 不触发 onend 时不能把通道永久占住
      setTimeout(rel, Math.max(1200, t.length*420));
      setTimeout(()=>{ if(ep===epoch && busy()){ engineSeen=true; hideHint(); } },450);''',
    '''      const u=mk(t,{rate:.95});
      const tok=holdChannel(t);
      let released=false;
      const rel=()=>{ if(released) return; released=true; releaseChannel(tok);
        if(ep===epoch && cntLatest!=null && !cntTimer) cntTimer=setTimeout(flush,40); };
      u.onend=u.onerror=rel;
      try{ S.speak(u); }catch(e){ rel(); }
      // 计数通道也要有 watchdog：WebKit 不触发 onend 时不能把通道永久占住
      later(rel, Math.max(1200, t.length*420));
      later(()=>{ if(ep===epoch && busy()){ engineSeen=true; hideHint(); } },450);''')

# ---------- unlockAndSay: token ----------
rep('''    const u=mk(text,{});
    u.onend=u.onerror=()=>{ releaseChannel(); notify(); };
    holdChannel(text);
    try{ S.speak(u); }catch(e){ releaseChannel(); }
    setTimeout(()=>{''',
    '''    const u=mk(text,{});
    const tok=holdChannel(text);
    u.onend=u.onerror=()=>{ releaseChannel(tok); notify(); };
    try{ S.speak(u); }catch(e){ releaseChannel(tok); }
    later(()=>{''')

# ---------- 6.4 补说带 isFirst ----------
rep('      redoneFirst=true; say(firstText,{tag:"redo-first"});',
    '      redoneFirst=true; say(firstText,{tag:"redo-first",isFirst:true});')

# ---------- stopScope: 清 timers + 用 engineBusy 判断是否需要打断 ----------
rep('''  function stopScope(){
    epoch++;
    clearCount();
    if(pendTimer){ clearTimeout(pendTimer); pendTimer=null; }
    if(pendItem&&!pendItem.done){ pendItem.done=true; if(pendItem._to) clearTimeout(pendItem._to); }
    pendItem=null;
    releaseChannel();
    try{ if(busy()){ S.cancel(); lastCancelAt=Date.now(); } }catch(e){}
  }''',
    '''  function stopScope(){
    epoch++;
    clearCount();
    clearTimers();                                  // 所有 watchdog / 探针一并作废
    if(pendTimer){ clearTimeout(pendTimer); pendTimer=null; }
    if(pendItem&&!pendItem.done){ pendItem.done=true; if(pendItem._to) clearTimeout(pendItem._to); }
    pendItem=null;
    chanToken++;                                    // 让所有在途回调的令牌全部失效
    active=false; activeUntil=0;
    try{ if(engineBusy()){ S.cancel(); lastCancelAt=Date.now(); } }catch(e){}
  }''')

# ---------- 6.3 顶栏重播统一走 replay ----------
rep('''      markAssisted();                      // 重听指令也是帮助 → 本题不计掌握
      if(cur&&cur.repeat) cur.repeat();
      else if(curW) Speech.replay(curW.intro,{tag:"repeat"});''',
    '''      markAssisted();                      // 重听指令也是帮助 → 本题不计掌握
      // repeat() 只负责返回"当前这一步该说什么"，实际播报统一走受控 replay()
      const txt=(cur&&cur.repeat&&cur.repeat())||(curW&&curW.intro);
      if(txt) Speech.replay(txt,{tag:"repeat"});''')

# 六个 repeat() 改成返回文本
rep('    repeat:()=>{ if(ui&&ui.pig) Speech.say("佩奇跳泥坑，溅起几个泥点呀？",{tag:"repeat"}); },',
    '    repeat:()=>(ui&&ui.pig)?"佩奇跳泥坑，溅起几个泥点呀？":"",')
rep('''    repeat:()=>{ if(!q) return;
      if(q.kind==="given"){ Speech.say("看看卡片上有几个点，就派出正好几只狗狗。",{tag:"repeat"}); return; }
      if(ui&&ui.objs&&ui.counted<q.n){ Speech.say("点一点小海龟，数一数。",{tag:"repeat"}); return; }
      Speech.say(q.kind==="plus1"?"再来一只，一共几只呀？":"一共几只呀？点一张卡片。",{tag:"repeat"}); },''',
    '''    repeat:()=>{ if(!q) return "";
      if(q.kind==="given") return "看看卡片上有几个点，就派出正好几只狗狗。";
      if(ui&&ui.objs&&ui.counted<q.n) return "点一点小海龟，数一数。";
      return q.kind==="plus1"?"再来一只，一共几只呀？":"一共几只呀？点一张卡片。"; },''')
rep('    repeat:()=>Speech.say(q&&q.mode==="fix"?"点篮子，给 Bingo 加到一样多。":"谁的多呀？",{tag:"repeat"}),',
    '    repeat:()=>(q&&q.mode==="fix")?"点篮子，给 Bingo 加到一样多。":"谁的多呀？",')
rep('''    repeat:()=>{ if(!q) return;
      Speech.say(q.kind==="ord"?("点一点第"+cnSeq(q.target)+"个葫芦。")
        :q.kind==="missing"?("山洞有"+cnQty(q.a)+"个，一共要"+cnQty(q.N)+"个，山顶还要几个？")
        :"两条路都要有人，你来分！",{tag:"repeat"}); },''',
    '''    repeat:()=>{ if(!q) return "";
      return q.kind==="ord"?("点一点第"+cnSeq(q.target)+"个葫芦。")
        :q.kind==="missing"?("山洞有"+cnQty(q.a)+"个，一共要"+cnQty(q.N)+"个，山顶还要几个？")
        :"两条路都要有人，你来分！"; },''')
rep('''    repeat:()=>{ if(!q) return;
      if(q.kind==="pair"){ Speech.say("先点一个英雄，再点一个坏蛋。",{tag:"repeat"}); return; }
      if(!st||!st.assembled){ Speech.say("按黄色按钮，让两边的英雄合到一起。",{tag:"repeat"}); return; }
      if(ui&&ui.merged&&ui.counted<q.n){ Speech.say("点一点每一个英雄，数一数。",{tag:"repeat"}); return; }
      Speech.say("一共几个英雄呀？点一张卡片。",{tag:"repeat"}); },''',
    '''    repeat:()=>{ if(!q) return "";
      if(q.kind==="pair") return "先点一个英雄，再点一个坏蛋。";
      if(!st||!st.assembled) return "按黄色按钮，让两边的英雄合到一起。";
      if(ui&&ui.merged&&ui.counted<q.n) return "点一点每一个英雄，数一数。";
      return "一共几个英雄呀？点一张卡片。"; },''')
rep('''    repeat:()=>{ if(!q) return;
      if(st&&st.asking){ Speech.say("你一共加了几格呀？点一张卡片。",{tag:"repeat"}); return; }
      Speech.say(q.mode==="reach"?"桥要搭到亮着的那个石墩，接着往前点。"
        :(q.pre>0?("已经有"+cnQty(q.pre)+"格，再变长"+cnQty(q.need)+"格。")
                 :("把金箍棒变长"+cnQty(q.need)+"格。")),{tag:"repeat"}); },''',
    '''    repeat:()=>{ if(!q) return "";
      if(st&&st.asking) return "你一共加了几格呀？点一张卡片。";
      return q.mode==="reach"?"桥要搭到亮着的那个石墩，接着往前点。"
        :(q.pre>0?("已经有"+cnQty(q.pre)+"格，再变长"+cnQty(q.need)+"格。")
                 :("把金箍棒变长"+cnQty(q.need)+"格。")); },''')

# ---------- 4.1 花果山预置期锁题 ----------
rep('''    if(q.pre>0){
      Speech.say("悟空先把金箍棒变长"+cnQty(q.pre)+"格！",{tag:"g:monkey"});
      let k=0;
      const pre=()=>{
        if(!ctx.alive()) return;
        if(k>=q.pre){ T.after(500,askNow); return; }
        grow(true); k++; T.after(680,pre);
      };
      T.after(1200,pre);
    }else T.after(1200,askNow);''',
    '''    if(q.pre>0){
      st.locked=true; const my=st;          // 预置动画期间禁止抢点，否则长度会被孩子提前改掉
      Speech.say("悟空先把金箍棒变长"+cnQty(q.pre)+"格！",{tag:"g:monkey"});
      let k=0;
      const pre=()=>{
        if(!ctx.alive()||st!==my) return;
        if(k>=q.pre){ T.after(500,()=>{ if(ctx.alive()&&st===my){ st.locked=false; askNow(); } }); return; }
        grow(true); k++; T.after(680,pre);
      };
      T.after(1200,pre);
    }else T.after(1200,askNow);''')

# ---------- 4.1b Bluey 新增物体删除监听 ----------
rep('      onTap(o,()=>{ if(st.done) return; const i=ui.B.indexOf(o); if(i<q.b) return;',
    '      onTap(o,()=>{ if(busyState(st)) return; const i=ui.B.indexOf(o); if(i<q.b) return;')

# ---------- 2.1 成人门：答错立即关门 + 连答两题 ----------
rep('''  let gaAnswer=0;
  function openAdultGate(){
    const a=rint(6,9), b=rint(5,9); gaAnswer=a+b;''',
    '''  let gaAnswer=0, gaStreak=0;
  function openAdultGate(reset){
    if(reset!==false) gaStreak=0;
    const a=rint(6,9), b=rint(5,9); gaAnswer=a+b;''')
rep('''      onTap(btn,()=>{
        if(v===gaAnswer){ $("#gateAdult").classList.remove("on"); openPanel(); return; }
        // 答错立刻换一道新题 —— 否则孩子把四个按钮挨个点一遍必然进得去
        btn.style.background="#ffb3b3";
        setTimeout(()=>{ if($("#gateAdult").classList.contains("on")) openAdultGate(); },450);
      });''',
    '''      onTap(btn,()=>{
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
      });''')
rep('  <div id="gaTip">这是给爸爸妈妈的入口，请先回答上面的题目。</div>',
    '  <div id="gaTip">这是给爸爸妈妈的入口，请连续答对两题。答错会直接关闭，需要重新长按。</div>')

# ---------- 3.2 掌握徽章 6 格 ----------
rep('      for(let i=0;i<4;i++) el("b","",badge);',
    '      for(let i=0;i<6;i++) el("b","",badge);   // 与门槛 mast>=6 一致')
rep('      if(mb) [].forEach.call(mb.children,(d,i)=>d.classList.toggle("f",i<Math.min(m,4)));',
    '      if(mb) [].forEach.call(mb.children,(d,i)=>d.classList.toggle("f",i<Math.min(m,6)));')

# ---------- 5.2 Assets 失败不缓存成功 ----------
rep('''  function one(src){ return new Promise(res=>{
    if(done.has(src)) return res();
    const im=new Image();
    im.onload=im.onerror=()=>{ done.add(src); res(); };
    im.src=src;
  }); }''',
    '''  function one(src){ return new Promise(res=>{
    if(done.has(src)) return res();
    const im=new Image();
    let fin=false;
    const end=ok=>{ if(fin) return; fin=true; if(ok) done.add(src); res(); };  // 失败不写成功缓存
    im.onload=()=>end(true);
    im.onerror=()=>end(false);
    setTimeout(()=>end(false),8000);                                          // 超时兜底
    im.src=src;
  }); }''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
