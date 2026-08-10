# -*- coding: utf-8 -*-
"""修复：onTap 监听器泄漏 / 提示在纠错期间乱插话"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()
n = 0


def rep(a, b):
    global s, n
    if a in s:
        s = s.replace(a, b, 1); n += 1
    else:
        print("MISS:", a[:70].replace("\n", "\\n"))


# 1) onTap：同一节点重复绑定时先摘掉旧监听（#cheer 每次通关都会重绑，否则泄漏）
rep('function onTap(node,fn){\n  let lock=0;',
    'function onTap(node,fn){\n'
    '  if(node.__tapoff){ try{ node.__tapoff(); }catch(e){} }   // 同节点重绑先摘旧的，杜绝监听器堆积\n'
    '  let lock=0;')

# 2) 一旦孩子作答，立刻收掉分级提示；新题的 ctx.ask 会重新武装
rep('function record(ctx,st,ok){\n'
    '  if(st.recorded||st.isRetry||st.hinted) return;\n'
    '  st.recorded=true; ctx.evidence(!!ok);\n'
    '}',
    'function record(ctx,st,ok){\n'
    '  ctx.clearHint();                       // 已作答 → 停止分级提示，避免在纠错动画里插话\n'
    '  if(st.recorded||st.isRetry||st.hinted) return;\n'
    '  st.recorded=true; ctx.evidence(!!ok);\n'
    '}')

# 3) Bluey 手动配对纠错需要孩子操作 → 用 ask（带分级提示），不是单纯播报
rep('    Speech.say("我们一个一个配对看看！先点上面一个，再点下面一个。",{tag:"remedy"});',
    '    ctx.ask("我们一个一个配对看看！先点上面一个，再点下面一个。",ui.A[0]);')

# 4) 汪汪队点数阶段、复联点数阶段也属于"等孩子操作"，装饰动画应暂停
rep('    ctx.ask(st.isRetry?"我们再数一次新的！点一点小海龟，数一数。":"沙滩上有小海龟！用手点一点，数一数。",objs[0]);',
    '    ctx.answering(true);\n'
    '    ctx.ask(st.isRetry?"我们再数一次新的！点一点小海龟，数一数。":"沙滩上有小海龟！用手点一点，数一数。",objs[0]);')
rep('      ctx.ask(startFrom>0?("已经有"+cnQty(startFrom)+"个啦，接着数下去！点一点后面的英雄。")\n'
    '                          :"一起数一数！点一点每一个英雄。",all[startFrom]);',
    '      ctx.answering(true);\n'
    '      ctx.ask(startFrom>0?("已经有"+cnQty(startFrom)+"个啦，接着数下去！点一点后面的英雄。")\n'
    '                          :"一起数一数！点一点每一个英雄。",all[startFrom]);')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
