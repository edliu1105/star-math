# 第四轮评审任务（第三轮问题的闭环核对）

## 先读
1. `docs/REVIEW_BRIEF.md` —— 职责与输出格式
2. `docs/RESPONSE-R3.md` —— **本轮要核对的逐条回应**（含委托方对 IP 与真机两项的裁决）
3. `index.html`、`sw.js`
4. 测试：`tests/test_app.py`（A–H）、`tests/test_gates.py`（G1/G1b/G2/G3/G4/G5/G5b/G6）、`tests/test_wrong.py`
5. 日志：`shots/test-chromium-r3.log`(137/0/0)、`shots/test-wrong.log`(14/0)、
   `shots/test-webkit.log`(84/0/1)、`shots/test-gates.log`（本轮正在重跑，可能是半截文件）

## 请逐条判定是否闭环（都在 `index.html` 里核对，不要采信文档）
- 6-1 `say()` 是否已改用 `engineBusy()`
- 6-2 `holdChannel()` 是否返回令牌、`releaseChannel(tok)` 是否校验令牌、
      `stopScope()` 是否 `clearTimers()` + `chanToken++` + 用 `engineBusy()` 判断打断
- 6-3 六个游戏的 `repeat()` 是否都改成**返回文本**、顶栏是否统一 `Speech.replay()`
- 6-4 补说是否带 `isFirst`、`fire()` 探针是否据此判首句
- 4-1 花果山预置期是否 `st.locked=true` 且带 `st!==my` 身份检查；Bluey 删除监听是否改 `busyState(st)`
- 1-2 `numPop()` / 计数角标是否统一经过 `Store.symbols()`（未解锁时用 `pipRow()` 圆点）
- 2-1 成人门是否"答错即关门 + 连对两题"
- 1-3 `patDiffers()` 是否改成点集 Hausdorff（并验证 `n=3 dice→ring` 会被判为太像）
- 3-2 掌握徽章是否 6 格
- 5-1 地图是否改用 `assets/bgthumb/`（512px，7 张共 153KB）
- 5-2 `Assets.one()` 是否失败不写缓存 + 超时兜底
- 3-1b `apply_local_chars.py` 是否写 `LOCAL_OVERRIDE.txt`、`tools/deploy.sh` 是否据此 `exit 1`
- 1-1 掌握门是否加了 `wins>=2`，且 `winAt` 比对的是**应用启动次数 `d.sess`**（不是进世界次数 `plays`）
- 4-2 测试盲区：G1b（固定位置+答案洗牌 200 轮）、G5b、`set_level` 写 mast/wins/sess、
      H 组六世界、D 组目标越界断言 —— 是否都已补上

## 仍未做的两项，请判断是否阻断（我认为不阻断，理由见 RESPONSE-R3）
- 2-2 花果山任务卡缺"新增"语义（准备改成"已有灰格 → 新增 n 个红格"）
- 2-3 首次示范不是完整动作链

## 输出
严格按 `REVIEW_BRIEF.md` 六维度格式。**最后一行** `VERDICT: APPROVE` 或 `VERDICT: REJECT`。
若因 IP / 真机而 REJECT，请把它们**单列为"委托方已知情并接受的未关闭项"**，与技术缺陷分开。
