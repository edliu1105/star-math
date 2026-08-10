# -*- coding: utf-8 -*-
"""codex 第二轮抓到的两个发布级问题：

R2-1【严重】解锁死锁：解锁条件是"上一个世界 L2 且 ⭐≥4"，但一个始终答错的孩子
      星星会一路加满 10 颗、难度却永远停在 L1 —— 于是**满星了下一个世界还是打不开**，
      而孩子界面只显示星星、不显示难度，家长完全看不出原因。
      修：再加一条"⭐ 满 10 颗也解锁"的兜底通路，保证任何情况下都不会卡死。

R2-2【严重】三级提示的手指会指向选择题的**第一张卡**，而那常常是错的 ——
      等于手把手教孩子点错误答案。
      修：选择题的提示改为"把所有卡片一起点亮"（告诉孩子该在这一排里选），
      永远不指向具体某一张。
"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()
n = 0
miss = []


def rep(a, b, cnt=1):
    global s, n
    if a in s:
        s = s.replace(a, b, cnt); n += s.count(b) and 1 or 1
    else:
        miss.append(a[:76].replace("\n", "\\n"))


# ---------- R2-1 解锁兜底 ----------
rep('''  function refreshUnlocks(){
    let changed=false;
    for(let i=1;i<ORDER.length;i++){
      const prev=W(ORDER[i-1]), cur=W(ORDER[i]);
      if(!cur.open && prev.lv>=2 && prev.stars>=4){ cur.open=1; changed=true; }
    }
    return changed;
  }''',
'''  function refreshUnlocks(){
    let changed=false;
    for(let i=1;i<ORDER.length;i++){
      const prev=W(ORDER[i-1]), cur=W(ORDER[i]);
      if(cur.open) continue;
      // 正常通路：上一个世界达到 L2 且 ⭐>=4（有掌握证据）
      // 兜底通路：⭐ 满了也开 —— 否则一个始终答错的孩子会星满却永远打不开下一个世界，
      //           而孩子界面只显示星星，没人看得出为什么卡住
      if((prev.lv>=2 && prev.stars>=4) || prev.stars>=STARS_FULL){ cur.open=1; changed=true; }
    }
    return changed;
  }''')

# ---------- R2-2 选择题提示不指向具体卡片 ----------
rep('''.cobj.tapme{animation:tapme 1.1s ease-in-out infinite}''',
    '''.cobj.tapme,.card.tapme{animation:tapme 1.1s ease-in-out infinite}''')

rep('''      if(hintStage===1){
        const t=typeof hintTarget==="function"?hintTarget():hintTarget;
        if(t&&t.classList) t.classList.add("tapme");
        SFX.tap();
      }else if(hintStage===2){
        Speech.nudge(hintText,{tag:"hint-repeat"});
      }else if(hintStage===3){
        const t=typeof hintTarget==="function"?hintTarget():hintTarget;
        if(t) Finger.at(t,3000);
      }else{ hintStage=2; }''',
'''      const t=typeof hintTarget==="function"?hintTarget():hintTarget;
      // 选择题：只提示"在这一排里选一张"，绝不指向具体某一张
      // （手指指到第一张卡就等于手把手教孩子点错误答案）
      const isChoice=!!(t&&t.classList&&t.classList.contains("cards"));
      const glow=()=>{
        if(!t||!t.classList) return;
        if(isChoice) [].forEach.call(t.children,c=>c.classList.add("tapme"));
        else t.classList.add("tapme");
      };
      if(hintStage===1){ glow(); SFX.tap(); }
      else if(hintStage===2){ Speech.nudge(hintText,{tag:"hint-repeat"}); }
      else if(hintStage===3){
        if(isChoice){ glow(); SFX.tap(); }        // 不出手指，只让整排卡片一起亮
        else if(t) Finger.at(t,3000);
      }else{ hintStage=2; }''')

# ---------- 所有选择题的提示目标从"第一张卡"改成"整排卡片" ----------
for old, new in [
    ('ctx.ask("刚才有几个泥点呀？点一张卡片。",()=>wrap.firstChild);',
     'ctx.ask("刚才有几个泥点呀？点一张卡片。",wrap);'),
    ('ctx.ask(plus?"如果再来一只，一共几只呀？":"一共几只呀？点一张卡片。",()=>wrap.firstChild);',
     'ctx.ask(plus?"如果再来一只，一共几只呀？":"一共几只呀？点一张卡片。",wrap);'),
    ('ctx.ask("一共几个英雄呀？点一张卡片。",()=>wrap.firstChild);',
     'ctx.ask("一共几个英雄呀？点一张卡片。",wrap);'),
    ('ctx.ask("英雄够不够呀？",()=>wrap.firstChild);',
     'ctx.ask("英雄够不够呀？",wrap);'),
    ('ctx.ask("你一共加了几格呀？点一张卡片。",()=>wrap.firstChild);',
     'ctx.ask("你一共加了几格呀？点一张卡片。",wrap);'),
    ('''    ctx.ask(st.isRetry?"再看看这一次：谁的多呀？":(q.mode==="cons"?"爸爸把饼干摆得不一样啦！谁的多呀？还是一样多？":"谁的多呀？点一下他。"),
            ()=>wrap.firstChild);''',
     '''    ctx.ask(st.isRetry?"再看看这一次：谁的多呀？":(q.mode==="cons"?"爸爸把饼干摆得不一样啦！谁的多呀？还是一样多？":"谁的多呀？点一下他。"),
            wrap);'''),
]:
    rep(old, new)

# 揭示答案时用的 Finger.at(正确卡) 保留 —— 那是"已经放弃、直接告诉答案"，指对是对的

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n, "blocks")
if miss:
    print("MISSED %d:" % len(miss))
    for m in miss:
        print("  !", m)
