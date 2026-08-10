# -*- coding: utf-8 -*-
"""代码清理：去掉合成 PointerEvent 的 hack 与一处死代码，改为直接调用具名函数。"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()
n = 0


def rep(a, b):
    global s, n
    if a in s:
        s = s.replace(a, b, 1); n += 1
    else:
        print("MISS:", a[:70].replace("\n", "\\n"))


# 1) 把"派一只狗 / 召回一只狗"抽成具名函数，giveAnswer 直接调用
rep('''      onTap(d,()=>{
        if(st.done||d.dataset.out) return;
        d.dataset.out="1"; d.style.opacity=".25";
        const c=el("div","",zone);
        c.style.cssText="width:clamp(40px,7.2vmin,80px);height:clamp(40px,7.2vmin,80px);position:relative";
        img(A.ch(DOGS[i]),"",c).style.cssText="width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 3px 4px rgba(0,0,0,.4))";
        c.classList.add("pop");
        sent.push({card:c,dog:d});
        SFX.count(sent.length); numPop(c,sent.length); Speech.count(cnSeq(sent.length),"child-count");
        onTap(c,()=>{ if(st.done) return; recall(c); });
        okBtn.disabled=false;
      });
    }
    function recall(c){
      const i=sent.findIndex(x=>x.card===c); if(i<0) return;
      sent[i].dog.dataset.out=""; sent[i].dog.style.opacity="1";
      sent[i].card.remove(); sent.splice(i,1); SFX.tap();
      [].forEach.call(zone.children,(x,k)=>{});
      okBtn.disabled=sent.length===0;
    }''',
'''      onTap(d,()=>{ if(st.done) return; sendDog(i); });
    }
    /** 派出第 i 只狗（孩子点击与"带着一起做"的演示共用同一条路径） */
    function sendDog(i){
      const d=ui.dogs[i]; if(!d||d.dataset.out) return false;
      d.dataset.out="1"; d.style.opacity=".25";
      const c=el("div","",zone);
      c.style.cssText="width:clamp(40px,7.2vmin,80px);height:clamp(40px,7.2vmin,80px);position:relative";
      img(A.ch(DOGS[i]),"",c).style.cssText="width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 3px 4px rgba(0,0,0,.4))";
      c.classList.add("pop");
      sent.push({card:c,dog:d});
      SFX.count(sent.length); numPop(c,sent.length); Speech.count(cnSeq(sent.length),"child-count");
      onTap(c,()=>{ if(st.done) return; recall(c); });
      okBtn.disabled=false;
      return true;
    }
    function recall(c){
      const i=sent.findIndex(x=>x.card===c); if(i<0) return;
      sent[i].dog.dataset.out=""; sent[i].dog.style.opacity="1";
      sent[i].card.remove(); sent.splice(i,1); SFX.tap();
      okBtn.disabled=sent.length===0;
    }
    ui.sendDog=sendDog; ui.recall=recall;''')

# 2) giveAnswer 不再合成 PointerEvent
rep('''      if(need>0&&k<need){
        const free=ui.dogs.find(d=>!d.dataset.out);
        if(free){ free.dispatchEvent(new PointerEvent("pointerdown",{bubbles:true})); }
        k++; T.after(650,step); return;
      }
      if(need<0&&k< -need){
        const last=ui.zone.lastChild; if(last) last.dispatchEvent(new PointerEvent("pointerdown",{bubbles:true}));
        k++; T.after(650,step); return;
      }''',
'''      if(need>0&&k<need){
        const idx=ui.dogs.findIndex(d=>!d.dataset.out);
        if(idx>=0) ui.sendDog(idx);
        k++; T.after(650,step); return;
      }
      if(need<0&&k< -need){
        const last=ui.sent.length?ui.sent[ui.sent.length-1].card:null;
        if(last) ui.recall(last);
        k++; T.after(650,step); return;
      }''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
