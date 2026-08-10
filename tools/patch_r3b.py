# -*- coding: utf-8 -*-
"""第三轮修复 B 组：
   R3-1.2 符号门只管了答案卡，计数角标与 numPop 从 L1 就在显示阿拉伯数字
          → 所有数字呈现统一经过 Store.symbols()；未解锁时用累计圆点
   R3-1.1 掌握门可被随机序列跨过 → 追加"两个跨会话独立掌握窗口"
   R3-1.3 patDiffers 按下标比较，n=3 的 dice 与 ring 其实是同一个三角形
          → 改用点集 Hausdorff 距离
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


# ---------- 1.3 点集 Hausdorff ----------
rep('''function patDiffers(n,a,b){
  if(a===b) return false;
  const A=dotPos(n,a), B=dotPos(n,b);
  if(!A||!B||A.length!==B.length) return true;
  let far=0;
  for(let i=0;i<A.length;i++){
    const d=Math.hypot(A[i][0]-B[i][0], A[i][1]-B[i][1]);
    if(d>14) far++;
  }
  return far>=Math.max(1,Math.ceil(n*0.6));
}''',
    '''function patDiffers(n,a,b){
  if(a===b) return false;
  const A=dotPos(n,a), B=dotPos(n,b);
  if(!A||!B||A.length!==B.length) return true;
  // 必须比"点集"而不是"按下标一一对应"：n=3 时 dice 与 ring 是同一个上尖三角形，
  // 只是左右两点的顺序相反，按下标比会得出"完全不同"的假阳性。
  const nearest=(p,S)=>Math.min.apply(null,S.map(q=>Math.hypot(p[0]-q[0],p[1]-q[1])));
  let h=0;
  A.forEach(p=>{ h=Math.max(h,nearest(p,B)); });
  B.forEach(p=>{ h=Math.max(h,nearest(p,A)); });
  return h>13;                      // Hausdorff 距离（百分比坐标）足够大才算"看起来不一样"
}''')

# ---------- 1.2 全局符号门 ----------
rep('''function numPop(elm,n){
  const p=$("#numpop"); if(!elm) return;
  const r=elm.getBoundingClientRect(), s=$("#scene").getBoundingClientRect();
  p.textContent=String(n);
  p.style.left=(r.left+r.width/2-s.left)+"px"; p.style.top=(r.top+r.height/2-s.top)+"px";
  p.classList.remove("on"); void p.offsetWidth; p.classList.add("on");
}''',
    '''/** 符号未解锁时，"数到几"一律用累计圆点表示，绝不出现阿拉伯数字。
    符号是量的名字，必须等量感建立之后才引入。 */
function pipRow(n){
  n=clamp(n,1,10);
  let h="";
  for(let i=0;i<n;i++) h+='<b></b>';
  return h;
}
function numPop(elm,n){
  const p=$("#numpop"); if(!elm) return;
  const r=elm.getBoundingClientRect(), s=$("#scene").getBoundingClientRect();
  if(Store.symbols()){ p.className=""; p.textContent=String(n); }
  else { p.className="pips"; p.innerHTML=pipRow(n); }
  p.style.left=(r.left+r.width/2-s.left)+"px"; p.style.top=(r.top+r.height/2-s.top)+"px";
  p.classList.remove("on"); void p.offsetWidth; p.classList.add("on");
}
/** 计数角标：解锁前显示圆点堆，解锁后才显示数字 */
function setTag(el,n){
  if(!el) return;
  if(Store.symbols()){ el.className="tag"; el.textContent=String(n); }
  else { el.className="tag pips"; el.innerHTML=pipRow(n); }
}''')
rep('''#numpop.on{display:block;animation:np .75s ease-out both}''',
    '''#numpop.on{display:block;animation:np .75s ease-out both}
/* 符号解锁前：数量用圆点堆表示 */
#numpop.pips{display:none;gap:clamp(3px,.6vmin,6px);flex-wrap:wrap;max-width:clamp(90px,17vmin,180px);
  justify-content:center;text-shadow:none}
#numpop.pips.on{display:flex}
#numpop.pips b{width:clamp(12px,2.4vmin,24px);height:clamp(12px,2.4vmin,24px);border-radius:50%;
  background:#fff;box-shadow:0 2px 0 #e2453f,0 0 10px rgba(0,0,0,.45);display:block}
.cobj .tag.pips{display:none;gap:1px;flex-wrap:wrap;max-width:calc(var(--obj)*.6);
  padding:2px 3px;justify-content:center;align-content:center}
.cobj.counted .tag.pips{display:flex}
.cobj .tag.pips b{width:calc(var(--obj)*.09);height:calc(var(--obj)*.09);border-radius:50%;
  background:#fff;display:block}''')

# 所有写数字到 .tag 的地方改用 setTag
for old, new in [
    ('o.classList.add("counted"); o.querySelector(".tag").textContent=String(i+1);',
     'o.classList.add("counted"); setTag(o.querySelector(".tag"),i+1);'),
    ('o.classList.add("counted"); o.querySelector(".tag").textContent=String(ui.counted);',
     'o.classList.add("counted"); setTag(o.querySelector(".tag"),ui.counted);'),
    ('''      const t=o.querySelector(".tag"); t.textContent=i<ui.len?String(i+1):"";''',
     '''      const t=o.querySelector(".tag");
      if(i<ui.len) setTag(t,i+1); else { t.className="tag"; t.textContent=""; }'''),
    ('''        for(let i=0;i<startFrom;i++){ const o=all[i];
          o.classList.add("counted"); o.querySelector(".tag").textContent=String(i+1); o.style.pointerEvents="none"; }''',
     '''        for(let i=0;i<startFrom;i++){ const o=all[i];
          o.classList.add("counted"); setTag(o.querySelector(".tag"),i+1); o.style.pointerEvents="none"; }'''),
]:
    rep(old, new)

# ---------- 1.1 跨会话双窗口 ----------
rep("  const mkW=()=>({stars:0,lv:1,hist:[],seen:0,tries:0,open:0,mast:0});",
    "  const mkW=()=>({stars:0,lv:1,hist:[],seen:0,tries:0,open:0,mast:0,wins:0,winAt:-1});")
rep("        t.mast=clamp(Math.floor(num(s.mast,0)),0,999);",
    "        t.mast=clamp(Math.floor(num(s.mast,0)),0,999);\n"
    "        t.wins=clamp(Math.floor(num(s.wins,0)),0,999);\n"
    "        t.winAt=Math.floor(num(s.winAt,-1));")
rep('''      const h=w.hist;
      if(h.length>=5){
        const last5=h.slice(-5), s5=last5.reduce((a,b)=>a+b,0);
        if(s5>=4 && w.lv<MAXLV){ w.lv++; w.hist=[]; refreshUnlocks(); save(); return "up"; }
      }''',
    '''      const h=w.hist;
      if(h.length>=5){
        const last5=h.slice(-5), s5=last5.reduce((a,b)=>a+b,0);
        if(s5>=4){
          // 一个"掌握窗口"完成。必须来自**不同的一次游玩**才算数 ——
          // 否则一次运气好的连对就能同时凑够两个窗口。
          if(w.winAt!==d.plays){ w.wins++; w.winAt=d.plays; }
          if(w.lv<MAXLV){ w.lv++; w.hist=[]; refreshUnlocks(); save(); return "up"; }
          w.hist=[]; refreshUnlocks(); save(); return "";
        }
      }''')
rep('''      // 三个条件同时成立才解锁，且全部只看"掌握"，与参与星完全无关：
      //   难度到 L2 以上 + 累计 >=6 次无提示首答正确 + 最近 10 次正确率 >=0.6
      if(prev.lv>=2 && prev.mast>=6 && recentRate(prev)>=0.6){ cur.open=1; changed=true; }''',
    '''      // 四个条件同时成立才解锁，全部只看"掌握"，与参与星完全无关：
      //   难度到 L2 以上 + 累计 >=6 次无提示首答正确 + 最近 10 次正确率 >=0.6
      //   + **两个来自不同游玩会话的掌握窗口**（单次运气好的连对不算）
      if(prev.lv>=2 && prev.mast>=6 && prev.wins>=2 && recentRate(prev)>=0.6){
        cur.open=1; changed=true;
      }''')
rep('    rate:id=>recentRate(W(id)),', '    rate:id=>recentRate(W(id)),\n    wins:id=>W(id).wins,')
rep('''        +"　掌握◆"+Store.mastery(w.id)+"（近期正确率 "+Math.round(Store.rate(w.id)*100)+"%）"''',
    '''        +"　掌握◆"+Store.mastery(w.id)
        +"（近期正确率 "+Math.round(Store.rate(w.id)*100)+"%，跨会话窗口 "+Store.wins(w.id)+"/2）"''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
