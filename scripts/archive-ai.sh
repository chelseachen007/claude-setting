#!/usr/bin/env bash
# 把 ~/ai 同步到 claude-setting 仓库，形成 AI 资产版本档案。
#
# 用法:
#   bash ~/ai/scripts/archive-ai.sh              # 同步 + 显示 diff，不提交
#   bash ~/ai/scripts/archive-ai.sh --commit     # 同步 + 自动提交 + 推送
#   bash ~/ai/scripts/archive-ai.sh --commit -m "自定义说明"
#
# 想改提交信息但不想自动推: --commit 后手动 git push

set -euo pipefail

SRC="$HOME/ai"
REPO="${CLAUDE_SETTING_REPO:-$HOME/claude-setting}"
REMOTE="git@github.com:chelseachen007/claude-setting.git"

DO_COMMIT=0
MSG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --commit) DO_COMMIT=1; shift ;;
    -m) MSG="${2:-}"; shift 2 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

[ -d "$SRC" ] || { echo "源目录不存在: $SRC"; exit 1; }

# 首次运行自动 clone
if [ ! -d "$REPO/.git" ]; then
  echo "→ 首次运行，克隆仓库到 $REPO"
  gh repo clone chelseachen007/claude-setting "$REPO" -- --quiet
fi

echo "→ 同步 $SRC → $REPO"
rsync -a --delete \
  --exclude '.git' \
  --exclude '.gitignore' \
  --exclude '.backup' \
  --exclude 'logs' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.venv' \
  --exclude 'node_modules' \
  --exclude '.DS_Store' \
  --exclude '.coverage' \
  --exclude '.pytest_cache' \
  --exclude '.system' \
  "$SRC/" "$REPO/"

cd "$REPO"

# README 描述的是档案本身，用仓库里那份（~/ai/README.md 描述的是运行目录，语义不同）
git checkout HEAD -- README.md 2>/dev/null || true

# 同步脚本自己也要进档案
cp "$SRC/scripts/archive-ai.sh" "$REPO/scripts/archive-ai.sh" 2>/dev/null || true

if [ -z "$(git status --porcelain)" ]; then
  echo "✓ 无变化，档案已是最新"
  exit 0
fi

echo
echo "=== 变化 ==="
git status --short
echo
git diff --stat HEAD | tail -1

if [ "$DO_COMMIT" -eq 0 ]; then
  echo
  echo "未提交。确认无误后加 --commit 重跑，或手动 git add/commit/push。"
  exit 0
fi

TYPE="chore"
[ -n "$MSG" ] || MSG="同步 ~/ai 最新状态（$(date +%Y-%m-%d)）"

git add -A
git commit -q -m "$TYPE: $MSG"
git push origin main

echo
echo "✓ 已推送 $(git log --oneline -1)"
