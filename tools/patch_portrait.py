# -*- coding: utf-8 -*-
"""竖屏修正：
   舞台加一个固定长宽比、贴底对齐的容器 —— 竖屏下不再把场景拉高，
   所有百分比布局在横竖屏得到同一个坐标系；角色改为宽高双向受限。
   另修：地图卡片里的角色在窄卡片下被裁切。
"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()
n = 0; miss = []


def rep(a, b):
    global s, n
    if a in s:
        s = s.replace(a, b, 1); n += 1
    else:
        miss.append(a[:78].replace("\n", "\\n"))


# 1) 舞台容器：固定长宽比 + 贴底
rep('.ztop{flex:1 1 auto;position:relative;min-height:0}',
    '/* 舞台外框：竖屏时不把场景拉高，而是保持横向长宽比并贴住"地面"一侧，\n'
    '   这样同一套百分比布局在横竖屏得到完全一致的坐标系。 */\n'
    '.ztop{flex:1 1 auto;position:relative;min-height:0;display:flex;align-items:flex-end;justify-content:center}\n'
    '.stage{position:relative;width:100%;height:100%;max-height:min(100%,64vw)}')

# 2) 角色宽高双向受限（竖屏下不再变成巨人）
rep('.side{position:absolute;bottom:1%;z-index:3;pointer-events:none;display:flex;align-items:flex-end;gap:2px;height:30%}\n'
    '.side img{height:100%;width:auto;object-fit:contain;filter:drop-shadow(0 5px 7px rgba(0,0,0,.45))}\n'
    '.side img.sm{height:76%}',
    '.side{position:absolute;bottom:1%;z-index:3;pointer-events:none;display:flex;align-items:flex-end;\n'
    '  gap:2px;height:30%;max-width:22%}\n'
    '.side img{width:auto;height:auto;max-width:100%;max-height:100%;object-fit:contain;\n'
    '  filter:drop-shadow(0 5px 7px rgba(0,0,0,.45))}\n'
    '.side img.sm{max-height:76%}')

# 3) layout() 里插入 .stage
rep('function layout(root){\n'
    '  root.textContent="";\n'
    '  const top=el("div","ztop",root), bot=el("div","zbot",root);\n'
    '  return {top,bot};\n'
    '}',
    'function layout(root){\n'
    '  root.textContent="";\n'
    '  const zt=el("div","ztop",root), bot=el("div","zbot",root);\n'
    '  const top=el("div","stage",zt);      // 所有游戏都在这个固定长宽比的舞台里定位\n'
    '  return {top,bot,zt};\n'
    '}')

# 4) Bluey 的行内头像也宽高双向受限
rep('  d.style.cssText="position:absolute;"+(rightSide?"right:0;":"left:0;")+"top:"+tPct+"%;height:"+hPct+\n'
    '    "%;z-index:3;pointer-events:none;display:flex;align-items:center";\n'
    '  img(A.ch(who),"",d).style.cssText="height:100%;width:auto;object-fit:contain;filter:drop-shadow(0 4px 6px rgba(0,0,0,.45))";',
    '  d.style.cssText="position:absolute;"+(rightSide?"right:0;":"left:0;")+"top:"+tPct+"%;height:"+hPct+\n'
    '    "%;max-width:13%;z-index:3;pointer-events:none;display:flex;align-items:center;justify-content:center";\n'
    '  img(A.ch(who),"",d).style.cssText="width:auto;height:auto;max-width:100%;max-height:100%;object-fit:contain;filter:drop-shadow(0 4px 6px rgba(0,0,0,.45))";')

# 5) 花果山：悟空与师徒也受宽度限制
rep('    wk.style.cssText="position:absolute;left:-1%;bottom:6%;height:30%;z-index:7;pointer-events:none";\n'
    '    img(A.ch("wukong"),"",wk).style.cssText="height:100%;width:auto;filter:drop-shadow(0 5px 6px rgba(0,0,0,.45))";',
    '    wk.style.cssText="position:absolute;left:0;bottom:4%;height:30%;max-width:13%;z-index:7;pointer-events:none;'
    'display:flex;align-items:flex-end;justify-content:center";\n'
    '    img(A.ch("wukong"),"",wk).style.cssText="width:auto;height:auto;max-width:100%;max-height:100%;object-fit:contain;'
    'filter:drop-shadow(0 5px 6px rgba(0,0,0,.45))";')
rep('    far.style.cssText="position:absolute;right:0;bottom:26%;width:28%;height:26%;z-index:7;pointer-events:none;display:flex;align-items:flex-end;gap:1px";',
    '    far.style.cssText="position:absolute;right:0;bottom:28%;width:26%;height:24%;z-index:7;pointer-events:none;display:flex;align-items:flex-end;gap:1px";')

# 6) 地图卡片：角色按宽度分配，不再被裁切
rep('.world .cast img{height:80%;max-height:100%;width:auto;object-fit:contain;filter:drop-shadow(0 4px 6px rgba(0,0,0,.5))}\n'
    '.world .cast img.lead{height:100%}',
    '.world .cast img{flex:1 1 0;min-width:0;width:100%;height:auto;max-height:86%;object-fit:contain;\n'
    '  object-position:bottom;filter:drop-shadow(0 4px 6px rgba(0,0,0,.5))}\n'
    '.world .cast img.lead{max-height:100%}')
rep('      w.cast.slice(0,4).forEach((c,i)=>img(A.th(c),i===0?"lead":"",cast));',
    '      w.cast.slice(0,3).forEach((c,i)=>img(A.th(c),i===0?"lead":"",cast));')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
