# -*- coding: utf-8 -*-
"""第二轮修复 C 组（无语音自足 + 提示可用性）：
   R2-2.1 葫芦娃"第几个"、金箍棒"变长几格" 之前只存在于语音里 → 补视觉任务卡
   R2-2.2 序数题的提示目标固定在第一个葫芦 → 改为整排一起亮
   R2-2.3 firstTime 从未使用 → 首次进入做一次不计分的手势示范；提示节奏 9/18/27 → 5/10/15
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


# ---------- 任务卡样式 ----------
rep('''/* 气泡 / 提示手指 */''',
    '''/* 视觉任务卡：把只在语音里的任务（"第几个"、"变长几格"）画出来，
   这样一个字都不识、一句话都听不见的孩子也知道要做什么 */
.taskcard{position:absolute;left:50%;top:1%;transform:translateX(-50%);z-index:8;pointer-events:none;
  display:flex;align-items:center;gap:clamp(4px,.9vmin,9px);
  padding:clamp(5px,1.1vmin,11px) clamp(9px,2vmin,20px);border-radius:99px;
  background:rgba(255,248,234,.95);box-shadow:0 4px 0 rgba(0,0,0,.22)}
.taskcard i{width:clamp(13px,2.6vmin,26px);height:clamp(13px,2.6vmin,26px);border-radius:50%;
  background:#e2453f;display:block;box-shadow:inset 0 -2px 0 rgba(0,0,0,.16)}
.taskcard i.ghost{background:#cfc6dd}
.taskcard i.mark{background:#f2a81b;box-shadow:0 0 0 3px #fff,0 0 10px #f2a81b}
.taskcard .arw{width:0;height:0;border-left:clamp(6px,1.2vmin,12px) solid transparent;
  border-right:clamp(6px,1.2vmin,12px) solid transparent;border-top:clamp(9px,1.8vmin,18px) solid #f2a81b}
.taskcard .who{height:clamp(26px,5vmin,52px)}
.taskcard .who img{height:100%;width:auto;object-fit:contain}

/* 气泡 / 提示手指 */''')

# ---------- 任务卡构造 ----------
rep('''function makeCard(n,pat){''',
    '''/** 视觉任务卡。
    mode="count" → 画 n 个红点（"要这么多"）
    mode="ordinal" → 画 n 个点、最后一个金色并带向下箭头（"第 n 个"） */
function taskCard(host,n,mode,who){
  const d=el("div","taskcard",host);
  if(who){ const w=el("div","who",d); img(A.ch(who),"",w); }
  n=clamp(n,1,10);
  for(let i=0;i<n;i++){
    const cell=el("div","",d);
    cell.style.cssText="display:flex;flex-direction:column;align-items:center;gap:2px";
    const dot=el("i",(mode==="ordinal"&&i<n-1)?"ghost":(mode==="ordinal"?"mark":""),cell);
    if(mode==="ordinal"&&i===n-1) el("div","arw",cell);
  }
  return d;
}
function makeCard(n,pat){''')

# ---------- 葫芦娃序数：加任务卡 + 提示整排亮 ----------
rep('''    ui.gs=gs; ui.field=field;
    ctx.answering(true);
    ctx.ask((st.isRetry?"再来一次！":"")+"爷爷说：该第"+cnSeq(q.target)+"个葫芦娃出来啦！点一点第"+cnSeq(q.target)+"个葫芦。",gs[0]);''',
    '''    ui.gs=gs; ui.field=field;
    field.dataset.glowall="1";                       // 提示时整排一起亮，绝不指某一个
    taskCard(L.top,q.target,"ordinal","yeye");       // 画出"第几个"，不再只靠语音
    ctx.answering(true);
    ctx.ask((st.isRetry?"再来一次！":"")+"爷爷说：该第"+cnSeq(q.target)+"个葫芦娃出来啦！点一点第"+cnSeq(q.target)+"个葫芦。",field);''')

# ---------- 金箍棒：加"要变长几格"的任务卡 ----------
rep('''    const okBtn=bigBtn(L.bot,"过河！","green",()=>submit());
    okBtn.disabled=true; ui.okBtn=okBtn;
    ctx.answering(true);''',
    '''    const okBtn=bigBtn(L.bot,"过河！","green",()=>submit());
    okBtn.disabled=true; ui.okBtn=okBtn;
    // reach 模式的目标由亮着的石墩表示；grow 模式的"变长几格"原来只在语音里 → 补任务卡
    if(q.mode!=="reach") ui.task=taskCard(L.top,q.need,"count","wukong");
    ctx.answering(true);''')

# ---------- 提示：支持"整排一起亮" ----------
rep('''      const isChoice=!!(t&&t.classList&&t.classList.contains("cards"));''',
    '''      const isChoice=!!(t&&t.classList&&(t.classList.contains("cards")||t.dataset.glowall==="1"));''')

# ---------- 提示节奏加快 ----------
rep('''    hintTimer=setInterval(()=>{
      if(!curW){ clearHint(); return; }
      if(Speech.busy()) return;                 // 引擎在说 → 退休
      if(Speech.sinceReq()<1500) return;        // 不插嘴''',
    '''    hintTimer=setInterval(()=>{
      if(!curW){ clearHint(); return; }
      if(Speech.engineBusy()) return;           // 引擎在说 → 退休
      if(Speech.sinceReq()<1500) return;        // 不插嘴''')
rep('''      }else{ hintStage=2; }
    },9000);''',
    '''      }else{ hintStage=2; }
    },5200);                                    // 三岁半等不了 9 秒：5 / 10 / 15 秒逐级推进''')

# ---------- firstTime：首次进入做一次不计分的手势示范 ----------
rep('''      cur=GAMES[id](makeCtx(w,my,first));
      cur.start();''',
    '''      cur=GAMES[id](makeCtx(w,my,first));
      cur.start();
      if(first){
        // 第一次来这个世界：等题目摆好后做一次手势示范（本题自动标记为"用过帮助"，不计掌握）
        T.after(2600,()=>{
          if(!alive(my)||!curW||curW.id!==id) return;
          markAssisted();
          const t=typeof hintTarget==="function"?hintTarget():hintTarget;
          if(t&&t.classList){
            if(t.classList.contains("cards")||t.dataset.glowall==="1")
              [].forEach.call(t.children,c=>c.classList.add("tapme"));
            else { t.classList.add("tapme"); Finger.at(t,2800); }
            SFX.tap();
            T.after(3000,()=>$$(".tapme").forEach(e=>e.classList.remove("tapme")));
          }
        });
      }''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
