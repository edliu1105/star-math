# 第三轮评审任务（对第二轮 REJECT 的逐条闭环）

## 先读这些

1. `docs/REVIEW_BRIEF.md` —— 你的评审职责、六个维度、iOS 军规 checklist、输出格式（**必须遵守**）
2. `docs/RESPONSE-R1.md` —— **末尾「第二轮评审（REJECT）的逐条回应」章节**是本轮要核对的内容
3. `index.html` —— 全部实现（单文件）
4. `sw.js` / `manifest.webmanifest`
5. 测试：`tests/test_app.py`（全量门槛 A–H）、`tests/test_gates.py`（掌握门槛专项）、`tests/test_wrong.py`（答错路径专项）
6. **本轮测试证据**（都是跑完的完整日志）：
   - `shots/test-chromium-r3.log` —— 全量门槛 Chromium **137 通过 / 0 失败 / 0 警告**
   - `shots/test-gates.log` —— 掌握门槛专项 **13 通过 / 0 失败**
   - `shots/test-wrong.log` —— 答错路径专项 **14 通过 / 0 失败**
   - `shots/test-webkit.log` —— WebKit（iPad Safari 同源引擎）A 组跑 L1+L3，B–H 全跑。
     **注意：这一份可能仍在跑，是半截文件**；前三份是跑完的完整日志，请以它们为准。
     WebKit 每个世界比 Chromium 慢约 8 倍，所以 A 组只跑 L1+L3（这两级已覆盖全部题型），
     四个难度的穷举由 Chromium 承担。
   - `shots/r3/` —— 本轮重新拍的证据截图（标注准确）：
     `1-map-locked.png` 锁态地图、`2-peppa-flash.png` 真实闪现帧、
     `3-map-badges.png` 参与星与掌握徽章并存、
     `4-hulu-taskcard.png` 序数任务卡、`5-monkey-taskcard.png` 数量任务卡

## 你上一轮列的五个发布阻断项，请逐条判定是否闭环

1. **满星绕过掌握**
   - 已删除 `prev.stars>=STARS_FULL` 兜底
   - 新增独立字段 `mast`（只由"新题 + 未用提示"的首答累计）
   - 解锁改为三条件同时成立：`prev.lv>=2 && prev.mast>=6 && recentRate(prev)>=0.6`
     （`recentRate` = 最近 10 次无提示首答的正确率；乱点期望只有 0.25，**结构上跨不过去**）
   - 参与与掌握用两套 UI：金色圆形星（参与） vs 绿色菱形徽章（掌握）
   - **确定性证据**：`test_gates.py` G1「固定乱点 100 轮」→ 难度仍 L1、`mast` 仍为 0、第三个世界仍锁着，
     而参与星照常累计到 10。请核对 `Store.refreshUnlocks()` / `recentRate()` 与该日志。

2. **提示后仍写掌握证据**
   - 新增全局 `markAssisted()`；调用点：三级自动提示的**每一级**、顶栏「再说一遍」、
     金箍棒 `autoFix()`、首次进入的示范
   - 每题 `bindState()` 登记当前状态，`record()` 检查 `st.hinted`
   - 证据：G2/G3（手动重看后答对、顶栏重播后答对，`mast`/`tries` 均不变）

3. **无语音时任务不自足**
   - 葫芦娃"第几个" → `taskCard(..., "ordinal")`：n 个点、最后一个金色并带向下箭头 + 爷爷头像
   - 金箍棒 grow 模式"变长几格" → `taskCard(..., "count")`：need 个红点 + 悟空头像
   - 请判断这两张卡是否真的让**不识字、听不见**的孩子知道要做什么；不够就直说还缺什么

4. **题目级竞态**
   - 每题状态加 `locked`；所有输入路径统一走 `busyState(st)`
   - 所有会推进流程的异步序列开头 `const my=st`，回调里 `st!==my` 即退出
   - 覆盖：peppa.remediate / paw.remedyCardinal+remedyGiveN / bluey.verify+pairDone /
     hulu.ordRemedy+missRemedy / aveng.remedyAdd+pair纠错 / monkey.remedy+remedyCountOn
   - 证据：答错专项 14/0（六世界 × L2/L4 全程答错，零 console error）

5. **iOS 语音竞态**
   - `voiceschanged` 补说改为可重排任务 `scheduleFirstRedo()`：引擎忙或距上次请求 <1.5s 就**重排**，
     **不再把"引擎忙"当成首句成功**
   - 「检测到引擎活动」`engineSeen` 与「首句确认发声」`firstOk` 拆成两个状态，诊断面板分两行显示
   - 两条通道都维护本地 `active/activeUntil`，`speak()` 后立刻占用通道；计数通道加 watchdog
   - 顶栏重播 / 声音提示条改走受控 `Speech.replay()`（安全打断 + 800ms 节流）
   - 离开世界 `Speech.stopScope()`：epoch 自增作废旧回调、清待播、失效 watchdog、必要时安全打断

## 你上一轮的其它意见，处置如下（也请核对）

- 1-4 符号门 → 改为按课程先修：必须 peppa/paw/bluey **三个世界都 L3 且 mast>=6**
- 1-5 `apat!==qpat` 只比名字 → 新增 `patDiffers()` 按**实际坐标距离**判定，`pickAnswerPat()` 保证几何差异；G4 对 n=1..6 全覆盖断言
- 2-3 `firstTime` 未使用 / 提示太慢 → 首次进入做一次**不计分手势示范**；提示节奏 9/18/27 秒 → **5/10/15 秒**
- 2-4 成人门可穷举 → 答错立即换题；G5 断言"连点三个错误选项进不去"
- 6-1 入口防重入 → `started` 同步锁
- 6-10 `.zbot` 安全区 → 已加 `safeB/safeL/safeR`
- 3-3 我上一轮附图标注不准 → 本轮附图重新给：闪现帧、锁态地图、掌握徽章

## 仍然保留的分歧（请给最终裁决）

- **IP**：委托方已明确决定并亲自提供素材。当前处置是：**公开仓库只包含 AI 绘制版**；
  委托方自行获取的官方漫威美术走 `incoming/` + `tools/apply_local_chars.py`，**该目录不入 git**，
  仅供其本地/家庭使用。我不会把官方美术推送到公开仓库。请判断这个处置是否可以放行公开部署。
- **真机验收**：仍无物理 iPad。清单在 `docs/IPAD-CHECKLIST.md`，结果需委托方回填。
  请明确：在真机结果回填之前，你是否允许"先上线、再回填"，还是必须先拿到真机结果。

## 未做的（请判断是否阻断）

- 1-2 你要求"升级至少要求两个跨会话独立窗口 + 非选择题建构任务"：
  我改成了**比例门槛**（最近 10 次正确率 ≥0.6）+ 累计 ≥6 + L2，并用固定乱点 100 轮做了确定性验证。
  如果你认为比例门槛仍不够，请说明它在哪种具体行为下会被攻破。
- 1-6 复联 L3 的 count-on 早于花果山：未改。理由是复联 L3 只在**合并之后**从 a 接着数，
  属于同一堂课的自然延伸；且花果山本身有独立的先修门控。如你坚持，我改成合并后从 1 数全体。
- 5-1 地图六张全尺寸背景常驻：未改。请判断是否阻断（当前地图卡背景 opacity .4，用的是 1280px JPEG）。

## 输出

严格按 `docs/REVIEW_BRIEF.md` 的六维度格式，最后一行 `VERDICT: APPROVE` 或 `VERDICT: REJECT`。
若 APPROVE，请一并列出"上线前必须人工确认的事项"。
