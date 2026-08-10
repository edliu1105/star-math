# -*- coding: utf-8 -*-
"""「再说一遍」按钮要说当前这一步该做什么，不能永远重复本轮开头那句。"""
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


# 花果山：搭桥阶段 / 提问阶段说不同的话
rep('''    repeat:()=>{ if(!q) return;
      Speech.say(q.mode==="reach"?"桥要搭到亮着的石墩，接着往前点。"
        :(q.pre>0?("已经有"+cnQty(q.pre)+"格，再变长"+cnQty(q.need)+"格。")
                 :("把金箍棒变长"+cnQty(q.need)+"格。")),{tag:"repeat"}); },''',
    '''    repeat:()=>{ if(!q) return;
      if(st&&st.asking){ Speech.say("你一共加了几格呀？点一张卡片。",{tag:"repeat"}); return; }
      Speech.say(q.mode==="reach"?"桥要搭到亮着的那个石墩，接着往前点。"
        :(q.pre>0?("已经有"+cnQty(q.pre)+"格，再变长"+cnQty(q.need)+"格。")
                 :("把金箍棒变长"+cnQty(q.need)+"格。")),{tag:"repeat"}); },''')

# 复联：集结前 / 点数中 / 选卡时说不同的话
rep('''    repeat:()=>{ if(!q) return;
      Speech.say(q.kind==="pair"?"先点一个英雄，再点一个坏蛋。":"按黄色按钮让英雄集结，再数一数一共几个。",{tag:"repeat"}); },''',
    '''    repeat:()=>{ if(!q) return;
      if(q.kind==="pair"){ Speech.say("先点一个英雄，再点一个坏蛋。",{tag:"repeat"}); return; }
      if(!st||!st.assembled){ Speech.say("按黄色按钮，让两边的英雄合到一起。",{tag:"repeat"}); return; }
      if(ui&&ui.merged&&ui.counted<q.n){ Speech.say("点一点每一个英雄，数一数。",{tag:"repeat"}); return; }
      Speech.say("一共几个英雄呀？点一张卡片。",{tag:"repeat"}); },''')

# 汪汪队：点数阶段 / 回答总数阶段
rep('''    repeat:()=>{ if(!q) return;
      Speech.say(q.kind==="given"?"看看卡片上有几个点，就派几只狗狗。":"点一点小海龟，数一数一共几只。",{tag:"repeat"}); },''',
    '''    repeat:()=>{ if(!q) return;
      if(q.kind==="given"){ Speech.say("看看卡片上有几个点，就派出正好几只狗狗。",{tag:"repeat"}); return; }
      if(ui&&ui.objs&&ui.counted<q.n){ Speech.say("点一点小海龟，数一数。",{tag:"repeat"}); return; }
      Speech.say(q.kind==="plus1"?"再来一只，一共几只呀？":"一共几只呀？点一张卡片。",{tag:"repeat"}); },''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
