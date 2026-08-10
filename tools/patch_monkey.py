# -*- coding: utf-8 -*-
"""花果山 L3/L4（缺失加数）补一道真正的算术判定：
   目标旗是给不识字孩子看的位置提示，但"把桥点到旗子那里"可以靠视觉对齐完成，
   不构成"接着数"的证据。因此到位之后必须再答一题"你一共加了几格？"，
   证据只记在这道题上；把桥点到位只是操作，不计证据。"""
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


rep('GAMES.monkey=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,fails=0;',
    'GAMES.monkey=ctx=>{\n  const T=ctx.T; let st=null,q=null,ui=null,fails=0,posWrong=0;')
rep('    st=newState(retry);\n    const lv=ctx.level();\n    let pre=0,need=0,target=0,mode="grow";',
    '    st=newState(retry); posWrong=0;\n    const lv=ctx.level();\n    let pre=0,need=0,target=0,mode="grow";')
rep('  function tapStone(i){\n    if(st.done) return;',
    '  function tapStone(i){\n    if(st.done||st.asking) return;')

rep('''  function submit(){
    if(st.done) return;
    const ok=(ui.len===q.target); record(ctx,st,ok);
    if(ok){
      st.done=true; ui.okBtn.disabled=true; ctx.answering(false);
      ui.stones.forEach(o=>o.classList.remove("tapme"));
      Speech.say(q.pre>0?(cnQty(q.pre)+"格再加"+cnQty(q.need)+"格，一共"+cnQty(q.target)+"格，正好！")
                        :("正好"+cnQty(q.target)+"格！"),{tag:"right"});
      SFX.right(); cross();
    }else{
      st.wrongs++; SFX.soft(); ui.staff.classList.add("shake");
      T.after(500,()=>ui.staff.classList.remove("shake"));
      ui.okBtn.disabled=true; ctx.answering(false);
      fails++;
      if(st.wrongs>=2||fails>=2){ reveal(); return; }
      remedy();
    }
  }''',
'''  function submit(){
    if(st.done||st.asking) return;
    /* L3/L4：先把桥点到亮着的石墩（这是操作，不计证据），
       再答"你一共加了几格"（这才是缺失加数，证据记在这一题） */
    if(q.mode==="reach"){
      if(ui.len!==q.target){
        SFX.soft(); ui.staff.classList.add("shake");
        T.after(500,()=>ui.staff.classList.remove("shake"));
        posWrong++;
        if(posWrong>=2){ autoFix(); return; }
        Speech.say("桥还没有正好搭到亮着的那个石墩，再看看。",{tag:"g:monkey"});
        return;
      }
      askHowMany(); return;
    }
    const ok=(ui.len===q.target); record(ctx,st,ok);
    if(ok){
      st.done=true; ui.okBtn.disabled=true; ctx.answering(false);
      ui.stones.forEach(o=>o.classList.remove("tapme"));
      Speech.say(q.pre>0?(cnQty(q.pre)+"格再加"+cnQty(q.need)+"格，一共"+cnQty(q.target)+"格，正好！")
                        :("正好"+cnQty(q.target)+"格！"),{tag:"right"});
      SFX.right(); cross();
    }else{
      st.wrongs++; SFX.soft(); ui.staff.classList.add("shake");
      T.after(500,()=>ui.staff.classList.remove("shake"));
      ui.okBtn.disabled=true; ctx.answering(false);
      fails++;
      if(st.wrongs>=2||fails>=2){ reveal(); return; }
      remedy();
    }
  }
  /** 位置连着两次不对 —— 带着孩子把桥放到位，再进入提问 */
  function autoFix(){
    st.asking=true; ui.okBtn.disabled=true; ctx.answering(false);
    ui.stones.forEach(o=>o.classList.remove("tapme"));
    const step=()=>{
      if(!ctx.alive()) return;
      if(ui.len<q.target){ grow(true); T.after(620,step); return; }
      if(ui.len>q.target){ shrinkTo(ui.len-1); T.after(520,step); return; }
      Speech.say("好啦，正好搭到啦！",{tag:"g:monkey"});
      T.after(1200,()=>{ if(ctx.alive()){ st.asking=false; askHowMany(); } });
    };
    T.after(700,step);
  }
  /** 缺失加数的真正判定：从起点接着数，一共加了几格？ */
  function askHowMany(){
    st.asking=true;
    ui.okBtn.disabled=true;
    ui.stones.forEach(o=>o.classList.remove("tapme"));
    ctx.answering(true);
    const apat=(ctx.symbols()&&ctx.level()>=4)?"num":pick(["dice","ring","line"]);
    const list=choices(q.need,1,8,4);
    const wrap=askCards(ui.L.bot,list,apat,(v,c)=>{
      if(st.done) return;
      const ok=(v===q.need); record(ctx,st,ok);
      if(ok){
        st.done=true; lockCards(wrap); c.classList.add("right"); ctx.answering(false);
        Speech.say("对啦！从"+cnSeq(q.pre)+"接着数"+cnQty(q.need)+"格，正好到"+cnSeq(q.target)+"！",{tag:"right"});
        SFX.right();
        T.after(1700,cross);
      }else{
        st.wrongs++; fails++; SFX.soft(); c.classList.add("wrong");
        T.after(420,()=>c.classList.remove("wrong"));
        lockCards(wrap); ctx.answering(false);
        if(st.wrongs>=2||fails>=2){
          st.done=true;
          [].forEach.call(wrap.children,x=>{
            if(+x.dataset.n===q.need){ x.classList.add("right"); Finger.at(x,2300); } else x.classList.add("dim"); });
          Speech.say("是这张，加了"+cnQty(q.need)+"格！",{tag:"reveal"});
          T.after(2100,cross);
          return;
        }
        remedyCountOn();
      }
    });
    ctx.ask("你一共加了几格呀？点一张卡片。",()=>wrap.firstChild);
  }
  /** 接着数专用纠错：已有的那几格保持不动，只把"新增的"重新逐格点亮报数 */
  function remedyCountOn(){
    st.asking=true;
    shrinkTo(q.pre);
    Speech.say("已经有的"+cnQty(q.pre)+"格不用再数，我们从"+cnSeq(q.pre)+"接着数。",{tag:"remedy"});
    T.after(1900,()=>{
      if(!ctx.alive()) return;
      let k=0;
      const step=()=>{
        if(!ctx.alive()) return;
        if(k>=q.need){
          Speech.say("一共加了"+cnQty(q.need)+"格。我们再试一个新的！",{tag:"remedy"});
          T.after(1900,()=>{ if(ctx.alive()) build(true); });
          return;
        }
        grow(true); k++; T.after(680,step);
      };
      step();
    });
  }''')

# reveal() 只用于 grow 模式；reach 模式走 autoFix/askHowMany
rep('  function reveal(){\n    st.done=true; ctx.answering(false); ui.okBtn.disabled=true;',
    '  function reveal(){\n    st.done=true; st.asking=true; ctx.answering(false); ui.okBtn.disabled=true;')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
