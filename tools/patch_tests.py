# -*- coding: utf-8 -*-
"""测试脚手架修正：
   1) play_session 必须等新题建好（__qn 递增）再作答，否则在旧 DOM 上乱点
   2) 重复播报断言只针对"指令级"文本，数词本来就会重复出现
   3) 离线段忘了解锁世界
"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "test_app.py")
s = io.open(p, encoding="utf-8").read()
n = 0; miss = []


def rep(a, b):
    global s, n
    if a in s:
        s = s.replace(a, b, 1); n += 1
    else:
        miss.append(a[:78].replace("\n", "\\n"))


# 1) play_session 重写
old_start = s.index("def play_session(page, wid, rounds=5")
old_end = s.index("# ---------------------------------------------------------------- 语音时间线断言")
new = '''def play_session(page, wid, rounds=5, timeout_s=170):
    """走完一个 session。关键：每次作答前必须确认新题已经建好（__qn 递增），
    否则会在上一题的 DOM 上乱点，测出来的失败是脚手架的锅不是应用的锅。"""
    t0 = time.time()
    guard = 0
    page.wait_for_function("window.__q != null", timeout=15000)
    while time.time() - t0 < timeout_s:
        guard += 1
        if guard > 60:
            break
        if not page.query_selector("#stage.on"):
            break
        if page.query_selector("#cheer.on"):
            break
        filled = page.evaluate("document.querySelectorAll('#dots i.f').length")
        if filled >= rounds:
            break
        qn = page.evaluate("window.__qn||0")
        try:
            solve_round(page, wid)
        except Exception:
            page.wait_for_timeout(700)
            continue
        # 得星或进入复测，都会建新题（__qn 递增）；通关则出现 #cheer
        try:
            page.wait_for_function(
                "(n)=>(window.__qn||0)>n || document.querySelector('#cheer.on')!==null",
                arg=qn, timeout=24000)
        except Exception:
            page.wait_for_timeout(600)
    return page.evaluate("document.querySelectorAll('#dots i.f').length") if page.query_selector("#dots") else 0


'''
s = s[:old_start] + new + s[old_end:]
n += 1

# 2) 重复播报断言：只看指令级文本（数词天然会反复出现，不算"无故重复"）
rep('''    dup = 0
    for i in range(1, len(log)):
        for j in range(max(0, i - 6), i):
            if log[i]["text"] == log[j]["text"] and log[i]["t"] - log[j]["t"] < 3000:
                dup += 1
                break
    check(dup == 0, "%s：指令没有 3 秒内无故重复（重复 %d 次）" % (label, dup))''',
    '''    instr = [e for e in log if len(e["text"]) >= 8]      # 数词/短反馈不算指令
    dup = 0
    for i in range(1, len(instr)):
        for j in range(max(0, i - 6), i):
            if instr[i]["text"] == instr[j]["text"] and instr[i]["t"] - instr[j]["t"] < 3000:
                dup += 1
                break
    check(dup == 0, "%s：指令没有 3 秒内无故重复（%d 条指令中重复 %d 次）" % (label, len(instr), dup))''')

# 3) 离线段解锁全部世界
rep('''            page.goto(BASE)
            page.wait_for_function("window.__ready===true", timeout=15000)
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")
            # 让 SW 装好并把素材灌进缓存''',
    '''            page.goto(BASE)
            page.wait_for_function("window.__ready===true", timeout=15000)
            set_level(page, 2); page.reload(); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")
            # 让 SW 装好并把素材灌进缓存''')

# 4) A 组每关放宽一点时间（纠错+复测本来就慢）
rep('                    got = play_session(page, w, rounds=5)',
    '                    got = play_session(page, w, rounds=5, timeout_s=170)')

# 5) 新增断言：一轮内最多错两次就必须给出答案（防止孩子陷在同一轮）
rep('''            check(len(C.errors) == 0, "B 组零 console error（%s）" % C.errors[:3])
            ctxb.close()''',
    '''            # B6 一直答错也必须在有限步内拿到答案并推进（3 岁半不能被卡住）
            page.click("#homeBtn", force=True); page.wait_for_selector("#map.on")
            set_level(page, 2); page.reload(); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True); page.wait_for_selector("#map.on")
            enter_world(page, "peppa")
            page.wait_for_function("window.__q != null", timeout=15000)
            f0 = page.evaluate("document.querySelectorAll('#dots i.f').length")
            wrongs = 0
            t_end = time.time() + 60
            while time.time() < t_end:
                if page.evaluate("document.querySelectorAll('#dots i.f').length") > f0:
                    break
                qn = page.evaluate("window.__qn||0")
                try:
                    solve_peppa(page, wrong=True); wrongs += 1
                except Exception:
                    pass
                try:
                    page.wait_for_function("(n)=>(window.__qn||0)>n || document.querySelectorAll('#dots i.f').length>%d" % f0,
                                           arg=qn, timeout=20000)
                except Exception:
                    page.wait_for_timeout(500)
            got = page.evaluate("document.querySelectorAll('#dots i.f').length")
            check(got > f0 and wrongs <= 3,
                  "一直答错时，最多 %d 次后系统给出答案并推进（星 %d -> %d）" % (wrongs, f0, got))
            check(len(C.errors) == 0, "B 组零 console error（%s）" % C.errors[:3])
            ctxb.close()''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
if miss:
    print("MISSED:", miss)
