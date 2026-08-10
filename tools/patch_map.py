# -*- coding: utf-8 -*-
"""每次离开世界都把星空地图整个重建（18 张缩略图重新创建），
   于是快速进出时会中止仍在加载的图片请求。改成"建一次、之后只刷新状态"。"""
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


rep('''  /* ---------- 地图 ---------- */
  function buildMap(){
    const host=$("#worlds"); host.textContent="";''',
    '''  /* ---------- 地图 ---------- */
  /** 只刷新状态，不重建 DOM —— 避免反复进出时中止仍在加载的缩略图请求 */
  function refreshMap(){
    const host=$("#worlds"), sug=suggest();
    WORLDS.forEach(w=>{
      const b=host.querySelector('[data-w="'+w.id+'"]'); if(!b) return;
      const n=Store.stars(w.id), un=Store.unlocked(w.id);
      b.classList.toggle("done",n>=STARS_FULL);
      b.classList.toggle("suggest",w.id===sug);
      b.classList.toggle("locked",!un);
      const st=b.querySelector(".wstars");
      if(st) [].forEach.call(st.children,(d,i)=>d.classList.toggle("f",i<n));
      const lk=b.querySelector(".lock");
      if(un && lk) lk.remove();
      else if(!un && !lk){ const l=el("div","lock",b); el("b","",l); }
    });
    drawConstell();
  }
  function buildMap(){
    const host=$("#worlds");
    if(host.children.length===WORLDS.length){ refreshMap(); return; }
    host.textContent="";''')

# 家长面板清空进度后需要强制重建（锁/星星差异较大，直接刷新即可，但保险起见走同一路径）
rep('      Store.reset(); armed=false; b.textContent="已清空"; buildMap(); refreshPanel();',
    '      Store.reset(); armed=false; b.textContent="已清空"; refreshMap(); refreshPanel();')

rep('  return { boot, buildMap, drawConstell, leave, enter, openPanel };',
    '  return { boot, buildMap, refreshMap, drawConstell, leave, enter, openPanel };')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
