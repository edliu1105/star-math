# -*- coding: utf-8 -*-
"""Bluey 比较关的"长度线索"三级梯度：
   L1 固定间距 —— 排得越长就是越多，允许用知觉直接比（这是三岁半正常的第一策略）
   L2 两排铺满同样宽度 —— 长度线索被抹掉，必须去看数量本身
   L3 守恒 —— 数量相同、只有间距不同，外观主动误导
   L4 补齐到一样多
   原来 L1/L2 都用铺满，等于跳过了第一级，而且会顺手教出"排得开=更少"的错误概括。"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()
n = 0


def rep(a, b):
    global s, n
    if a in s:
        s = s.replace(a, b, 1); n += 1
    else:
        print("MISS:", a[:76].replace("\n", "\\n"))


# 固定间距排布助手
rep('function rowPos(n){ const o=[],st=84/n; for(let i=0;i<n;i++) o.push([8+st*(i+.5),50]); return o; }',
    'function rowPos(n){ const o=[],st=84/n; for(let i=0;i<n;i++) o.push([8+st*(i+.5),50]); return o; }\n'
    '/** 固定间距：按 slots 个槽位的间距摆 n 个 —— 数量越多，排出来就越长 */\n'
    'function rowFixed(n,slots){ const o=[],st=84/Math.max(slots,1);\n'
    '  for(let i=0;i<n;i++) o.push([8+st*(i+.5),50]); return o; }')

# spec 里带上排布方式
rep('    if(lv===1){ const a=rint(1,5); let b=a; while(Math.abs(b-a)<2||b<1||b>6) b=rint(1,6); return {a,b,mode:"cmp",spread:false}; }\n'
    '    if(lv===2){ const a=rint(3,6); const b=a+(rnd(2)?1:-1); return {a:clamp(a,1,7),b:clamp(b,1,7),mode:"cmp",spread:false}; }',
    '    // lay: "fixed" 长度与数量成正比（知觉比较）；"fill" 两排等长（长度线索被抹掉）\n'
    '    if(lv===1){ const a=rint(1,5); let b=a; while(Math.abs(b-a)<2||b<1||b>6) b=rint(1,6);\n'
    '                return {a,b,mode:"cmp",spread:false,lay:"fixed"}; }\n'
    '    if(lv===2){ const a=rint(3,6); const b=a+(rnd(2)?1:-1);\n'
    '                return {a:clamp(a,1,7),b:clamp(b,1,7),mode:"cmp",spread:false,lay:"fill"}; }')
rep('    if(lv===3){ const n=rint(3,6); return {a:n,b:n,mode:"cons",spread:true}; }   // 守恒：等量、只改间距\n'
    '    const n=rint(3,6), miss=rint(1,3);\n'
    '    return {a:n,b:Math.max(1,n-miss),mode:"fix",spread:false};',
    '    if(lv===3){ const n=rint(3,6); return {a:n,b:n,mode:"cons",spread:true,lay:"spread"}; } // 守恒：等量、只改间距\n'
    '    const n=rint(3,6), miss=rint(1,3);\n'
    '    return {a:n,b:Math.max(1,n-miss),mode:"fix",spread:false,lay:"fixed"};')
rep('    st=newState(retry); q=setQ(fresh(spec,o=>o.mode+":"+o.a+","+o.b,box));',
    '    st=newState(retry); q=setQ(fresh(spec,o=>o.mode+":"+o.a+","+o.b,box));\n'
    '    const layOf=(cnt,wide)=>q.lay==="spread"?rowSpread(cnt,wide)\n'
    '                            :q.lay==="fill"?rowPos(cnt)\n'
    '                            :rowFixed(cnt,Math.max(q.a,q.b)+(q.mode==="fix"?1:0));')
rep('    ui.A=place(rowA,q.a,item,q.spread?rowSpread(q.a,wideTop):rowPos(q.a));\n'
    '    ui.B=place(rowB,q.b,item,q.spread?rowSpread(q.b,!wideTop):rowPos(q.b));',
    '    ui.A=place(rowA,q.a,item,layOf(q.a,wideTop));\n'
    '    ui.B=place(rowB,q.b,item,layOf(q.b,!wideTop));')
# L4 补齐时重排也用同一套间距
rep('    function relayoutB(){ const pos=rowPos(ui.B.length); ui.B.forEach((o,i)=>{ o.style.left=pos[i][0]+"%"; o.style.top="50%"; }); }',
    '    function relayoutB(){\n'
    '      const pos=rowFixed(ui.B.length,Math.max(q.a,q.b)+1);\n'
    '      ui.B.forEach((o,i)=>{ o.style.left=pos[i][0]+"%"; o.style.top="50%"; });\n'
    '    }')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
