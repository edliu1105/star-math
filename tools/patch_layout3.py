# -*- coding: utf-8 -*-
"""布局 v4：Bluey 行位下移、花果山师徒上岸、复联标记避让、葫芦山两条路重排"""
import io, os, re
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()
n = 0; miss = []


def rep(a, b):
    global s, n
    if a in s:
        s = s.replace(a, b, 1); n += 1
    else:
        miss.append(a[:80].replace("\n", "\\n"))


# ---------- CSS：落区更紧凑、内部素材更大 ----------
rep('.dropzone{position:relative;flex:1 1 0;min-width:0;height:100%;border-radius:clamp(10px,2vmin,20px);\n'
    '  border:4px dashed rgba(255,255,255,.7);background:rgba(0,0,0,.24);display:flex;flex-direction:column;\n'
    '  align-items:center;justify-content:flex-end;padding:4px;transition:.15s}',
    '.dropzone{position:relative;flex:1 1 0;min-width:0;height:100%;border-radius:clamp(10px,2vmin,20px);\n'
    '  border:4px dashed rgba(255,255,255,.8);background:rgba(0,0,0,.3);display:flex;flex-direction:column;\n'
    '  align-items:center;justify-content:flex-end;padding:4px;transition:.15s;overflow:hidden}')
rep('.dropzone .zhead img{height:clamp(28px,5.6vmin,62px);width:auto}',
    '.dropzone .zhead img{height:clamp(34px,7vmin,86px);width:auto;filter:drop-shadow(0 3px 5px rgba(0,0,0,.45))}')
rep('.dropzone .slot img{height:clamp(26px,5.4vmin,58px);width:auto}',
    '.dropzone .slot img{height:clamp(30px,6.4vmin,72px);width:auto}')
rep('.dropzone .zhead{position:absolute;top:3%;left:0;right:0;display:flex;justify-content:center}',
    '.dropzone .zhead{position:absolute;top:4%;left:0;right:0;display:flex;justify-content:center;pointer-events:none}')
rep('.side.l{left:0}.side.r{right:0}',
    '.side.l{left:0}.side.r{right:0}\n'
    '/* 宽度受限的角色组（竖屏也不会撑爆） */\n'
    '.side.fitw{display:flex;align-items:flex-end;gap:1px}\n'
    '.side.fitw img{flex:1 1 0;min-width:0;width:100%;height:auto;max-height:100%;object-fit:contain}')

# ---------- Bluey：两行下移到栅栏/草地，几何仍完全一致 ----------
rep('    faceAt(L.top,"bluey",20,30); faceAt(L.top,"bingo",62,30);\n'
    '    faceAt(L.top,q.mode==="cons"?"bandit":"chilli",1,17,true);\n'
    '    const rowA=mkField(L.top,{l:15,r:4,t:20,b:52});\n'
    '    const rowB=mkField(L.top,{l:15,r:4,t:62,b:10});',
    '    faceAt(L.top,"bluey",28,32); faceAt(L.top,"bingo",62,32);\n'
    '    faceAt(L.top,q.mode==="cons"?"bandit":"chilli",1,20,true);\n'
    '    const rowA=mkField(L.top,{l:15,r:4,t:28,b:44});\n'
    '    const rowB=mkField(L.top,{l:15,r:4,t:62,b:10});')

# ---------- 复联：count-on 标记避开昆式战机 ----------
rep('        badge.style.cssText="position:absolute;left:8%;top:6%;width:clamp(44px,7.4vmin,78px);height:clamp(44px,7.4vmin,78px);z-index:6;pointer-events:none";',
    '        badge.style.cssText="position:absolute;left:1%;top:30%;width:clamp(42px,7vmin,74px);height:clamp(42px,7vmin,74px);z-index:6;pointer-events:none";')

# ---------- 花果山：师徒站到右岸；石墩盖在金箍棒之上 ----------
rep('  const CELLS=8, X0=15, XW=70;   // 数轴左起点与总宽(%)，右侧留给对岸师徒',
    '  const CELLS=8, X0=13, XW=56;   // 数轴左起点与总宽(%)，右侧留给对岸师徒')
rep('      img(A.pr("stone"),"",o); el("div","tag",o);',
    '      img(A.pr("stone"),"",o); el("div","tag",o); o.style.zIndex="6";')
rep('    const far=el("div","",field);\n'
    '    far.style.cssText="position:absolute;right:0;top:1%;height:31%;display:flex;align-items:flex-end;gap:2px;z-index:7;pointer-events:none";\n'
    '    ["tangseng","bajie","shaseng","bailongma"].forEach(c=>\n'
    '      img(A.ch(c),"",far).style.cssText="height:100%;width:auto;filter:drop-shadow(0 5px 6px rgba(0,0,0,.45))");',
    '    const far=el("div","side r fitw",field);\n'
    '    far.style.cssText="position:absolute;right:0;bottom:26%;width:28%;height:26%;z-index:7;pointer-events:none;display:flex;align-items:flex-end;gap:1px";\n'
    '    ["tangseng","bajie","shaseng","bailongma"].forEach(c=>\n'
    '      img(A.ch(c),"",far).style.cssText="flex:1 1 0;min-width:0;width:100%;height:auto;max-height:100%;object-fit:contain;filter:drop-shadow(0 5px 6px rgba(0,0,0,.45))");')
