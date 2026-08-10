# -*- coding: utf-8 -*-
"""入口手势顺序：把最脆弱的 TTS 首句放在同步栈的最前面，
   再做 AudioContext 解锁与无声 audio 循环 —— 三者仍在同一个 click 任务里。"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()

old = '''    $("#startBtn").addEventListener("click",function(){
      SFX.gesture();
      Audio2.kick();
      Speech.unlockAndSay("欢迎来到星星回家！我们一起帮朋友们把星星送回天上吧！");
      buildMap(); show("map"); SFX.star();
    });'''
new = '''    $("#startBtn").addEventListener("click",function(){
      // 顺序有意为之：TTS 首句最脆弱，放在同步栈最前；
      // AudioContext 解锁与无声 audio 循环紧随其后，三者同属这一次 click 任务。
      Speech.unlockAndSay("欢迎来到星星回家！我们一起帮朋友们把星星送回天上吧！");
      SFX.gesture();
      Audio2.kick();
      buildMap(); show("map"); SFX.star();
    });'''
assert old in s, "gate handler not found"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("gate order fixed")
