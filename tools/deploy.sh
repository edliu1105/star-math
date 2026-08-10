#!/bin/bash
# 部署到 GitHub 组织 edliu1105 + 开启 Pages(main / 根目录) + enforce HTTPS
# 用法: bash tools/deploy.sh <repo-name>
set -e
GH="C:/Program Files/GitHub CLI/gh.exe"
ORG="edliu1105"
REPO="${1:?用法: bash tools/deploy.sh <repo-name>}"
PROJ="D:/ClaudeCode/kidmath2"
cd "$PROJ"

# 硬拦截：本地素材覆盖生效时绝不推送 —— 那些图是委托方自备的第三方美术，
# 覆盖的正是公开部署路径 assets/chars/，推上去就是公开转载。
if [ -f "$PROJ/LOCAL_OVERRIDE.txt" ]; then
  echo "!! 检测到 LOCAL_OVERRIDE.txt —— 本地素材覆盖正在生效，拒绝推送。"
  sed "s/^/     /" "$PROJ/LOCAL_OVERRIDE.txt"
  echo "   请先运行： python tools/apply_local_chars.py --revert"
  exit 1
fi

echo "==> 1/5 创建公开仓库 $ORG/$REPO"
"$GH" repo create "$ORG/$REPO" --public \
  --description "星星回家 · 给三四岁孩子的数感建构互动应用（瞬识/基数/守恒/分解/合并加法/接着数）" \
  --homepage "https://$ORG.github.io/$REPO/" || echo "(仓库可能已存在，继续)"

echo "==> 2/5 初始化并推送"
if [ ! -d .git ]; then
  git init -q
  git branch -M main
fi
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$ORG/$REPO.git"
git add -A
git -c user.name="behindthepixels" -c user.email="edliu@nvidia.com" \
    commit -q -m "星星回家：给三四岁孩子的数感建构互动应用

六个世界各教一种不同的数学认知，玩法来自角色本身的能力：
瞬识 / 一一对应·基数·Give-N / 比较·守恒 / 序数·部分整体 / 合并加法 / 接着数。
每题独立作答 + 分技能纠错 + 同构新题复测，封死猜测与背诵通关。
单文件 vanilla JS + PWA 离线可玩，针对 iPad WebKit 做了完整的语音兼容处理。" || echo "(无新提交)"
git push -u origin main --force

echo "==> 3/5 开启 GitHub Pages (main / 根目录)"
"$GH" api -X POST "repos/$ORG/$REPO/pages" \
  -f "source[branch]=main" -f "source[path]=/" 2>/dev/null \
  || "$GH" api -X PUT "repos/$ORG/$REPO/pages" -f "source[branch]=main" -f "source[path]=/" \
  || echo "(Pages 可能已开启)"

echo "==> 4/5 强制 HTTPS"
sleep 6
"$GH" api -X PUT "repos/$ORG/$REPO/pages" -F https_enforced=true || echo "(稍后重试 https_enforced)"

echo "==> 5/5 等待发布"
URL="https://$ORG.github.io/$REPO/"
for i in $(seq 1 40); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -L "$URL" || echo 000)
  echo "  [$i] $URL -> $CODE"
  if [ "$CODE" = "200" ]; then break; fi
  sleep 15
done

echo
echo "=== 部署完成 ==="
echo "URL: $URL"
"$GH" api "repos/$ORG/$REPO/pages" --jq '{status:.status,url:.html_url,https:.https_enforced,branch:.source.branch,path:.source.path}'
