# -*- coding: utf-8 -*-
"""第二轮修复 B 组（iOS 语音）：
   R2-6.6 voiceschanged 补说：引擎忙不再直接判成功，而是**重排**直到真的补说或被新的入口语音取代
   R2-6.9 「首句成功」与「检测到引擎活动」拆成两个状态，后续任何语音不能把首句误报成成功
   R2-6.3/6.8 两条通道都维护本地 active 标记与 watchdog，不再只依赖原生 speaking/pending
   R2-6.7 顶栏重播 / 声音提示条统一走受控 API（安全打断 + 节流）
   R2-4.2 离开世界时 Speech.stopScope()：废弃待播、失效旧 watchdog、安全打断
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


rep('''  let firstText=null,firstOk=false,firstProbed=false,redoneFirst=false;
  let serial=0; const subs=[];''',
    '''  let firstText=null,firstOk=false,firstProbed=false,redoneFirst=false,firstRedoTimer=null;
  let engineSeen=false;                 // 「检测到引擎有过发声活动」—— 与「首句成功」是两回事
  let active=false, activeUntil=0;      // 本地忙标记：不能只信 WebKit 的 speaking/pending
  let epoch=0;                          // 路由作用域，换世界即作废旧的一切
  let serial=0; const subs=[];''')

rep('''  function busy(){ try{ return !!(S&&(S.speaking||S.pending)); }catch(e){ return false; } }''',
    '''  function busy(){ try{ return !!(S&&(S.speaking||S.pending)); }catch(e){ return false; } }
  /** 判忙必须"原生状态 或 本地标记"取或 —— WebKit 的状态位更新可能滞后 */
  function engineBusy(){ return busy() || (active && Date.now()<activeUntil); }
  function holdChannel(text){ active=true; activeUntil=Date.now()+Math.max(2500,(text||"").length*380); }
  function releaseChannel(){ active=false; activeUntil=0; }''')

# fire(): 作用域校验 + 本地忙标记 + 首句/引擎活动分离
rep('''  function fire(item){
    pendTimer=null; pendItem=null;
    if(!OK){ finish(item); return; }
    try{ S.resume(); }catch(e){}                       // 军规4
    const u=mk(item.text,item.opt);
    const fin=()=>{ if(!item.done) finish(item); };
    u.onend=fin; u.onerror=fin;
    item._to=setTimeout(fin, Math.max(2500,item.text.length*380));  // 军规3 超时兜底
    try{ S.speak(u); }catch(e){ fin(); }
    setTimeout(()=>{                                    // 军规3 轮询判定
      if(busy()) markOk();
      if(item.id===1){ firstProbed=true; if(!firstOk) showHint(); }
      notify();
    },450);
  }''',
    '''  function fire(item){
    pendTimer=null; pendItem=null;
    if(item.ep!==epoch){ item.done=true; return; }     // 换过世界了，这条作废
    if(!OK){ finish(item); return; }
    try{ S.resume(); }catch(e){}                       // 军规4
    const u=mk(item.text,item.opt);
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
    },450);
  }''')

rep('''  function markOk(){ if(!firstOk){ firstOk=true; state="READY"; hideHint(); notify(); } }''',
    '''  function markFirstOk(){
    if(firstOk) return;
    firstOk=true; state="READY";
    if(firstRedoTimer){ clearTimeout(firstRedoTimer); firstRedoTimer=null; }
    hideHint(); notify();
  }''')

# say(): 带上 epoch
rep('''    const item={id,text,opt,done:false}; pendItem=item;''',
    '''    const item={id,text,opt,done:false,ep:epoch}; pendItem=item;''')

# 计数通道：本地忙判定 + watchdog
rep('''      if(busy()){ cntTimer=setTimeout(flush,120); return; }   // 等空闲，绝不打断
      const t=cntLatest; cntLatest=null;
      try{ S.resume(); }catch(e){}
      const u=mk(t,{rate:.95});
      u.onend=u.onerror=()=>{ if(cntLatest!=null&&!cntTimer) cntTimer=setTimeout(flush,40); };
      try{ S.speak(u); }catch(e){}
      setTimeout(()=>{ if(busy()) markOk(); },450);
      if(cntLatest!=null&&!cntTimer) cntTimer=setTimeout(flush,260);''',
    '''      if(engineBusy()){ cntTimer=setTimeout(flush,120); return; }  // 等空闲，绝不打断
      const t=cntLatest; cntLatest=null;
      const ep=epoch;
      try{ S.resume(); }catch(e){}
      const u=mk(t,{rate:.95});
      let released=false;
      const rel=()=>{ if(released) return; released=true; releaseChannel();
        if(ep===epoch && cntLatest!=null && !cntTimer) cntTimer=setTimeout(flush,40); };
      u.onend=u.onerror=rel;
      holdChannel(t);
      try{ S.speak(u); }catch(e){ rel(); }
      // 计数通道也要有 watchdog：WebKit 不触发 onend 时不能把通道永久占住
      setTimeout(rel, Math.max(1200, t.length*420));
      setTimeout(()=>{ if(ep===epoch && busy()){ engineSeen=true; hideHint(); } },450);''')

# unlockAndSay：首句成功单独判定
rep('''    const u=mk(text,{}); u.onend=notify; u.onerror=notify;
    try{ S.speak(u); }catch(e){}
    setTimeout(()=>{ if(busy()) markOk(); firstProbed=true; if(!firstOk) showHint(); notify(); },450);
    return id;''',
    '''    const u=mk(text,{});
    u.onend=u.onerror=()=>{ releaseChannel(); notify(); };
    holdChannel(text);
    try{ S.speak(u); }catch(e){ releaseChannel(); }
    setTimeout(()=>{
      if(busy()){ engineSeen=true; hideHint(); markFirstOk(); }
      firstProbed=true; if(!firstOk) showHint(); notify();
    },450);
    return id;''')

# nudge 用本地忙判定
rep('''  function nudge(text,opt){
    const now=Date.now();
    if(busy()) return false;''',
    '''  function nudge(text,opt){
    const now=Date.now();
    if(engineBusy()) return false;''')

# voiceschanged：重排而不是放弃，且不再把"引擎忙"当成首句成功
rep('''  function onVoicesChanged(){
    const before=voice, v=refreshVoice(); notify();
    if(!v||redoneFirst||firstOk||!firstText) return;
    if(before&&before.name===v.name) return;
    setTimeout(()=>{
      if(redoneFirst||firstOk) return;
      if(busy()){ markOk(); return; }
      if(sinceReq()<NO_INTERRUPT) return;
      redoneFirst=true; say(firstText,{tag:"redo-first"});
    }, Math.max(0,NO_INTERRUPT-sinceReq())+60);
  }''',
    '''  function scheduleFirstRedo(){
    if(redoneFirst||firstOk||!firstText||firstRedoTimer) return;
    firstRedoTimer=setTimeout(()=>{
      firstRedoTimer=null;
      if(redoneFirst||firstOk) return;
      // 引擎忙或刚请求过 → **重排**，不是放弃，也绝不把这当成"首句成功"
      if(engineBusy()||sinceReq()<NO_INTERRUPT){ scheduleFirstRedo(); return; }
      redoneFirst=true; say(firstText,{tag:"redo-first"});
    }, Math.max(0,NO_INTERRUPT-sinceReq())+80);
  }
  function onVoicesChanged(){
    const before=voice, v=refreshVoice(); notify();
    if(!v||redoneFirst||firstOk||!firstText) return;
    if(before&&before.name===v.name) return;
    scheduleFirstRedo();
  }''')

# 提示条：用"是否检测到引擎活动"判定，而不是首句
rep('''  let hintShown=false;
  function showHint(){ if(hintShown||firstOk) return; hintShown=true; $("#soundHint").classList.add("on"); }''',
    '''  let hintShown=false;
  function showHint(){ if(hintShown||engineSeen) return; hintShown=true; $("#soundHint").classList.add("on"); }''')

# 受控重播 + 作用域停止
rep('''  return { ok:OK, say, count, clearCount, unlockAndSay, nudge, busy, sinceReq, refreshVoice, hideHint,''',
    '''  /** 用户主动要求重听：安全打断（latest-wins）+ 短节流，防止连点排长队 */
  let lastReplay=0;
  function replay(text,opt){
    const now=Date.now();
    if(now-lastReplay<800) return 0;
    lastReplay=now;
    return say(text,opt||{tag:"replay"});
  }
  /** 换世界/回地图：废弃待播、失效旧 watchdog、安全打断当前 */
  function stopScope(){
    epoch++;
    clearCount();
    if(pendTimer){ clearTimeout(pendTimer); pendTimer=null; }
    if(pendItem&&!pendItem.done){ pendItem.done=true; if(pendItem._to) clearTimeout(pendItem._to); }
    pendItem=null;
    releaseChannel();
    try{ if(busy()){ S.cancel(); lastCancelAt=Date.now(); } }catch(e){}
  }
  return { ok:OK, say, count, clearCount, unlockAndSay, nudge, replay, stopScope,
    busy, engineBusy, sinceReq, refreshVoice, hideHint,''')

rep('''      diag(){ let a=[]; try{a=S?(S.getVoices()||[]):[];}catch(e){}
      return { all:a.length, zh:zhVoices(),
        cur:voice?(voice.name+"  ["+voice.lang+"]"):"（无中文声音，画面仍可完整游玩）",
        speaking:busy(), firstOk, firstProbed, tries }; }''',
    '''      diag(){ let a=[]; try{a=S?(S.getVoices()||[]):[];}catch(e){}
      return { all:a.length, zh:zhVoices(),
        cur:voice?(voice.name+"  ["+voice.lang+"]"):"（无中文声音，画面仍可完整游玩）",
        speaking:engineBusy(), engineSeen, firstOk, firstProbed, redone:redoneFirst,
        pendingRedo:!!firstRedoTimer, tries }; }''')

# 诊断面板：把两个状态分开显示
rep('''    <div><b>首句是否成功：</b><span id="dgFirst">-</span></div>''',
    '''    <div><b>检测到语音引擎活动：</b><span id="dgSeen">-</span></div>
    <div><b>第一句是否确认发声：</b><span id="dgFirst">-</span></div>''')
rep('''    $("#dgFirst").textContent=d.firstOk?"成功 ✅":(d.firstProbed?"未检测到发声 ⚠️":"尚未检测");''',
    '''    $("#dgSeen").textContent=d.engineSeen?"是 ✅":"否 ⚠️";
    $("#dgFirst").textContent=d.firstOk?"是 ✅"
      :(d.pendingRedo?"待用新声音补说…":(d.redone?"已补说一次":(d.firstProbed?"未检测到发声 ⚠️":"尚未检测")));''')

# 声音提示条也走受控 API
rep('''      SFX.gesture(); Audio2.kick(); Speech.refreshVoice();
      Speech.say("你好呀！听得到我说话吗？",{tag:"hint-retry"});''',
    '''      SFX.gesture(); Audio2.kick(); Speech.refreshVoice();
      Speech.replay("你好呀！听得到我说话吗？",{tag:"hint-retry"});''')

# 离开世界时收掉语音作用域
rep('''  function leave(){
    clearHint(); Speech.clearCount(); Finger.off(); Bubble.hide();''',
    '''  function leave(){
    clearHint(); Speech.stopScope(); Finger.off(); Bubble.hide();''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
