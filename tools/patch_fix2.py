# -*- coding: utf-8 -*-
"""修复：
   1) 计数通道违反 cancel→speak ≥150ms（军规②）
   2) 连续答错时 wrongs 被复测题重置 → 永远等不到"直接给答案"，孩子会陷在同一轮
   3) 纠错动画偏长
   4) 暴露 __qn 轮次计数（测试用来确认新题已经建好）
"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()
n = 0; miss = []


def rep(a, b, cnt=1):
    global s, n
    if a in s:
        s = s.replace(a, b, cnt); n += 1
    else:
        miss.append(a[:78].replace("\n", "\\n"))


# ---------- 1) 计数通道遵守 cancel 间隔 ----------
rep('    const flush=()=>{\n'
    '      cntTimer=null;\n'
    '      if(cntLatest==null) return;\n'
    '      if(busy()){ cntTimer=setTimeout(flush,120); return; }   // 等空闲，不打断',
    '    const flush=()=>{\n'
    '      cntTimer=null;\n'
    '      if(cntLatest==null) return;\n'
    '      // 军规②：cancel 之后必须等满 CANCEL_GAP，计数通道也不例外\n'
    '      const gap=Date.now()-lastCancelAt;\n'
    '      if(gap<CANCEL_GAP){ cntTimer=setTimeout(flush,CANCEL_GAP-gap+10); return; }\n'
    '      if(pendTimer){ cntTimer=setTimeout(flush,120); return; } // 有待播指令时让路\n'
    '      if(busy()){ cntTimer=setTimeout(flush,120); return; }   // 等空闲，绝不打断')

# ---------- 4) 轮次计数 ----------
rep('function setQ(o){ window.__q=o; return o; }',
    'function setQ(o){ window.__q=o; window.__qn=(window.__qn||0)+1; return o; }')

# ---------- 2) 每一轮最多错两次，之后必定给答案并带着孩子过关 ----------
# 佩奇
rep('GAMES.peppa=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,shownAt=0;',
    'GAMES.peppa=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,shownAt=0,fails=0;')
rep('      if(st.wrongs>=2){ reveal(wrap); return; }\n      lockCards(wrap); ctx.answering(false);\n      remediate();',
    '      fails++;\n'
    '      if(st.wrongs>=2||fails>=2){ reveal(wrap); return; }   // 一轮内最多错两次\n'
    '      lockCards(wrap); ctx.answering(false);\n      remediate();')
rep('    start:()=>build(false), next:()=>build(false),\n'
    '    repeat:()=>{ if(ui&&ui.pig)',
    '    start:()=>{ fails=0; build(false); }, next:()=>{ fails=0; build(false); },\n'
    '    repeat:()=>{ if(ui&&ui.pig)')
# 汪汪队
rep('GAMES.paw=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0;',
    'GAMES.paw=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0,fails=0;')
rep('        lockCards(wrap);\n        if(st.wrongs>=2){ revealCard(wrap,target); return; }',
    '        lockCards(wrap); fails++;\n        if(st.wrongs>=2||fails>=2){ revealCard(wrap,target); return; }')
rep('      if(st.wrongs>=2){ giveAnswer(); return; }\n      remedyGiveN(got);',
    '      fails++;\n      if(st.wrongs>=2||fails>=2){ giveAnswer(); return; }\n      remedyGiveN(got);')
rep('    start:()=>{ rt=0; build(false); }, next:()=>build(false),\n'
    '    repeat:()=>{ if(!q) return;\n      Speech.say(q.kind==="given"',
    '    start:()=>{ rt=0; fails=0; build(false); }, next:()=>{ fails=0; build(false); },\n'
    '    repeat:()=>{ if(!q) return;\n      Speech.say(q.kind==="given"')
# Bluey
rep('GAMES.bluey=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null;',
    'GAMES.bluey=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,fails=0;')
rep('      if(st.wrongs>=2){ verify(()=>{ revealWho(wrap); }); return; }\n      handPair();',
    '      fails++;\n      if(st.wrongs>=2||fails>=2){ verify(()=>{ revealWho(wrap); }); return; }\n      handPair();')
rep('        if(st.wrongs>=2){ verify(()=>{ st.done=true; T.after(300,()=>ctx.win(basket)); }); return; }\n'
    '        verify(()=>{ if(ctx.alive()) build(true); });',
    '        fails++;\n'
    '        if(st.wrongs>=2||fails>=2){ verify(()=>{ st.done=true; T.after(300,()=>ctx.win(basket)); }); return; }\n'
    '        verify(()=>{ if(ctx.alive()) build(true); });')
rep('    start:()=>build(false), next:()=>build(false),\n'
    '    repeat:()=>Speech.say(q&&q.mode==="fix"',
    '    start:()=>{ fails=0; build(false); }, next:()=>{ fails=0; build(false); },\n'
    '    repeat:()=>Speech.say(q&&q.mode==="fix"')
# 葫芦山
rep('GAMES.hulu=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0;',
    'GAMES.hulu=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0,fails=0;')
rep('      if(st.wrongs>=2){ ordReveal(gs); return; }\n      ctx.answering(false); ordRemedy(gs);',
    '      fails++;\n      if(st.wrongs>=2||fails>=2){ ordReveal(gs); return; }\n'
    '      ctx.answering(false); ordRemedy(gs);')
rep('        if(st.wrongs>=2){ missReveal(); return; }\n        missRemedy();',
    '        fails++;\n        if(st.wrongs>=2||fails>=2){ missReveal(); return; }\n        missRemedy();')
rep('    start:()=>{ rt=0; build(false); }, next:()=>build(false),\n'
    '    repeat:()=>{ if(!q) return;\n      Speech.say(q.kind==="ord"',
    '    start:()=>{ rt=0; fails=0; build(false); }, next:()=>{ fails=0; build(false); },\n'
    '    repeat:()=>{ if(!q) return;\n      Speech.say(q.kind==="ord"')
# 复联
rep('GAMES.aveng=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0;',
    'GAMES.aveng=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0,fails=0;')
rep('        lockCards(wrap);\n        if(st.wrongs>=2){\n          st.done=true; ctx.answering(false);',
    '        lockCards(wrap); fails++;\n        if(st.wrongs>=2||fails>=2){\n          st.done=true; ctx.answering(false);')
rep('      lockCards(wrap); ctx.answering(false);\n      if(st.wrongs>=2){\n        st.done=true;\n'
    '        [].forEach.call(wrap.children,(x,i)=>{ const k=["less","same","more"][i];',
    '      lockCards(wrap); ctx.answering(false); fails++;\n      if(st.wrongs>=2||fails>=2){\n        st.done=true;\n'
    '        [].forEach.call(wrap.children,(x,i)=>{ const k=["less","same","more"][i];')
rep('    start:()=>{ rt=0; build(false); }, next:()=>build(false),\n'
    '    repeat:()=>{ if(!q) return;\n      Speech.say(q.kind==="pair"',
    '    start:()=>{ rt=0; fails=0; build(false); }, next:()=>{ fails=0; build(false); },\n'
    '    repeat:()=>{ if(!q) return;\n      Speech.say(q.kind==="pair"')
# 花果山
rep('GAMES.monkey=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null;',
    'GAMES.monkey=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,fails=0;')
rep('      if(st.wrongs>=2){ reveal(); return; }\n      remedy();',
    '      fails++;\n      if(st.wrongs>=2||fails>=2){ reveal(); return; }\n      remedy();')
rep('    start:()=>build(false), next:()=>build(false),\n'
    '    repeat:()=>{ if(!q) return;\n      Speech.say(q.mode==="reach"',
    '    start:()=>{ fails=0; build(false); }, next:()=>{ fails=0; build(false); },\n'
    '    repeat:()=>{ if(!q) return;\n      Speech.say(q.mode==="reach"')

# ---------- 3) 纠错节奏收紧（3 岁半的耐心有限） ----------
rep('    Speech.say("看，一共要"+cnQty(q.N)+"格。山洞已经有"+cnQty(q.a)+"个了。",{tag:"remedy"});\n'
    '    T.after(1800,()=>{', '    Speech.say("看，一共要"+cnQty(q.N)+"格。山洞已经有"+cnQty(q.a)+"个了。",{tag:"remedy"});\n'
    '    T.after(1400,()=>{')
rep('          Speech.say("还差"+cnQty(q.need)+"个。我们再试一个新的！",{tag:"remedy"});\n'
    '          T.after(2600,()=>{', '          Speech.say("还差"+cnQty(q.need)+"个。我们再试一个新的！",{tag:"remedy"});\n'
    '          T.after(2000,()=>{')
rep('        k++; T.after(700,blink);', '        k++; T.after(600,blink);')
rep('        Speech.say("合起来是"+cnQty(n)+"个！我们再看一次新的。",{tag:"remedy"});\n'
    '        T.after(2200,()=>{', '        Speech.say("合起来是"+cnQty(n)+"个！我们再看一次新的。",{tag:"remedy"});\n'
    '        T.after(1800,()=>{')
rep('          Speech.say("看，就是这样。我们再试一个新的！",{tag:"remedy"});\n'
    '          T.after(2400,()=>{', '          Speech.say("看，就是这样。我们再试一个新的！",{tag:"remedy"});\n'
    '          T.after(1900,()=>{')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
