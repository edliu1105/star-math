# -*- coding: utf-8 -*-
"""布局修正补丁：计数垫 + 角色带 + 自适应物体尺寸 + 花果山几何"""
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
        miss.append(a[:80].replace("\n", "\\n"))


# 1. 公共助手
rep('function actor(top,name,side,h){',
    'function crewRow(top,h){ const c=el("div","crew",top); if(h!=null) c.style.height=h+"%"; return c; }\n'
    'function crewAdd(row,src,cls){ const d=el("div","cw"+(cls?" "+cls:""),row); img(src,"",d); return d; }\n'
    'function crewGap(row){ el("div","sp",row); }\n'
    'function mkField(top,mat){ return el("div","field"+(mat?" mat":""),top); }\n'
    '/** 计数物尺寸随数量自适应：同题内严格等大、绝不重叠 */\n'
    'function fitObj(field,n,mode){\n'
    '  n=Math.max(n,1);\n'
    '  let maxPct;\n'
    '  if(mode==="row")          maxPct=84/n*0.86;\n'
    '  else if(mode==="scatter") maxPct=86/Math.ceil(Math.sqrt(n*1.5))*0.82;\n'
    '  else                      maxPct=n<=3?26:(n<=5?22:(n<=7?18:15));\n'
    '  field.style.setProperty("--obj","min(clamp(38px,9vmin,104px),"+maxPct.toFixed(2)+"%)");\n'
    '}\n'
    'function actor(top,name,side,h){')

# 2. 佩奇
rep('    const L=layout(ctx.root);\n'
    '    actor(L.top,"george",1,26); actor(L.top,"mummypig",1,30).style.right="14%";\n'
    '    const pig=actor(L.top,"peppa",-1,34); pig.classList.add("tap");\n'
    '    const field=el("div","field",L.top);\n'
    '    ui={L,field,pig,blobs:[]};',
    '    const L=layout(ctx.root);\n'
    '    const cr=crewRow(L.top,30);\n'
    '    const pig=crewAdd(cr,A.ch("peppa"),"tap");\n'
    '    crewGap(cr);\n'
    '    crewAdd(cr,A.ch("mummypig"),"sm"); crewAdd(cr,A.ch("george"),"sm");\n'
    '    const field=mkField(L.top,true);\n'
    '    ui={L,field,pig,blobs:[]};')
rep('      ui.blobs=place(ui.field,q.n,A.pr("mudblob"),dotPos(q.n,q.cfg.qpat));\n'
    '      ui.blobs.forEach((b,i)=>{ b.classList.add("pop"); b.style.animationDelay=(i*.02)+"s"; });',
    '      fitObj(ui.field,q.n,q.cfg.qpat);\n'
    '      ui.blobs=place(ui.field,q.n,A.pr("mudblob"),dotPos(q.n,q.cfg.qpat));\n'
    '      ui.blobs.forEach((b,i)=>{ b.classList.add("pop"); b.style.animationDelay=(i*.02)+"s"; });')
rep('      ui.blobs=place(ui.field,q.n,A.pr("mudblob"),dotPos(q.n,q.cfg.qpat));\n      autoCount',
    '      fitObj(ui.field,q.n,q.cfg.qpat);\n'
    '      ui.blobs=place(ui.field,q.n,A.pr("mudblob"),dotPos(q.n,q.cfg.qpat));\n      autoCount')
rep('    const A1=place(ui.field,a,A.pr("mudblob"),posA);',
    '    fitObj(ui.field,Math.max(a,b)*2+1,"dice");\n'
    '    const A1=place(ui.field,a,A.pr("mudblob"),posA);')

# 3. 汪汪队
rep('    const L=layout(ctx.root); ui={L};\n'
    '    actor(L.top,"ryder",-1,30);\n'
    '    if(kind==="given") buildGiven(L); else buildCount(L);',
    '    const L=layout(ctx.root); ui={L};\n'
    '    const cr=crewRow(L.top,26);\n'
    '    crewAdd(cr,A.ch("ryder")); crewGap(cr); crewAdd(cr,A.ch("marshall"),"sm");\n'
    '    if(kind==="given") buildGiven(L); else buildCount(L);')
rep('  function buildCount(L){\n'
    '    const field=el("div","field",L.top);\n'
    '    const pos=q.cfg.pat==="row"?rowPos(q.n):scatter(q.n);',
    '  function buildCount(L){\n'
    '    const field=mkField(L.top,true);\n'
    '    fitObj(field,q.n,q.cfg.pat==="row"?"row":"scatter");\n'
    '    const pos=q.cfg.pat==="row"?rowPos(q.n):scatter(q.n);')
