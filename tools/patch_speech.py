# -*- coding: utf-8 -*-
"""修复：计数通道没有遵守 cancel→speak 的 ≥150ms 间隔（军规②），
   也没有给"待播指令"让路 —— 会在 iOS 上把刚 cancel 的队列重新卡死。"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = io.open(p, encoding="utf-8").read()

old = '''    const flush=()=>{
      cntTimer=null;
      if(cntLatest==null) return;
      if(busy()){ cntTimer=setTimeout(flush,120); return; }   // 等空闲，不打断
      const t=cntLatest; cntLatest=null;'''
new = '''    const flush=()=>{
      cntTimer=null;
      if(cntLatest==null) return;
      // 军规②：cancel 之后必须先等满 CANCEL_GAP，计数通道也不例外
      const gap=Date.now()-lastCancelAt;
      if(gap<CANCEL_GAP){ cntTimer=setTimeout(flush,CANCEL_GAP-gap+10); return; }
      // 指令通道有待播的一条时让路，避免刚起播就被 fire() 顶掉
      if(pendTimer){ cntTimer=setTimeout(flush,120); return; }
      if(busy()){ cntTimer=setTimeout(flush,120); return; }   // 等空闲，绝不打断
      const t=cntLatest; cntLatest=null;'''
assert old in s, "flush block not found"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("speech count channel patched")
