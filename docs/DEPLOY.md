# 部署指令

正式地址：**https://edliu1105.github.io/star-math/**

> ⚠️ 下面的命令会把**当前 `assets/chars/` 的内容原样推上去**。
> 如果你刚跑过 `python tools/apply_local_chars.py`，里面就是你自备的官方漫威图；
> 想推 AI 绘制版，先跑 `python tools/apply_local_chars.py --revert`。

## 一次性：建仓 + 推送 + 开 Pages

```bash
cd /d/ClaudeCode/kidmath2
```

**1. 建公开仓库**
```bash
"C:/Program Files/GitHub CLI/gh.exe" repo create edliu1105/star-math --public \
  --description "星星回家 · 幼儿数感建构互动应用" \
  --homepage "https://edliu1105.github.io/star-math/"
```

**2. 初始化并推送**
```bash
git init -q
git branch -M main
git remote add origin https://github.com/edliu1105/star-math.git
git add -A
git commit -q -m "星星回家：给三四岁孩子的数感建构互动应用"
git push -u origin main
```

**3. 开启 GitHub Pages（main / 根目录）**
```bash
"C:/Program Files/GitHub CLI/gh.exe" api -X POST repos/edliu1105/star-math/pages \
  -f "source[branch]=main" -f "source[path]=/"
```

**4. 强制 HTTPS**
```bash
"C:/Program Files/GitHub CLI/gh.exe" api -X PUT repos/edliu1105/star-math/pages -F https_enforced=true
```

**5. 等发布完成（1–3 分钟），确认返回 200**
```bash
curl -s -o /dev/null -w "%{http_code} %{url_effective}\n" -L https://edliu1105.github.io/star-math/
```

`gh api repos/edliu1105/star-math/pages` 可以看状态：`status` 变成 `built` 就好了。

---

## 以后更新

```bash
cd /d/ClaudeCode/kidmath2
git add -A && git commit -m "改了什么" && git push
```

推完在 iPad 上**刷新一次**页面（或从主屏图标重开一次）就是新版本。

> 原理：`sw.js` 对页面用网络优先 + 2.5 秒超时，新代码不会被旧缓存挡住；
> 素材用缓存优先，所以离线仍然完整可玩。**改了素材记得同时把 `sw.js` 里的 `VER` 加一位**，
> 否则旧素材缓存不会失效。

---

## 为什么一定要放在 `edliu1105` 组织下

个人账号 `behindthepixels` 的所有 Pages 会被博客自定义域名 `behindthepixels.io` **301 劫持且没有 HTTPS**，
这是账号级机制，没法按仓库关闭。所以仓库必须建在组织 `edliu1105` 名下。

部署后验证没有被劫持：
```bash
curl -sI -L https://edliu1105.github.io/star-math/ | grep -iE "^(HTTP|location)"
```
最终地址必须仍是 `edliu1105.github.io`，不能出现 `behindthepixels.io`。

---

## 二维码

```bash
python tools/make_qr.py https://edliu1105.github.io/star-math/
```
生成 `qrcode.png`，用 iPad 相机直接扫。

---

## 线上冒烟测试

```bash
python tests/test_live.py https://edliu1105.github.io/star-math/ --browser webkit
```
会检查：HTTP 200 / HTTPS / 无重定向到个人域名 / Service Worker 注册 / 六个世界各玩两轮 / 断网后仍可玩。

---

## 版权提示（说明，不阻拦）

公开发布受版权保护的角色形象（佩奇、Bluey、汪汪队、漫威）有被投诉下架的可能。
收到通知时最快的处置：
```bash
python tools/apply_local_chars.py --revert   # 换回 AI 绘制版
git add -A && git commit -m "替换素材" && git push
```
更彻底的做法是把角色显示名也换成原创名（西游记、葫芦娃属公有领域/国产经典，可保留）。
