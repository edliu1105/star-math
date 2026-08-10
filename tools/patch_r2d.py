# -*- coding: utf-8 -*-
"""第二轮修复 D 组（题目级竞态，codex 4-1）：
   问题：纠错/揭答案/自动演示期间输入没有统一锁定，且旧定时器只检查 ctx.alive()，
        而同一个世界里的新题仍然 alive —— 于是旧回调会污染新题。
   修法：
     1) 每题状态加 `locked`；所有输入路径统一先查 `st.done || st.locked`
     2) 所有"会推进流程"的异步序列开头捕获 `const my=st`，回调里用 `stale(my)` 判断本题是否已被换掉
"""
import io, os, re
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()
n = 0
miss = []


def rep(a, b, cnt=1):
    global s, n
    if a in s:
        s = s.replace(a, b, cnt); n += 1
    else:
        miss.append(a[:78].replace("\n", "\\n"))


# ---------- 公共助手 ----------
rep('''function newState(isRetry){ return {isRetry:!!isRetry,hinted:false,wrongs:0,recorded:false,done:false}; }''',
    '''function newState(isRetry){
  return {isRetry:!!isRetry,hinted:false,wrongs:0,recorded:false,done:false,locked:false,asking:false};
}
/** 本题是否已被换掉（纠错结束会 build(true) 生成新 st）——
    旧定时器必须据此退出，否则会拿旧数据去改新题 */
function busyState(st){ return !st || st.done || st.locked; }''')

# ---------- 佩奇 ----------
rep('onTap(pig,()=>{ if(st.done) return; st.hinted=true; flash(); });',
    'onTap(pig,()=>{ if(busyState(st)) return; st.hinted=true; flash(); });')
rep('''  function remediate(){
    const n=q.n, a=n<=3?n:(n<=5?n-2:3), b=n-a;''',
    '''  function remediate(){
    st.locked=true; const my=st;
    const n=q.n, a=n<=3?n:(n<=5?n-2:3), b=n-a;''')
rep('''    T.after(1400,()=>{
      if(!ctx.alive()) return;
      if(b>0){''',
    '''    T.after(1400,()=>{
      if(!ctx.alive()||st!==my) return;
      if(b>0){''')
rep('''      T.after(1400,()=>{
        if(!ctx.alive()) return;
        Speech.say("合起来是"+cnQty(n)+"个！我们再看一次新的。",{tag:"remedy"});
        T.after(1800,()=>{ if(ctx.alive()) build(true); });    // 同构新题复测''',
    '''      T.after(1400,()=>{
        if(!ctx.alive()||st!==my) return;
        Speech.say("合起来是"+cnQty(n)+"个！我们再看一次新的。",{tag:"remedy"});
        T.after(1800,()=>{ if(ctx.alive()&&st===my) build(true); });    // 同构新题复测''')

# ---------- 汪汪队 ----------
rep('''  function tapTurtle(o){
    if(st.done||o.classList.contains("counted")) return;''',
    '''  function tapTurtle(o){
    if(busyState(st)||o.classList.contains("counted")) return;''')
rep('''  function remedyCardinal(plus){
    ui.objs.forEach''',
    '''  function remedyCardinal(plus){
    st.locked=true; const my=st;
    ui.objs.forEach''')
rep('''    T.after(900,()=>{
      if(!ctx.alive()) return;
      autoCount(ctx,ui.objs,0,620,()=>{
        if(!ctx.alive()) return;
        Speech.say("最后数到"+cnSeq(q.n)+"，就是"+cnQty(q.n)+"只！",{tag:"remedy"});
        T.after(2400,()=>{ if(ctx.alive()) build(true,plus?"plus1":"count"); });''',
    '''    T.after(900,()=>{
      if(!ctx.alive()||st!==my) return;
      autoCount(ctx,ui.objs,0,620,()=>{
        if(!ctx.alive()||st!==my) return;
        Speech.say("最后数到"+cnSeq(q.n)+"，就是"+cnQty(q.n)+"只！",{tag:"remedy"});
        T.after(2400,()=>{ if(ctx.alive()&&st===my) build(true,plus?"plus1":"count"); });''')
rep('      onTap(d,()=>{ if(st.done) return; sendDog(i); });',
    '      onTap(d,()=>{ if(busyState(st)) return; sendDog(i); });')
rep('      onTap(c,()=>{ if(st.done) return; recall(c); });',
    '      onTap(c,()=>{ if(busyState(st)) return; recall(c); });')
rep('''  function remedyGiveN(got){
    ctx.answering(false); ui.okBtn.disabled=true;''',
    '''  function remedyGiveN(got){
    st.locked=true; const my=st;
    ctx.answering(false); ui.okBtn.disabled=true;''')
