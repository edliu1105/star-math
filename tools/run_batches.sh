#!/bin/bash
# 并行跑素材生成批次。用法: bash tools/run_batches.sh <并发数> [批次号...]
CODEX="C:/Users/edliu/AppData/Local/OpenAI/Codex/bin/cfac6bda2d141e07/codex.exe"
PROJ="D:/ClaudeCode/kidmath2"
CONC="${1:-6}"; shift
mkdir -p "$PROJ/batches/log"

if [ "$#" -gt 0 ]; then BATCHES="$@"; else BATCHES=$(ls "$PROJ/batches"/b*.txt | sed 's/.*b\([0-9]*\)\.txt/\1/' | sort -n); fi

run_one() {
  local n="$1"
  local f="$PROJ/batches/b${n}.txt"
  [ -f "$f" ] || return 0
  echo "[start] batch $n"
  "$CODEX" exec -C "$PROJ" --skip-git-repo-check -s workspace-write \
      -c model_reasoning_effort='"low"' "$(cat "$f")" \
      > "$PROJ/batches/log/b${n}.log" 2>&1
  echo "[done ] batch $n rc=$?"
}

i=0
for n in $BATCHES; do
  run_one "$n" &
  i=$((i+1))
  if [ $((i % CONC)) -eq 0 ]; then wait; fi
done
wait
echo "ALL BATCHES FINISHED"
