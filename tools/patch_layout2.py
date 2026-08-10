# -*- coding: utf-8 -*-
"""布局 v3：绘本式舞台 —— 两侧角色 + 中央下半部计数区（永远落在"地面"上）"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()
n = 0; miss = []


def rep(a, b):
    global s, n
    if a in s:
        s = s.replace(a, b, 1); n += 1
    else:
        miss.append(a[:80].replace("\n", "\\n"))


# ---------------- CSS ----------------
rep('.ztop{flex:1 1 auto;position:relative;min-height:0;display:flex;flex-direction:column;\n'
    '  align-items:center;justify-content:center;gap:var(--gap);padding:clamp(4px,1vmin,12px)}',
    '.ztop{flex:1 1 auto;position:relative;min-height:0}')
rep('.field{position:relative;width:100%;flex:1 1 auto;min-height:0}',
    '/* 计数区：绝对定位在画面下半部，两侧留给角色，物体永远落在"地面"上 */\n'
    '.field{position:absolute;left:13%;right:13%;top:30%;bottom:4%}')
rep('/* 角色带：与计数区分层，绝不遮挡可点物体 */\n'
    '.crew{flex:0 0 auto;width:100%;height:28%;min-height:0;display:flex;align-items:flex-end;\n'
    '  justify-content:space-between;padding:0 1%;pointer-events:none;position:relative;z-index:3}\n'
    '.crew .cw{height:100%;display:flex;align-items:flex-end;flex:0 0 auto}\n'
    '.crew .cw img{height:100%;width:auto;object-fit:contain;filter:drop-shadow(0 5px 7px rgba(0,0,0,.42))}\n'
    '.crew .cw.tap{pointer-events:auto}\n'
    '.crew .cw.sm img{height:76%}\n'
    '.crew .sp{flex:1 1 auto}\n'
    '/* 计数垫：保证计数物永远落在明确的界面上，并稳定前景/背景对比 */\n'
    '.field.mat{background:rgba(255,250,240,.44);border:3px solid rgba(255,255,255,.62);\n'
    '  border-radius:clamp(14px,2.6vmin,26px);box-shadow:0 6px 18px rgba(0,0,0,.22);\n'
    '  margin:0 2%;width:96%;flex:1 1 auto}\n'
    '/* Bluey 比较行 */\n'
    '.cmprow{flex:1 1 0;min-height:0;width:100%;display:flex;align-items:center;gap:1%;padding:0 1%}\n'
    '.cmprow .who{flex:0 0 auto;height:86%;display:flex;align-items:center}\n'
    '.cmprow .who img{height:100%;width:auto;object-fit:contain;filter:drop-shadow(0 4px 6px rgba(0,0,0,.42))}',
    '/* 两侧角色：贴地站立，不与计数区重叠，且不吃点击 */\n'
    '.side{position:absolute;bottom:1%;z-index:3;pointer-events:none;display:flex;align-items:flex-end;gap:2px;height:30%}\n'
    '.side img{height:100%;width:auto;object-fit:contain;filter:drop-shadow(0 5px 7px rgba(0,0,0,.45))}\n'
    '.side img.sm{height:76%}\n'
    '.side.l{left:0}.side.r{right:0}\n'
    '.side.tap{pointer-events:auto}\n'
    '/* 计数垫：稳定前景/背景对比，让数量刺激不受背景干扰 */\n'
    '.field.mat{background:rgba(255,250,240,.30);border:3px solid rgba(255,255,255,.55);\n'
    '  border-radius:clamp(14px,2.6vmin,26px);box-shadow:0 5px 16px rgba(0,0,0,.2)}')

# ---------------- JS 助手 ----------------
rep('function crewRow(top,h){ const c=el("div","crew",top); if(h!=null) c.style.height=h+"%"; return c; }\n'
    'function crewAdd(row,src,cls){ const d=el("div","cw"+(cls?" "+cls:""),row); img(src,"",d); return d; }\n'
    'function crewGap(row){ el("div","sp",row); }\n'
    'function mkField(top,mat){ return el("div","field"+(mat?" mat":""),top); }',
    '/** 舞台两侧角色（贴地站立） */\n'
    'function sideCast(top,side,names,h,tap){\n'
    '  const d=el("div","side "+side+(tap?" tap":""),top);\n'
    '  if(h!=null) d.style.height=h+"%";\n'
    '  names.forEach(nm=>{ const im=img(A.ch(nm.n||nm),"",d); if(nm.sm) im.classList.add("sm"); });\n'
    '  return d;\n'
    '}\n'
    '/** 计数区：默认落在画面下半部中央，两侧留给角色 */\n'
    'function mkField(top,o){\n'
    '  o=o||{};\n'
    '  const f=el("div","field"+(o.mat===false?"":" mat"),top);\n'
    '  if(o.l!=null) f.style.left=o.l+"%";\n'
    '  if(o.r!=null) f.style.right=o.r+"%";\n'
    '  if(o.t!=null) f.style.top=o.t+"%";\n'
    '  if(o.b!=null) f.style.bottom=o.b+"%";\n'
    '  return f;\n'
    '}\n'
    '/** 单独一个角色贴片（用于 Bluey 每一行的头像） */\n'
    'function faceAt(top,who,tPct,hPct,rightSide){\n'
    '  const d=el("div","",top);\n'
    '  d.style.cssText="position:absolute;"+(rightSide?"right:0;":"left:0;")+"top:"+tPct+"%;height:"+hPct+\n'
    '    "%;z-index:3;pointer-events:none;display:flex;align-items:center";\n'
    '  img(A.ch(who),"",d).style.cssText="height:100%;width:auto;object-fit:contain;filter:drop-shadow(0 4px 6px rgba(0,0,0,.45))";\n'
    '  return d;\n'
    '}')

# ---------------- 佩奇 ----------------
rep('    const cr=crewRow(L.top,30);\n'
    '    const pig=crewAdd(cr,A.ch("peppa"),"tap");\n'
    '    crewGap(cr);\n'
    '    crewAdd(cr,A.ch("mummypig"),"sm"); crewAdd(cr,A.ch("george"),"sm");\n'
    '    const field=mkField(L.top,true);',
    '    const pig=sideCast(L.top,"l",["peppa"],34,true);\n'
    '    sideCast(L.top,"r",["mummypig",{n:"george",sm:1}],28);\n'
    '    const field=mkField(L.top,{t:26});')

# ---------------- 汪汪队 ----------------
rep('    const cr=crewRow(L.top,26);\n'
    '    crewAdd(cr,A.ch("ryder")); crewGap(cr); crewAdd(cr,A.ch("marshall"),"sm");\n'
    '    if(kind==="given") buildGiven(L); else buildCount(L);',
    '    sideCast(L.top,"l",["ryder"],32);\n'
    '    sideCast(L.top,"r",["marshall"],26);\n'
    '    if(kind==="given") buildGiven(L); else buildCount(L);')
rep('    const field=mkField(L.top,true);\n'
    '    fitObj(field,q.n,q.cfg.pat==="row"?"row":"scatter");',
    '    const field=mkField(L.top,{t:q.cfg.pat==="row"?38:26});\n'
    '    fitObj(field,q.n,q.cfg.pat==="row"?"row":"scatter");')
rep('    // 任务卡单独一行，绝不与出动区重叠\n'
    '    const taskRow=el("div","",L.top);\n'
    '    taskRow.style.cssText="flex:0 0 auto;display:flex;align-items:center;justify-content:center;padding:2px 0";\n'
    '    const task=makeCard(q.n,pick(["dice","ring"])); task.style.pointerEvents="none";\n'
    '    taskRow.appendChild(task);\n'
    '    const zone=el("div","field mat",L.top);\n'
    '    zone.style.cssText+=";display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:2%";',
    '    // 任务卡固定在上方，绝不与出动区重叠\n'
    '    const holder=el("div","",L.top);\n'
    '    holder.style.cssText="position:absolute;left:50%;top:1%;transform:translateX(-50%);z-index:6;pointer-events:none";\n'
    '    const task=makeCard(q.n,pick(["dice","ring"])); task.style.pointerEvents="none";\n'
    '    holder.appendChild(task);\n'
    '    const zone=mkField(L.top,{t:44,b:3});\n'
    '    zone.style.display="flex"; zone.style.alignItems="center";\n'
    '    zone.style.justifyContent="center"; zone.style.flexWrap="wrap"; zone.style.gap="2%";')

# ---------------- Bluey ----------------
rep('    const cr=crewRow(L.top,20);\n'
    '    crewGap(cr); crewAdd(cr,A.ch(q.mode==="cons"?"bandit":"chilli"));\n'
    '    const mkRow=(who)=>{\n'
    '      const r=el("div","cmprow",L.top);\n'
    '      const w=el("div","who",r); img(A.ch(who),"",w);\n'
    '      const f=el("div","field mat",r); f.style.margin="0"; f.style.width="auto";\n'
    '      return f;\n'
    '    };\n'
    '    const rowA=mkRow("bluey"), rowB=mkRow("bingo");',
    '    // 两行几何完全相同 —— 比较/守恒的效度要求除间距外没有任何其它差异\n'
    '    faceAt(L.top,"bluey",20,30); faceAt(L.top,"bingo",62,30);\n'
    '    faceAt(L.top,q.mode==="cons"?"bandit":"chilli",1,17,true);\n'
    '    const rowA=mkField(L.top,{l:15,r:4,t:20,b:52});\n'
    '    const rowB=mkField(L.top,{l:15,r:4,t:62,b:10});')

# ---------------- 葫芦山 ----------------
rep('    const L=layout(ctx.root); ui={L};\n'
    '    if(kind==="ord") buildOrd(L,lv); else if(kind==="explore") buildExplore(L,lv); else buildMissing(L,lv);\n'
    '    const cr=crewRow(L.top,kind==="ord"?26:15);\n'
    '    crewAdd(cr,A.ch("yeye")); crewGap(cr);',
    '    const L=layout(ctx.root); ui={L};\n'
    '    sideCast(L.top,"l",["yeye"],kind==="ord"?30:20);\n'
    '    if(kind==="ord") buildOrd(L,lv); else if(kind==="explore") buildExplore(L,lv); else buildMissing(L,lv);')
rep('    const field=mkField(L.top,false);\n'
    '    fitObj(field,total,"row");\n'
    '    const pos=rowPos(total).map(p=>[p[0],48]);',
    '    const field=mkField(L.top,{mat:false,l:14,r:4,t:8,b:44});\n'
    '    fitObj(field,total,"row");\n'
    '    const pos=rowPos(total).map(p=>[p[0],62]);')
rep('  function buildPaths(L,N,already){\n'
    '    const field=el("div","field",L.top);\n'
    '    const wrap=el("div","",field);\n'
    '    wrap.style.cssText="position:absolute;left:3%;right:3%;top:3%;bottom:15%;display:flex;gap:3%";',
    '  function buildPaths(L,N,already){\n'
    '    const field=mkField(L.top,{mat:false,l:13,r:2,t:2,b:2});\n'
    '    const wrap=el("div","",field);\n'
    '    wrap.style.cssText="position:absolute;left:0;right:0;top:0;bottom:17%;display:flex;gap:3%";')

# ---------------- 复联 ----------------
rep('    const field=mkField(L.top,true); ui.field=field;\n'
    '    fitObj(field,Math.max(q.n,4),"row");\n'
    '    const jet',
    '    const field=mkField(L.top,{l:4,r:4,t:14,b:4}); ui.field=field;\n'
    '    fitObj(field,Math.max(q.n,4),"row");\n'
    '    const jet')
rep('    const field=mkField(L.top,true); ui.field=field;\n'
    '    fitObj(field,Math.max(n,m),"row");',
    '    const field=mkField(L.top,{l:4,r:4,t:10,b:4}); ui.field=field;\n'
    '    fitObj(field,Math.max(n,m),"row");')

# ---------------- 花果山（保持自定义绝对布局，只把 field 撑满） ----------------
rep('    const field=el("div","field",L.top); ui.field=field;\n'
    '\n'
    '    // 石墩 = 数轴刻度',
    '    const field=mkField(L.top,{mat:false,l:0,r:0,t:0,b:0}); ui.field=field;\n'
    '\n'
    '    // 石墩 = 数轴刻度')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched %d blocks" % n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