rep('''    T.after(900,()=>{
      if(!ctx.alive()) return;
      autoCount(ctx,objs,0,560,()=>{
        if(!ctx.alive()) return;''',
    '''    T.after(900,()=>{
      if(!ctx.alive()||st!==my) return;
      autoCount(ctx,objs,0,560,()=>{
        if(!ctx.alive()||st!==my) return;''')
rep('''        T.after(3000,()=>{
          if(!ctx.alive()) return;
          ui.task.classList.remove("right");''',
    '''        T.after(3000,()=>{
          if(!ctx.alive()||st!==my) return;
          ui.task.classList.remove("right");''')

# ---------- Bluey ----------
rep('''  function verify(done){
    Link.clear();''',
    '''  function verify(done){
    st.locked=true; const my=st;
    Link.clear();''')
rep('''    const step=()=>{
      if(!ctx.alive()) return;
      if(i>=n){
        const extra=q.a>q.b?ui.A.slice(n):(q.b>q.a?ui.B.slice(n):[]);''',
    '''    const step=()=>{
      if(!ctx.alive()||st!==my) return;
      if(i>=n){
        const extra=q.a>q.b?ui.A.slice(n):(q.b>q.a?ui.B.slice(n):[]);''')
rep('''        T.after(1900,()=>{ Link.clear(); extra.forEach(x=>x.classList.remove("tapme")); if(done) done(); });''',
    '''        T.after(1900,()=>{ if(st!==my) return; st.locked=false;
          Link.clear(); extra.forEach(x=>x.classList.remove("tapme")); if(done) done(); });''')
# handPair 需要孩子操作 → 解锁
rep('''  function handPair(){
    Link.clear();''',
    '''  function handPair(){
    st.locked=false;                      // 这一步要孩子亲手配对，必须可点
    Link.clear();''')
rep('''  function pairDone(){
    const left=ui.A.filter''',
    '''  function pairDone(){
    st.locked=true; const my=st;
    const left=ui.A.filter''')
rep('''    T.after(2600,()=>{
      if(!ctx.alive()) return;
      Link.clear(); build(true);            // 换新排列的同构题复测''',
    '''    T.after(2600,()=>{
      if(!ctx.alive()||st!==my) return;
      Link.clear(); build(true);            // 换新排列的同构题复测''')
rep('''      if(st.done||q.b+added>=9) return;''', '''      if(busyState(st)||q.b+added>=9) return;''')

# ---------- 葫芦山 ----------
rep('''  function tapG(i,o,gs){
    if(st.done) return;''',
    '''  function tapG(i,o,gs){
    if(busyState(st)) return;''')
rep('''  function ordRemedy(gs){
    Speech.say("我们从左边开始数：",{tag:"remedy"});''',
    '''  function ordRemedy(gs){
    st.locked=true; const my=st;          // 演示期间葫芦不可点，旧回调也不能改新题
    Speech.say("我们从左边开始数：",{tag:"remedy"});''')
rep('''    const step=()=>{
      if(!ctx.alive()) return;
      if(i>=q.target){
        gs[q.target-1].classList.add("tapme");''',
    '''    const step=()=>{
      if(!ctx.alive()||st!==my) return;
      if(i>=q.target){
        gs[q.target-1].classList.add("tapme");''')
rep('''        T.after(2600,()=>{ if(ctx.alive()){ gs[q.target-1].classList.remove("tapme"); build(true,"ord"); } });''',
    '''        T.after(2600,()=>{ if(ctx.alive()&&st===my){ gs[q.target-1].classList.remove("tapme"); build(true,"ord"); } });''')
rep('''    onTap(ui.zl,()=>{ if(st.done||pool<=0) return; pool--; addTo("l"); upd(); });
    onTap(ui.zr,()=>{ if(st.done||pool<=0) return; pool--; addTo("r"); upd(); });
    onTap(ui.sl,()=>{ if(st.done||!ui.left.length) return; popFrom("l"); pool++; upd(); });
    onTap(ui.sr,()=>{ if(st.done||!ui.right.length) return; popFrom("r"); pool++; upd(); });''',
    '''    onTap(ui.zl,()=>{ if(busyState(st)||pool<=0) return; pool--; addTo("l"); upd(); });
    onTap(ui.zr,()=>{ if(busyState(st)||pool<=0) return; pool--; addTo("r"); upd(); });
    onTap(ui.sl,()=>{ if(busyState(st)||!ui.left.length) return; popFrom("l"); pool++; upd(); });
    onTap(ui.sr,()=>{ if(busyState(st)||!ui.right.length) return; popFrom("r"); pool++; upd(); });''')
rep('''    onTap(ui.zr,()=>{ if(st.done||ui.right.length>=7) return; addTo("r"); upd(); });
    onTap(ui.sr,()=>{ if(st.done||!ui.right.length) return; popFrom("r"); upd(); });''',
    '''    onTap(ui.zr,()=>{ if(busyState(st)||ui.right.length>=7) return; addTo("r"); upd(); });
    onTap(ui.sr,()=>{ if(busyState(st)||!ui.right.length) return; popFrom("r"); upd(); });''')
