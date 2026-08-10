# -*- coding: utf-8 -*-
"""测试增强：
   1) 给 WebKit 补 SpeechSynthesisUtterance / getVoices 桩，让它也走完整语音路径
      （Playwright WebKit 不带语音合成，但 iPad Safari 带）
   2) 新增 H 组：完全没有语音引擎时，仍必须能完整通关（这是我对"不做本地录音兜底"的承诺）
"""
import io, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "test_app.py")
s = io.open(p, encoding="utf-8").read()
n = 0


def rep(a, b):
    global s, n
    if a in s:
        s = s.replace(a, b, 1); n += 1
    else:
        print("MISS:", a[:70].replace("\n", "\\n"))


rep('''window.__spk = [];
(function(){
  var S = window.speechSynthesis;
  if(!S){''',
    '''window.__spk = [];
(function(){
  // WebKit(Playwright) 不带语音合成，但 iPad Safari 带 —— 补桩以走完整语音路径
  if(typeof window.SpeechSynthesisUtterance !== "function"){
    window.SpeechSynthesisUtterance = function(t){
      this.text = t; this.lang = ""; this.voice = null;
      this.rate = 1; this.pitch = 1; this.volume = 1;
      this.onend = null; this.onerror = null; this.onstart = null;
    };
  }
  var S = window.speechSynthesis;
  if(!S){''')

rep('''  S.cancel = function(){
    window.__lastCancel = Date.now();
    window.__cancels = (window.__cancels||0) + 1;
    busyUntil = 0;
    try{ realCancel(); }catch(e){}
  };
})();
"""''',
    '''  S.cancel = function(){
    window.__lastCancel = Date.now();
    window.__cancels = (window.__cancels||0) + 1;
    busyUntil = 0;
    try{ realCancel(); }catch(e){}
  };
  // 固定一份声音列表：既覆盖 iOS 的 Ting-Ting，也验证中文优先与打分逻辑
  S.getVoices = function(){
    return [{name:"Samantha", lang:"en-US", localService:true},
            {name:"Ting-Ting", lang:"zh-CN", localService:true},
            {name:"Mei-Jia",   lang:"zh-TW", localService:true}];
  };
})();
"""

# 完全没有语音引擎的环境（最坏情况：iPad 上一个中文声音都没装）
NO_SPEECH = r"""
window.__spk = [];
try{ Object.defineProperty(window, "speechSynthesis", {get:function(){return undefined;}, configurable:true}); }catch(e){}
try{ delete window.SpeechSynthesisUtterance; }catch(e){}
window.SpeechSynthesisUtterance = undefined;
"""''')

rep('''        finally:
            browser.close()''',
    '''            # ============ H. 完全没有语音引擎 ============
            print("\\n=== H. 无语音引擎时仍可完整游玩 ===")
            ctxb = browser.new_context(viewport={"width": 1180, "height": 820}, has_touch=True)
            ctxb.add_init_script(NO_SPEECH)
            page = ctxb.new_page(); C = Ctx(page)
            page.goto(BASE)
            page.wait_for_function("window.__ready===true", timeout=15000)
            check(True, "无语音引擎时应用仍能启动")
            set_level(page, 2); page.reload(); page.wait_for_function("window.__ready===true")
            page.click("#startBtn", force=True)
            page.wait_for_selector("#map.on", timeout=6000)
            check(page.is_visible("#soundHint"), "无语音时自动出现喇叭提示条（用引擎状态判定，不靠事件）")
            for w in ("peppa", "paw", "monkey"):
                enter_world(page, w)
                got = play_session(page, w, rounds=3, timeout_s=120)
                check(got >= 3, "无语音时 %s 仍可完整通关（完成 %d/3 轮）" % (w, got))
                if page.query_selector("#stage.on"):
                    page.click("#homeBtn", force=True)
                page.wait_for_selector("#map.on", timeout=8000)
            page.screenshot(path=os.path.join(SHOTS, "H-no-speech.png"))
            check(len(C.errors) == 0, "无语音时零 console error（%s）" % C.errors[:3])
            ctxb.close()

        finally:
            browser.close()''')

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", n)
