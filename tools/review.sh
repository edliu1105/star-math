#!/bin/bash
# 调用 codex (gpt-5.6-sol, max reasoning) 做里程碑评审
# 注意：codex 的 -i/--image 是可变参数，会吞掉后面的位置参数 —— 提示词必须放在图片之前
# 用法: bash tools/review.sh <任务文件> [截图1 截图2 ...]
CODEX="C:/Users/edliu/AppData/Local/OpenAI/Codex/bin/cfac6bda2d141e07/codex.exe"
PROJ="D:/ClaudeCode/kidmath2"
TASK="${1:?用法: bash tools/review.sh <docs/REVIEW-*.md> [截图...]}"
shift
cd "$PROJ"
PROMPT="$(cat "$TASK")"
IMGS=()
for f in "$@"; do IMGS+=(-i "$PROJ/$f"); done
"$CODEX" exec -C "$PROJ" --skip-git-repo-check -s read-only \
  -m gpt-5.6-sol -c model_reasoning_effort='"max"' \
  "$PROMPT" "${IMGS[@]}" < /dev/null