rep('    wk.style.cssText="position:absolute;left:-1%;bottom:2%;height:32%;z-index:7;pointer-events:none";',
    '    wk.style.cssText="position:absolute;left:-1%;bottom:6%;height:30%;z-index:7;pointer-events:none";')

# ---------- 葫芦山：两条路重排（落区下移变矮；待命区与目标格移到底部作答区） ----------
start = s.index("  /* ---- 两条路的公共布局 ---- */")
end = s.index("  return {\n    start:()=>{ rt=0; build(false); }, next:()=>build(false),\n    repeat:()=>{ if(!q) return;\n      Speech.say(q.kind===\"ord\"")
new_block = r'''  /* ---- 两条路的公共布局 ---- */
  function buildPaths(L,N,already){
    const field=mkField(L.top,{mat:false,l:13,r:2,t:26,b:2});
    const wrap=el("div","",field);
    wrap.style.cssText="position:absolute;inset:0;display:flex;gap:3%";
    const zl=el("button","dropzone",wrap), zr=el("button","dropzone",wrap);
    const hl=el("div","zhead",zl), hr=el("div","zhead",zr);
    img(A.ch("shejing"),"",hl); img(A.ch("xiezijing"),"",hr);
    const sl=el("div","slot",zl), sr=el("div","slot",zr);
    ui.zl=zl; ui.zr=zr; ui.sl=sl; ui.sr=sr; ui.field=field;
    ui.left=[]; ui.right=[];
    for(let i=0;i<(already||0);i++){ const im=img(A.ch(HULU_COLORS[i%7]),"",sl); ui.left.push(im); }
    return {zl,zr,sl,sr};
  }
  function addTo(side){
    const arr=side==="l"?ui.left:ui.right, slot=side==="l"?ui.sl:ui.sr;
    const im=img(A.ch(HULU_COLORS[(ui.left.length+ui.right.length)%7]),"",slot);
    im.classList.add("pop"); arr.push(im);
    SFX.count(arr.length); Speech.count(cnSeq(arr.length),"child-count");
  }
  function popFrom(side){
    const arr=side==="l"?ui.left:ui.right;
    if(!arr.length) return; const im=arr.pop(); im.remove(); SFX.tap();
  }
  /** 底部小条：待命的葫芦娃 / 目标格 */
  function strip(bot){
    const d=el("div","",bot);
    d.style.cssText="display:flex;gap:clamp(2px,.7vmin,6px);align-items:center;"+
      "padding:clamp(4px,1vmin,10px) clamp(6px,1.4vmin,14px);border-radius:99px;background:rgba(0,0,0,.4)";
    return d;
  }

  /* ---- 自由探索分解（不计掌握，探索"合起来还是那么多"） ---- */
  function buildExplore(L,lv){
    const N=rint(4,5); q=setQ({kind:"explore",N});
    buildPaths(L,N,0);
    let pool=N;
    const bar=strip(L.bot), chips=[];
    for(let i=0;i<N;i++){
      const c=el("div","",bar);
      c.style.cssText="width:clamp(26px,5vmin,54px);height:clamp(26px,5vmin,54px);transition:opacity .2s";
      img(A.ch(HULU_COLORS[i%7]),"",c).style.cssText="width:100%;height:100%;object-fit:contain";
      chips.push(c);
    }
    const upd=()=>{
      chips.forEach((c,i)=>c.style.opacity=i<pool?"1":".18");
      okBtn.disabled=!(pool===0&&ui.left.length>0&&ui.right.length>0);
    };
    onTap(ui.zl,()=>{ if(st.done||pool<=0) return; pool--; addTo("l"); upd(); });
    onTap(ui.zr,()=>{ if(st.done||pool<=0) return; pool--; addTo("r"); upd(); });
    onTap(ui.sl,()=>{ if(st.done||!ui.left.length) return; popFrom("l"); pool++; upd(); });
    onTap(ui.sr,()=>{ if(st.done||!ui.right.length) return; popFrom("r"); pool++; upd(); });
    const okBtn=bigBtn(L.bot,"出发！","green",()=>{
      if(st.done) return;
      st.done=true; okBtn.disabled=true;
      const a=ui.left.length,b=ui.right.length;
      Speech.say("左边"+cnQty(a)+"个，右边"+cnQty(b)+"个 —— 合起来还是"+cnQty(N)+"个！",{tag:"right"});
      SFX.right();
      T.after(2400,()=>{ if(ctx.alive()){ rt++; ctx.win(ui.zl); } });
    });
    okBtn.disabled=true; upd();
    ctx.answering(true);
    ctx.ask("要"+cnQty(N)+"个葫芦娃去救爷爷！两条路都要有人，你来分！点山洞或者山顶。",ui.zl);
  }

  /* ---- 缺失加数（唯一答案，计掌握） ---- */
  function buildMissing(L,lv){
    const N=lv>=4?rint(5,6):rint(4,5), a=rint(1,N-1);
    q=setQ({kind:"missing",N,a,need:N-a});
    buildPaths(L,N,a);
    const bar=strip(L.bot);
    ui.slots=[];
    for(let i=0;i<N;i++){
      const sl2=el("div","",bar);
      sl2.style.cssText="width:clamp(24px,4.6vmin,48px);height:clamp(24px,4.6vmin,48px);border-radius:8px;"+
        "border:3px solid rgba(255,255,255,.9);transition:background .2s;background:"+
        (i<a?"#6fbf4a":"rgba(0,0,0,.35)");
      ui.slots.push(sl2);
    }
    const upd=()=>{
      ui.slots.forEach((x,i)=>{ x.style.background=i<a?"#6fbf4a":(i<a+ui.right.length?"#ffd75e":"rgba(0,0,0,.35)"); });
      okBtn.disabled=ui.right.length===0;
    };
    onTap(ui.zr,()=>{ if(st.done||ui.right.length>=7) return; addTo("r"); upd(); });
    onTap(ui.sr,()=>{ if(st.done||!ui.right.length) return; popFrom("r"); upd(); });
    const okBtn=bigBtn(L.bot,"出发！","green",()=>submit());
    okBtn.disabled=true; ui.okBtn=okBtn;
    ctx.answering(true);
    ctx.ask((st.isRetry?"再来一次！":"")+"要"+cnQty(N)+"个葫芦娃！山洞里已经有"+cnQty(a)+"个了，山顶还要几个？点山顶派人，好了按绿色按钮。",ui.zr);
    function submit(){
      if(st.done) return;
      const ok=(ui.right.length===q.need); record(ctx,st,ok);
      if(ok){
        st.done=true; okBtn.disabled=true; ctx.answering(false);
        Speech.say("对啦！"+cnQty(a)+"个和"+cnQty(q.need)+"个，合起来正好"+cnQty(N)+"个！",{tag:"right"});
        SFX.right();
        T.after(2000,()=>{ if(ctx.alive()){ rt++; ctx.win(ui.zr); } });
      }else{
        st.wrongs++; SFX.soft(); ui.zr.classList.add("shake");
        T.after(500,()=>ui.zr.classList.remove("shake"));
        okBtn.disabled=true; ctx.answering(false);
        if(st.wrongs>=2){ missReveal(); return; }
        missRemedy();
      }
    }
  }
  /** 部分-整体专用纠错：已有部分保持不动，只闪烁"还差的空位" */
  function missRemedy(){
    ui.right.forEach(im=>im.remove()); ui.right=[];
    ui.slots.forEach((x,i)=>{ x.style.background=i<q.a?"#6fbf4a":"rgba(0,0,0,.35)"; });
    Speech.say("看，一共要"+cnQty(q.N)+"格。山洞已经有"+cnQty(q.a)+"个了。",{tag:"remedy"});
    T.after(1800,()=>{
      if(!ctx.alive()) return;
      let k=0;
      const blink=()=>{
        if(!ctx.alive()) return;
        if(k>=q.need){
          Speech.say("还差"+cnQty(q.need)+"个。我们再试一个新的！",{tag:"remedy"});
          T.after(2600,()=>{ if(ctx.alive()) build(true,"missing"); });
          return;
        }
        ui.slots[q.a+k].style.background="#ffd75e";
        SFX.count(k+1); Speech.count(cnSeq(k+1),"auto-count");
        k++; T.after(700,blink);
      };
      blink();
    });
  }
  function missReveal(){
    st.done=true; ctx.answering(false); ui.okBtn.disabled=true;
    ui.right.forEach(im=>im.remove()); ui.right=[];
    let k=0;
    const step=()=>{
      if(!ctx.alive()) return;
      if(k>=q.need){
        Speech.say("要"+cnQty(q.need)+"个才够！",{tag:"reveal"});
        T.after(1800,()=>{ if(ctx.alive()){ rt++; ctx.win(ui.zr); } });
        return;
      }
      addTo("r"); ui.slots[q.a+k].style.background="#ffd75e"; k++; T.after(700,step);
    };
    T.after(1200,step);
  }

'''
s = s[:start] + new_block + s[end:]
n += 1

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched %d blocks" % n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
