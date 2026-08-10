# -*- coding: utf-8 -*-
"""连续两题不出同一道：孩子连着听到一模一样的指令既奇怪也浪费一次练习机会。"""
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


# 公共助手
rep('function setQ(o){ window.__q=o; window.__qn=(window.__qn||0)+1; return o; }',
    'function setQ(o){ window.__q=o; window.__qn=(window.__qn||0)+1; return o; }\n'
    '/** 连续两题不重复：最多重掷 8 次，掷不出来就算了（小数值域下必然会撞） */\n'
    'function fresh(gen,key,box){\n'
    '  let o=gen(), k=key(o), i=0;\n'
    '  while(box.last!=null && k===box.last && i<8){ o=gen(); k=key(o); i++; }\n'
    '  box.last=k; return o;\n'
    '}')

# 佩奇
rep('GAMES.peppa=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,shownAt=0,fails=0;',
    'GAMES.peppa=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,shownAt=0,fails=0; const box={last:null};')
rep('    st=newState(retry); q=setQ(spec());',
    '    st=newState(retry); q=setQ(fresh(spec,o=>o.n,box));')

# 汪汪队
rep('GAMES.paw=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0,fails=0;',
    'GAMES.paw=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0,fails=0; const box={last:null};')
rep('    q=setQ(spec(kind));',
    '    q=setQ(fresh(()=>spec(kind),o=>o.kind+":"+o.n,box));')

# Bluey
rep('GAMES.bluey=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,fails=0;',
    'GAMES.bluey=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,fails=0; const box={last:null};')
rep('    st=newState(retry); q=setQ(spec());',
    '    st=newState(retry); q=setQ(fresh(spec,o=>o.mode+":"+o.a+","+o.b,box));')

# 葫芦山（序数）
rep('GAMES.hulu=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0,fails=0;',
    'GAMES.hulu=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0,fails=0; const box={last:null};')
rep('    const total=lv===1?4:6, target=rint(1,lv===1?3:total);\n'
    '    const cols=shuffle(GOURDS).slice(0,total);\n'
    '    q=setQ({kind:"ord",total,target,cols});',
    '    const total=lv===1?4:6;\n'
    '    const mk=()=>({kind:"ord",total,target:rint(1,lv===1?3:total),cols:shuffle(GOURDS).slice(0,total)});\n'
    '    q=setQ(fresh(mk,o=>"ord:"+o.target,box));')
# 葫芦山（缺失加数）
rep('    const N=lv>=4?rint(5,6):rint(4,5), a=rint(1,N-1);\n'
    '    q=setQ({kind:"missing",N,a,need:N-a});',
    '    const mk=()=>{ const N=lv>=4?rint(5,6):rint(4,5), a=rint(1,N-1); return {kind:"missing",N,a,need:N-a}; };\n'
    '    const qq=fresh(mk,o=>"miss:"+o.N+","+o.a,box); q=setQ(qq);\n'
    '    const N=qq.N, a=qq.a;')

# 复联
rep('GAMES.aveng=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0,fails=0;',
    'GAMES.aveng=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,rt=0,fails=0; const box={last:null};')
rep('    const cap=lv===1?5:lv===2?6:8;\n'
    '    let a=rint(1,Math.min(4,cap-1)), b=rint(1,Math.min(4,cap-a));\n'
    '    q=setQ({kind:"add",a,b,n:a+b,lv});',
    '    const cap=lv===1?5:lv===2?6:8;\n'
    '    const mk=()=>{ const a=rint(1,Math.min(4,cap-1)); const b=rint(1,Math.min(4,cap-a));\n'
    '                   return {kind:"add",a,b,n:a+b,lv}; };\n'
    '    const qq=fresh(mk,o=>"add:"+o.a+","+o.b,box); q=setQ(qq);\n'
    '    const a=qq.a, b=qq.b;')
rep('    const n=rint(2,5); const d=pick([-1,0,1]);\n'
    '    const m=clamp(n+d,1,6);\n'
    '    q=setQ({kind:"pair",n,m,truth:m<n?"less":(m>n?"more":"same")});',
    '    const mk=()=>{ const n2=rint(2,5), m2=clamp(n2+pick([-1,0,1]),1,6);\n'
    '                   return {kind:"pair",n:n2,m:m2,truth:m2<n2?"less":(m2>n2?"more":"same")}; };\n'
    '    const qq=fresh(mk,o=>"pair:"+o.n+","+o.m,box); q=setQ(qq);\n'
    '    const n=qq.n, m=qq.m;')

# 花果山
rep('GAMES.monkey=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,fails=0,posWrong=0;',
    'GAMES.monkey=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,fails=0,posWrong=0; const box={last:null};')
rep('    let pre=0,need=0,target=0,mode="grow";\n'
    '    if(lv===1){ pre=0; need=rint(1,3); }\n'
    '    else if(lv===2){ pre=rint(1,3); need=rint(1,3); }\n'
    '    else { pre=rint(1,4); need=rint(2,4); mode="reach"; }\n'
    '    target=pre+need;\n'
    '    q=setQ({pre,need,target,lv,mode});',
    '    const mk=()=>{\n'
    '      let pre=0,need=0,mode="grow";\n'
    '      if(lv===1){ pre=0; need=rint(1,3); }\n'
    '      else if(lv===2){ pre=rint(1,3); need=rint(1,3); }\n'
    '      else { pre=rint(1,4); need=rint(2,4); mode="reach"; }\n'
    '      return {pre,need,target:pre+need,lv,mode};\n'
    '    };\n'
    '    q=setQ(fresh(mk,o=>o.pre+","+o.need,box));')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
