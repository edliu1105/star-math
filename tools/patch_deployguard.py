# -*- coding: utf-8 -*-
"""部署路径隔离（codex 3-1b）：
   apply_local_chars.py 覆盖的正是公开部署路径 assets/chars/，
   仅把 incoming/ 加进 .gitignore 并不能阻止工作树把第三方素材部署出去。
   处置：应用时写 LOCAL_OVERRIDE.txt 标记，deploy.sh 见到它就拒绝推送。"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

p = os.path.join(ROOT, "tools", "apply_local_chars.py")
s = io.open(p, encoding="utf-8").read()

a = ('    print("\\n完成 %d 个。用 shots/sheet-chars.png 目检（跑 python tools/contact_sheet.py）。" % len(todo))\n'
     '    print("还原：python tools/apply_local_chars.py --revert")')
b = ('    # 关键：这些文件覆盖的就是公开部署路径 assets/chars/。\n'
     '    # 写一个标记，deploy.sh 见到它会直接拒绝推送，必须先 --revert。\n'
     '    with io.open(os.path.join(ROOT, "LOCAL_OVERRIDE.txt"), "w", encoding="utf-8") as f:\n'
     '        f.write("本地素材覆盖生效中，以下文件来自 incoming/（委托方自备，非本仓库产出）：\\n")\n'
     '        for dst2, src2 in todo:\n'
     '            f.write("  %s  <-  %s\\n" % (dst2, os.path.basename(src2)))\n'
     '        f.write("\\n公开部署前必须先运行：python tools/apply_local_chars.py --revert\\n")\n'
     '    print("\\n完成 %d 个。用 shots/sheet-chars.png 目检（跑 python tools/contact_sheet.py）。" % len(todo))\n'
     '    print("已写 LOCAL_OVERRIDE.txt —— 在它存在期间 tools/deploy.sh 会拒绝推送。")\n'
     '    print("还原：python tools/apply_local_chars.py --revert")')
if a in s:
    s = s.replace(a, b, 1)
    print("apply_local_chars: 覆盖标记 ok")
else:
    print("apply_local_chars: 覆盖标记 已存在或未命中")

a2 = '        print("已还原 %d 个文件" % k); sys.exit(0)'
b2 = ('        mk = os.path.join(ROOT, "LOCAL_OVERRIDE.txt")\n'
      '        if os.path.exists(mk):\n'
      '            os.remove(mk)\n'
      '        print("已还原 %d 个文件，LOCAL_OVERRIDE.txt 已移除" % k); sys.exit(0)')
if a2 in s:
    s = s.replace(a2, b2, 1)
    print("apply_local_chars: 还原时清标记 ok")
io.open(p, "w", encoding="utf-8", newline="").write(s)

q = os.path.join(ROOT, "tools", "deploy.sh")
t = io.open(q, encoding="utf-8").read()
a3 = 'cd "$PROJ"\n\necho "==> 1/5 创建公开仓库 $ORG/$REPO"'
b3 = ('cd "$PROJ"\n\n'
      '# 硬拦截：本地素材覆盖生效时绝不推送 —— 那些图是委托方自备的第三方美术，\n'
      '# 覆盖的正是公开部署路径 assets/chars/，推上去就是公开转载。\n'
      'if [ -f "$PROJ/LOCAL_OVERRIDE.txt" ]; then\n'
      '  echo "!! 检测到 LOCAL_OVERRIDE.txt —— 本地素材覆盖正在生效，拒绝推送。"\n'
      '  sed "s/^/     /" "$PROJ/LOCAL_OVERRIDE.txt"\n'
      '  echo "   请先运行： python tools/apply_local_chars.py --revert"\n'
      '  exit 1\n'
      'fi\n\n'
      'echo "==> 1/5 创建公开仓库 $ORG/$REPO"')
if a3 in t:
    t = t.replace(a3, b3, 1)
    io.open(q, "w", encoding="utf-8", newline="").write(t)
    print("deploy.sh: 拦截 ok")
else:
    print("deploy.sh: 拦截 已存在或未命中")

# 自检：模拟标记存在时的判定
mk = os.path.join(ROOT, "LOCAL_OVERRIDE.txt")
io.open(mk, "w", encoding="utf-8").write("selftest\n")
blocked = os.path.exists(mk)
os.remove(mk)
print("自检：标记存在时 deploy.sh 会 exit 1 →", blocked)
print("自检：标记已清除 →", not os.path.exists(mk))