rep('  function buildGiven(L){\n'
    '    const wrapTop=el("div","field",L.top);\n'
    '    // 任务卡（点阵表示数量，不用数字）\n'
    '    const holder=el("div","",wrapTop);\n'
    '    holder.style.cssText="position:absolute;left:50%;top:6%;transform:translateX(-50%);z-index:5";\n'
    '    const task=makeCard(q.n,pick(["dice","ring"])); task.style.pointerEvents="none";\n'
    '    holder.appendChild(task);\n'
    '    // 出动区\n'
    '    const zone=el("div","",wrapTop);\n'
    '    zone.style.cssText="position:absolute;left:6%;right:6%;top:46%;bottom:20%;border-radius:16px;"+\n'
    '      "border:4px dashed rgba(255,255,255,.75);background:rgba(0,0,0,.22);display:flex;align-items:center;"+\n'
    '      "justify-content:center;flex-wrap:wrap;gap:2%";',
    '  function buildGiven(L){\n'
    '    // 任务卡单独一行，绝不与出动区重叠\n'
    '    const taskRow=el("div","",L.top);\n'
    '    taskRow.style.cssText="flex:0 0 auto;display:flex;align-items:center;justify-content:center;padding:2px 0";\n'
    '    const task=makeCard(q.n,pick(["dice","ring"])); task.style.pointerEvents="none";\n'
    '    taskRow.appendChild(task);\n'
    '    const zone=el("div","field mat",L.top);\n'
    '    zone.style.cssText+=";display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:2%";')

# 4. Bluey
rep('    const wideTop=q.spread?(rnd(2)===0):false;\n'
    '    const rowA=el("div","",L.top), rowB=el("div","",L.top);\n'
    '    [rowA,rowB].forEach(r=>{ r.style.cssText="position:relative;width:100%;flex:1 1 0;min-height:0"; });\n'
    '    const item=q.mode==="fix"?A.pr("cookie"):pick([A.pr("cookie"),A.pr("icecream")]);\n'
    '    ui.item=item;\n'
    '    ui.A=place(rowA,q.a,item,q.spread?rowSpread(q.a,wideTop):rowPos(q.a));\n'
    '    ui.B=place(rowB,q.b,item,q.spread?rowSpread(q.b,!wideTop):rowPos(q.b));\n'
    '    ui.rowA=rowA; ui.rowB=rowB;\n'
    '    // 角色：上排 Bluey，下排 Bingo\n'
    '    const la=el("div","",rowA), lb=el("div","",rowB);\n'
    '    la.style.cssText="position:absolute;left:1%;top:50%;transform:translateY(-50%);height:78%";\n'
    '    lb.style.cssText="position:absolute;left:1%;top:50%;transform:translateY(-50%);height:78%";\n'
    '    img(A.ch("bluey"),"",la).style.cssText="height:100%;width:auto";\n'
    '    img(A.ch("bingo"),"",lb).style.cssText="height:100%;width:auto";\n'
    '    actor(L.top,q.mode==="cons"?"bandit":"chilli",1,26);',
    '    const wideTop=q.spread?(rnd(2)===0):false;\n'
    '    const cr=crewRow(L.top,20);\n'
    '    crewGap(cr); crewAdd(cr,A.ch(q.mode==="cons"?"bandit":"chilli"));\n'
    '    const mkRow=(who)=>{\n'
    '      const r=el("div","cmprow",L.top);\n'
    '      const w=el("div","who",r); img(A.ch(who),"",w);\n'
    '      const f=el("div","field mat",r); f.style.margin="0"; f.style.width="auto";\n'
    '      return f;\n'
    '    };\n'
    '    const rowA=mkRow("bluey"), rowB=mkRow("bingo");\n'
    '    const item=q.mode==="fix"?A.pr("cookie"):pick([A.pr("cookie"),A.pr("icecream")]);\n'
    '    ui.item=item;\n'
    '    const most=Math.max(q.a,q.b)+(q.mode==="fix"?1:0);\n'
    '    fitObj(rowA,most,"row"); fitObj(rowB,most,"row");\n'
    '    ui.A=place(rowA,q.a,item,q.spread?rowSpread(q.a,wideTop):rowPos(q.a));\n'
    '    ui.B=place(rowB,q.b,item,q.spread?rowSpread(q.b,!wideTop):rowPos(q.b));\n'
    '    ui.rowA=rowA; ui.rowB=rowB;')

# 5. 葫芦山
rep('    const L=layout(ctx.root); ui={L};\n'
    '    actor(L.top,"yeye",-1,30);\n'
    '    if(kind==="ord") buildOrd(L,lv); else if(kind==="explore") buildExplore(L,lv); else buildMissing(L,lv);',
    '    const L=layout(ctx.root); ui={L};\n'
    '    if(kind==="ord") buildOrd(L,lv); else if(kind==="explore") buildExplore(L,lv); else buildMissing(L,lv);\n'
    '    const cr=crewRow(L.top,kind==="ord"?26:15);\n'
    '    crewAdd(cr,A.ch("yeye")); crewGap(cr);')
rep('    const field=el("div","field",L.top);\n'
    '    const pos=rowPos(total).map(p=>[p[0],38]);',
    '    const field=mkField(L.top,false);\n'
    '    fitObj(field,total,"row");\n'
    '    const pos=rowPos(total).map(p=>[p[0],48]);')
