# -*- coding: utf-8 -*-
"""清理死代码 + 不预载未使用素材"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()
n = 0


def rep(a, b):
    global s, n
    if a in s:
        s = s.replace(a, b, 1); n += 1
    else:
        print("MISS:", a[:60].replace("\n", "\\n"))


rep('function actor(top,name,side,h){\n'
    '  const a=el("div","actor",top);\n'
    '  a.style[side<0?"left":"right"]=(side<0?1:1)+"%";\n'
    '  a.style.height=(h||30)+"%";\n'
    '  img(A.ch(name),"",a);\n'
    '  return a;\n'
    '}\n', '')
rep('/* 角色 */\n'
    '.actor{position:absolute;bottom:0;pointer-events:none;filter:drop-shadow(0 6px 8px rgba(0,0,0,.4));z-index:3}\n'
    '.actor img{height:100%;width:auto;object-fit:contain}\n', '')
rep('      practice:()=>{},                    // 复测/纠错题：不写掌握证据\n', '')
rep('    const gotStar=Store.addStar(curW.id);', '    Store.addStar(curW.id);')
rep('  hulu:GOURDS.slice(), aveng:["goon","web","portal","quinjet"],\n'
    '  monkey:["gubang_seg","gubang_tip","stone","peach"]',
    '  hulu:GOURDS.slice(), aveng:["goon","portal","quinjet"],\n'
    '  monkey:["gubang_seg","gubang_tip","stone"]')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)

# 同步：不再产出未使用素材
op = os.path.join(os.path.dirname(os.path.abspath(__file__)), "optimize.py")
t = io.open(op, encoding="utf-8").read()
t2 = t.replace('"goon", "web", "portal", "quinjet", "peach", "basket",', '"goon", "portal", "quinjet", "basket",')
if t2 != t:
    io.open(op, "w", encoding="utf-8", newline="").write(t2)
    print("optimize.py prop list trimmed")
else:
    print("optimize.py: prop list unchanged (check manually)")
