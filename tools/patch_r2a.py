# -*- coding: utf-8 -*-
"""第二轮修复 A 组：
   R2-1 参与奖励与掌握证据彻底分离；解锁只看掌握，删掉"满星兜底"
   R2-3 markAssisted()：任何提示/重播/自动摆正之后，本题不再写掌握证据
   R2-2b 成人门答错立即换题（不能靠穷举四个按钮进入）
   R2-6.1 入口按钮防重入
   R2-10 底部作答区加安全区内边距
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


# ---------------- R2-1 掌握字段 ----------------
rep('  const mkW=()=>({stars:0,lv:1,hist:[],seen:0,tries:0,open:0});',
    '  // stars = 参与（陪着玩就有，给孩子看）；mast = 掌握（只由"新题+无提示"的首答累计，用于解锁）\n'
    '  const mkW=()=>({stars:0,lv:1,hist:[],seen:0,tries:0,open:0,mast:0});')
rep("        t.open=num(s.open,0)?1:0;",
    "        t.open=num(s.open,0)?1:0;\n        t.mast=clamp(Math.floor(num(s.mast,0)),0,999);")
rep('''      if(cur.open) continue;
      // 正常通路：上一个世界达到 L2 且 ⭐>=4（有掌握证据）
      // 兜底通路：⭐ 满了也开 —— 否则一个始终答错的孩子会星满却永远打不开下一个世界，
      //           而孩子界面只显示星星，没人看得出为什么卡住
      if((prev.lv>=2 && prev.stars>=4) || prev.stars>=STARS_FULL){ cur.open=1; changed=true; }''',
    '''      if(cur.open) continue;
      // 只看掌握，不看参与：上一个世界升到 L2 以上，且累计 >=4 次"新题+无提示"的首答正确。
      // 绝不能用星星兜底 —— 那等于"一直答错也能解锁"，掌握门槛就废了。
      if(prev.lv>=2 && prev.mast>=4){ cur.open=1; changed=true; }''')
rep('''    evidence(id,ok){
      const w=W(id); w.tries++;
      w.hist.push(ok?1:0); if(w.hist.length>8) w.hist.shift();''',
    '''    mastery:id=>W(id).mast,
    evidence(id,ok){
      const w=W(id); w.tries++;
      if(ok) w.mast++;
      w.hist.push(ok?1:0); if(w.hist.length>8) w.hist.shift();''')

# 地图上把"掌握"单独显示成一枚小徽章，和参与星区分开
rep('''      const st=el("div","wstars",b);
      for(let i=0;i<STARS_FULL;i++) el("i",i<n?"f":"",st);''',
    '''      const st=el("div","wstars",b);
      for(let i=0;i<STARS_FULL;i++) el("i",i<n?"f":"",st);
      const badge=el("div","mbadge",b);   // 掌握徽章：与参与星完全分开的另一套指示
      badge.innerHTML="";
      for(let i=0;i<4;i++) el("b","",badge);''')
rep('''      const st=b.querySelector(".wstars");
      if(st) [].forEach.call(st.children,(d,i)=>d.classList.toggle("f",i<n));''',
    '''      const st=b.querySelector(".wstars");
      if(st) [].forEach.call(st.children,(d,i)=>d.classList.toggle("f",i<n));
      const mb=b.querySelector(".mbadge"); const m=Store.mastery(w.id);
      if(mb) [].forEach.call(mb.children,(d,i)=>d.classList.toggle("f",i<Math.min(m,4)));''')
rep('''.world .wstars i.f{background:var(--gold);box-shadow:0 0 6px var(--gold)}''',
    '''.world .wstars i.f{background:var(--gold);box-shadow:0 0 6px var(--gold)}
/* 掌握徽章：菱形、蓝绿色 —— 和金色圆形的"参与星"在形状和颜色上都不一样 */
.world .mbadge{position:absolute;left:5px;top:5px;display:flex;gap:2px;z-index:5}
.world .mbadge b{width:clamp(6px,1.2vmin,11px);height:clamp(6px,1.2vmin,11px);display:block;
  transform:rotate(45deg);background:rgba(255,255,255,.26);border-radius:2px}
.world .mbadge b.f{background:#37d67a;box-shadow:0 0 6px #37d67a}''')

# 家长面板同时显示两套数字
rep('''      return w.name+" · "+w.skill+"：⭐"+Store.stars(w.id)+"/"+STARS_FULL+"　难度 L"+Store.level(w.id)+"　答题 "+Store.data.w[w.id].tries+lock;''',
    '''      return w.name+" · "+w.skill+"：参与⭐"+Store.stars(w.id)+"/"+STARS_FULL
        +"　掌握◆"+Store.mastery(w.id)+"　难度 L"+Store.level(w.id)
        +"　答题 "+Store.data.w[w.id].tries+lock;''')

# ---------------- R2-3 markAssisted ----------------
rep('''function newState(isRetry){ return {isRetry:!!isRetry,hinted:false,wrongs:0,recorded:false,done:false}; }''',
    '''function newState(isRetry){ return {isRetry:!!isRetry,hinted:false,wrongs:0,recorded:false,done:false}; }
/** 本题用过任何形式的帮助（自动提示/重播指令/系统代为摆正）→ 之后作答一律不计掌握 */
let CUR_STATE=null;
function bindState(st){ CUR_STATE=st; return st; }
function markAssisted(){ if(CUR_STATE) CUR_STATE.hinted=true; }''')
rep('''function record(ctx,st,ok){
  ctx.clearHint();                       // 已作答 → 停止分级提示，避免在纠错动画里插话''',
    '''function record(ctx,st,ok){
  ctx.clearHint();                       // 已作答 → 停止分级提示，避免在纠错动画里插话''')
# 每个游戏 build 时把当前题状态登记进去
for old in [
    "    st=newState(retry); q=setQ(fresh(spec,o=>o.n,box));",
    "    st=newState(retry); q=setQ(fresh(spec,o=>o.mode+\":\"+o.a+\",\"+o.b,box));",
]:
    rep(old, old.replace("st=newState(retry);", "st=bindState(newState(retry));"))
rep("    st=newState(retry);\n    const lv=ctx.level();\n    let kind=forceKind;",
    "    st=bindState(newState(retry));\n    const lv=ctx.level();\n    let kind=forceKind;")
rep("    st=newState(retry);\n    const lv=ctx.level();\n    let kind=forceKind||(lv<=2?\"ord\"",
    "    st=bindState(newState(retry));\n    const lv=ctx.level();\n    let kind=forceKind||(lv<=2?\"ord\"")
rep("    st=newState(retry);\n    const lv=ctx.level();\n    let kind=forceKind||((lv>=2&&rt%3===1)?\"pair\":\"add\");",
    "    st=bindState(newState(retry));\n    const lv=ctx.level();\n    let kind=forceKind||((lv>=2&&rt%3===1)?\"pair\":\"add\");")
rep("    st=newState(retry); posWrong=0;",
    "    st=bindState(newState(retry)); posWrong=0;")

# 三级提示的每一级都算"用过帮助"
rep('''      if(hintStage===1){ glow(); SFX.tap(); }
      else if(hintStage===2){ Speech.nudge(hintText,{tag:"hint-repeat"}); }''',
    '''      markAssisted();                       // 自动提示已经给了帮助 → 本题不计掌握
      if(hintStage===1){ glow(); SFX.tap(); }
      else if(hintStage===2){ Speech.nudge(hintText,{tag:"hint-repeat"}); }''')
# 顶栏「再说一遍」
rep('''    onTap($("#speakBtn"),()=>{
      const b=$("#speakBtn"); b.classList.add("talking");
      setTimeout(()=>b.classList.remove("talking"),1400);
      if(cur&&cur.repeat) cur.repeat();
      else if(curW) Speech.say(curW.intro,{tag:"repeat"});
    });''',
    '''    onTap($("#speakBtn"),()=>{
      const b=$("#speakBtn"); b.classList.add("talking");
      setTimeout(()=>b.classList.remove("talking"),1400);
      markAssisted();                      // 重听指令也是帮助 → 本题不计掌握
      if(cur&&cur.repeat) cur.repeat();
      else if(curW) Speech.replay(curW.intro,{tag:"repeat"});
    });''')
# 金箍棒自动摆正
rep('''  function autoFix(){
    st.asking=true; ui.okBtn.disabled=true; ctx.answering(false);''',
    '''  function autoFix(){
    markAssisted();                        // 系统代为摆正 → 本题不计掌握
    st.asking=true; ui.okBtn.disabled=true; ctx.answering(false);''')

# ---------------- R2-2b 成人门防穷举 ----------------
rep('''      onTap(btn,()=>{
        if(v===gaAnswer){ $("#gateAdult").classList.remove("on"); openPanel(); }
        else{ btn.style.background="#ffb3b3"; setTimeout(()=>btn.style.background="#fff",400); }
      });''',
    '''      onTap(btn,()=>{
        if(v===gaAnswer){ $("#gateAdult").classList.remove("on"); openPanel(); return; }
        // 答错立刻换一道新题 —— 否则孩子把四个按钮挨个点一遍必然进得去
        btn.style.background="#ffb3b3";
        setTimeout(()=>{ if($("#gateAdult").classList.contains("on")) openAdultGate(); },450);
      });''')

# ---------------- R2-6.1 入口防重入 ----------------
rep('''    $("#startBtn").addEventListener("click",function(){''',
    '''    let started=false;
    $("#startBtn").addEventListener("click",function(){
      if(started) return; started=true;      // 防重入：重复点击不能再调一次 unlockAndSay''')

# ---------------- R2-10 底部安全区 ----------------
rep('''.zbot{flex:0 0 auto;display:flex;align-items:center;justify-content:center;gap:clamp(8px,2vmin,24px);
  padding:clamp(5px,1.2vmin,14px) 8px calc(clamp(5px,1.2vmin,14px));flex-wrap:wrap}''',
    '''.zbot{flex:0 0 auto;display:flex;align-items:center;justify-content:center;gap:clamp(8px,2vmin,24px);
  padding:clamp(5px,1.2vmin,14px) calc(8px + var(--safeR)) calc(clamp(5px,1.2vmin,14px) + var(--safeB))
          calc(8px + var(--safeL));flex-wrap:wrap}''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