rep('''  function missRemedy(){
    ui.right.forEach''',
    '''  function missRemedy(){
    st.locked=true; const my=st;
    ui.right.forEach''')
rep('''    T.after(1400,()=>{
      if(!ctx.alive()) return;
      let k=0;
      const blink=()=>{
        if(!ctx.alive()) return;''',
    '''    T.after(1400,()=>{
      if(!ctx.alive()||st!==my) return;
      let k=0;
      const blink=()=>{
        if(!ctx.alive()||st!==my) return;''')
rep('''          T.after(2000,()=>{ if(ctx.alive()) build(true,"missing"); });''',
    '''          T.after(2000,()=>{ if(ctx.alive()&&st===my) build(true,"missing"); });''')

# ---------- 复联 ----------
rep('''  function tapHero(o){
    if(st.done||o.classList.contains("counted")) return;''',
    '''  function tapHero(o){
    if(busyState(st)||o.classList.contains("counted")) return;''')
rep('''  function remedyAdd(){
    const all=ui.merged, posA=[],posB=[];''',
    '''  function remedyAdd(){
    st.locked=true; const my=st;          // 演示期间英雄不可点，旧回调也不能改新题
    const all=ui.merged, posA=[],posB=[];''')
rep('''    T.after(2000,()=>{
      if(!ctx.alive()) return;
      const pos=rowPos(q.n);''',
    '''    T.after(2000,()=>{
      if(!ctx.alive()||st!==my) return;
      const pos=rowPos(q.n);''')
rep('''      T.after(800,()=>{
        if(!ctx.alive()) return;
        autoCount(ctx,all,0,560,()=>{
          if(!ctx.alive()) return;
          Speech.say("合起来一共"+cnQty(q.n)+"个！我们再来一次新的。",{tag:"remedy"});
          T.after(2600,()=>{ if(ctx.alive()) build(true,"add"); });''',
    '''      T.after(800,()=>{
        if(!ctx.alive()||st!==my) return;
        autoCount(ctx,all,0,560,()=>{
          if(!ctx.alive()||st!==my) return;
          Speech.say("合起来一共"+cnQty(q.n)+"个！我们再来一次新的。",{tag:"remedy"});
          T.after(2600,()=>{ if(ctx.alive()&&st===my) build(true,"add"); });''')
rep('''      T.after(3000,()=>{ if(ctx.alive()){ Link.clear(); build(true,"pair"); } });''',
    '''      const myp=st; st.locked=true;
      T.after(3000,()=>{ if(ctx.alive()&&st===myp){ Link.clear(); build(true,"pair"); } });''')

# ---------- 花果山 ----------
rep('''  function tapStone(i){
    if(st.done||st.asking) return;''',
    '''  function tapStone(i){
    if(busyState(st)||st.asking) return;''')
rep('''  function remedy(){
    shrinkTo(q.pre);''',
    '''  function remedy(){
    st.locked=true; const my=st;          // 演示期间石墩不可点
    shrinkTo(q.pre);''')
rep('''    T.after(2200,()=>{
      if(!ctx.alive()) return;
      let k=0;
      const step=()=>{
        if(!ctx.alive()) return;
        if(k>=q.need){
          Speech.say("看，就是这样。我们再试一个新的！",{tag:"remedy"});
          T.after(1900,()=>{ if(ctx.alive()) build(true); });''',
    '''    T.after(2200,()=>{
      if(!ctx.alive()||st!==my) return;
      let k=0;
      const step=()=>{
        if(!ctx.alive()||st!==my) return;
        if(k>=q.need){
          Speech.say("看，就是这样。我们再试一个新的！",{tag:"remedy"});
          T.after(1900,()=>{ if(ctx.alive()&&st===my) build(true); });''')
rep('''  function remedyCountOn(){
    st.asking=true;
    shrinkTo(q.pre);''',
    '''  function remedyCountOn(){
    st.asking=true; st.locked=true; const my=st;
    shrinkTo(q.pre);''')
rep('''    T.after(1900,()=>{
      if(!ctx.alive()) return;
      let k=0;
      const step=()=>{
        if(!ctx.alive()) return;
        if(k>=q.need){
          Speech.say("一共加了"+cnQty(q.need)+"格。我们再试一个新的！",{tag:"remedy"});
          T.after(1900,()=>{ if(ctx.alive()) build(true); });''',
    '''    T.after(1900,()=>{
      if(!ctx.alive()||st!==my) return;
      let k=0;
      const step=()=>{
        if(!ctx.alive()||st!==my) return;
        if(k>=q.need){
          Speech.say("一共加了"+cnQty(q.need)+"格。我们再试一个新的！",{tag:"remedy"});
          T.after(1900,()=>{ if(ctx.alive()&&st===my) build(true); });''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