rep('    // 藤蔓横线\n'
    '    const vine=el("div","",field);\n'
    '    vine.style.cssText="position:absolute;left:3%;right:3%;top:20%;height:6px;border-radius:99px;background:#4a8f2e;box-shadow:0 3px 0 rgba(0,0,0,.25)";\n'
    '    ui.gs=gs; ui.field=field;',
    '    ui.gs=gs; ui.field=field;')
rep('    wrap.style.cssText="position:absolute;left:3%;right:3%;top:6%;bottom:4%;display:flex;gap:3%";',
    '    wrap.style.cssText="position:absolute;left:3%;right:3%;top:3%;bottom:15%;display:flex;gap:3%";')

# 6. 复联
rep('    const field=el("div","field",L.top); ui.field=field;\n'
    '    const jet=el("div","",field);\n'
    '    jet.style.cssText="position:absolute;left:2%;top:4%;width:clamp(46px,8vmin,92px)";',
    '    const field=mkField(L.top,true); ui.field=field;\n'
    '    fitObj(field,Math.max(q.n,4),"row");\n'
    '    const jet=el("div","",field);\n'
    '    jet.style.cssText="position:absolute;left:2%;top:3%;width:clamp(36px,6.4vmin,74px);pointer-events:none";')
rep('    por.style.cssText="position:absolute;right:2%;top:4%;width:clamp(46px,8vmin,92px)";',
    '    por.style.cssText="position:absolute;right:2%;top:3%;width:clamp(36px,6.4vmin,74px);pointer-events:none";')
rep('    for(let i=0;i<a;i++) posA.push([9+(i%2)*15, 40+Math.floor(i/2)*26]);\n'
    '    for(let i=0;i<b;i++) posB.push([76+(i%2)*15, 40+Math.floor(i/2)*26]);',
    '    for(let i=0;i<a;i++) posA.push([14+(i%2)*15, 44+Math.floor(i/2)*25]);\n'
    '    for(let i=0;i<b;i++) posB.push([71+(i%2)*15, 44+Math.floor(i/2)*25]);')
rep('    const field=el("div","field",L.top); ui.field=field;\n'
    '    const names=shuffle(HEROES);\n'
    '    ui.H=[]; ui.G=[];\n'
    '    const hp=rowPos(m).map(p=>[p[0],32]), gp=rowPos(n).map(p=>[p[0],72]);',
    '    const field=mkField(L.top,true); ui.field=field;\n'
    '    fitObj(field,Math.max(n,m),"row");\n'
    '    const names=shuffle(HEROES);\n'
    '    ui.H=[]; ui.G=[];\n'
    '    const hp=rowPos(m).map(p=>[p[0],30]), gp=rowPos(n).map(p=>[p[0],74]);')

# 7. 花果山
rep('  const CELLS=10;',
    '  const CELLS=8, X0=15, XW=70;   // 数轴左起点与总宽(%)，右侧留给对岸师徒')
rep('    const pos=[],stones=[];\n'
    '    for(let i=0;i<CELLS;i++) pos.push([7+(86/CELLS)*(i+.5),70]);',
    '    fitObj(field,CELLS+2,"row");\n'
    '    const pos=[],stones=[];\n'
    '    for(let i=0;i<CELLS;i++) pos.push([X0+(XW/CELLS)*(i+.5),66]);')
rep('    staff.style.cssText="position:absolute;left:"+(pos[0][0]-86/CELLS/2)+"%;top:62%;height:clamp(14px,2.6vmin,26px);"+',
    '    staff.style.cssText="position:absolute;left:"+X0+"%;top:58%;height:clamp(14px,2.6vmin,26px);"+')
rep('    tip.style.cssText="position:absolute;top:60%;height:clamp(18px,3.2vmin,32px);width:clamp(12px,2.2vmin,22px);"+',
    '    tip.style.cssText="position:absolute;top:56%;height:clamp(18px,3.2vmin,32px);width:clamp(12px,2.2vmin,22px);"+')
rep('    ui.staff=staff; ui.tip=tip; ui.x0=pos[0][0]-86/CELLS/2; ui.cw=86/CELLS;',
    '    ui.staff=staff; ui.tip=tip; ui.x0=X0; ui.cw=XW/CELLS;')
rep('    wk.style.cssText="position:absolute;left:0;bottom:6%;height:34%;z-index:7";',
    '    wk.style.cssText="position:absolute;left:-1%;bottom:2%;height:32%;z-index:7;pointer-events:none";')
rep('    far.style.cssText="position:absolute;right:0;bottom:6%;height:30%;display:flex;align-items:flex-end;gap:2px;z-index:7";',
    '    far.style.cssText="position:absolute;right:0;top:1%;height:31%;display:flex;align-items:flex-end;gap:2px;z-index:7;pointer-events:none";')
rep('      flag.style.cssText="position:absolute;left:"+pos[q.target-1][0]+"%;top:44%;transform:translate(-50%,-50%);"+',
    '      flag.style.cssText="position:absolute;left:"+pos[q.target-1][0]+"%;top:40%;transform:translate(-50%,-50%);pointer-events:none;"+')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched %d blocks" % n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
