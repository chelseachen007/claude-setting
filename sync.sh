#!/usr/bin/env bash
# ~/ai/sync.sh — 跨平台 AI 资产一致性体检与修复
#
# 用法：
#   ~/ai/sync.sh          体检，报告问题
#   ~/ai/sync.sh --fix    自动修复被替换成实体文件的软链（会先备份实体文件）
#
# 检查三类软链：规则 / 记忆 / 项目技能
set -uo pipefail

AI="$HOME/ai"
FIX=0
[ "${1:-}" = "--fix" ] && FIX=1

# 记忆合并文件（~/.agents/AGENTS.md 的源）随记忆源文件一起刷新
[ -x "$AI/scripts/build-memory-agents.sh" ] && "$AI/scripts/build-memory-agents.sh" >/dev/null

ok=0; bad=0; warn=0
declare -a issues=()

# 期望的软链：<链接路径>|<目标路径>|<标签>
LINKS=(
  "$HOME/.codex/AGENTS.md|$AI/rules/global.md|规则·Codex"
  "$HOME/.dsh/AGENTS.md|$AI/rules/global.md|规则·dsh"
  "$HOME/.workbuddy-ai/user-99d85571-55d9-4729-92a4-d3d5a36edab4-personal/MEMORY.md|$AI/memory/MEMORY.md|记忆·长期"
  "$HOME/.workbuddy-ai/user-99d85571-55d9-4729-92a4-d3d5a36edab4-personal/USER.md|$AI/memory/USER.md|记忆·用户画像"
  "$HOME/.workbuddy-ai/user-99d85571-55d9-4729-92a4-d3d5a36edab4-personal/SOUL.md|$AI/memory/SOUL.md|记忆·人格"
  "$HOME/.workbuddy-ai/user-99d85571-55d9-4729-92a4-d3d5a36edab4-personal/IDENTITY.md|$AI/memory/IDENTITY.md|记忆·身份"
  "$HOME/.agents/AGENTS.md|$AI/memory/AGENTS.md|记忆·合并(dsh)"
)

echo "AI 资产体检 · $(date '+%Y-%m-%d %H:%M')"
echo "─────────────────────────────────────"

for item in "${LINKS[@]}"; do
  IFS='|' read -r link target label <<< "$item"
  if [ -L "$link" ] && [ -e "$link" ]; then
    actual=$(readlink "$link")
    # 目标存在性校验在下面的 actual 比对里做，这里不能用 -e 当唯一判据
    if [ "$actual" = "$target" ]; then
      printf '  ✓ %-16s → %s\n' "$label" "${target/#$HOME/~}"
      ok=$((ok+1))
    else
      printf '  ⚠ %-16s 指向别处：%s\n' "$label" "$actual"
      issues+=("$label|$link|$target|错误指向")
      warn=$((warn+1))
    fi
  elif [ -f "$link" ] && [ ! -L "$link" ]; then
    printf '  ✗ %-16s 被替换成实体文件（App 覆盖了软链）\n' "$label"
    issues+=("$label|$link|$target|实体文件")
    bad=$((bad+1))
  else
    printf '  ✗ %-16s 不存在\n' "$label"
    issues+=("$label|$link|$target|缺失")
    bad=$((bad+1))
  fi
done

# 项目技能完整性（真实目录 .agents/skills，每个技能必须有 SKILL.md）
PROJECTS=(
  "$HOME/Documents/study/github/Obsidian"
)
for proj in "${PROJECTS[@]}"; do
  [ -d "$proj/.agents/skills" ] || continue
  echo
  echo "项目技能 · ${proj/#$HOME/~}"
  total=0; broken=0; noskill=0
  while IFS= read -r p; do
    name=$(basename "$p")
    total=$((total+1))
    if [ ! -e "$p" ]; then
      printf '  ✗ 断链：%s\n' "$name"
      issues+=("技能|$p|$(readlink "$p")|断链")
      broken=$((broken+1)); bad=$((bad+1))
    elif [ -d "$p" ] && [ ! -f "$p/SKILL.md" ]; then
      printf '  ⚠ 缺 SKILL.md：%s\n' "$name"
      noskill=$((noskill+1)); warn=$((warn+1))
    fi
  done < <(find "$proj/.agents/skills" -maxdepth 1 -mindepth 1 \( -type d -o -type l \) ! -name "__pycache__" ! -name ".claude-plugin")
  if [ "$broken" -eq 0 ] && [ "$noskill" -eq 0 ]; then
    printf '  ✓ %d 个技能全部有效\n' "$total"
    ok=$((ok+1))
  fi
done

echo
echo "─────────────────────────────────────"

# 全局技能：全部收口到 ~/ai/skills（唯一源），明细交给 sync-skill-sources.sh
echo
if [ -x "$AI/scripts/sync-skill-sources.sh" ]; then
  skill_out=$("$AI/scripts/sync-skill-sources.sh" 2>&1)
  echo "$skill_out" | sed -n '/─────/,$p'
  if echo "$skill_out" | grep -qE '  ✗ '; then
    bad=$((bad+1)); issues+=("技能源|$AI/skills|$AI/skills|未收口")
  fi
  if echo "$skill_out" | grep -qE '  ⚠ '; then
    warn=$((warn+1))
  fi
else
  printf '  ✗ 缺 ~/ai/scripts/sync-skill-sources.sh\n'
  bad=$((bad+1))
fi

# dsh CLI 是否还在 PATH 上（指向 App 内置 CLI，App 升级后路径可能变）
DSH_BIN="$HOME/.npm-global/bin/dsh"
if [ -x "$DSH_BIN" ]; then
  printf '  ✓ dsh CLI → %s\n' "$(readlink "$DSH_BIN" 2>/dev/null || echo "$DSH_BIN")"
else
  printf '  ✗ dsh CLI 不在 PATH（%s）\n' "${DSH_BIN/#$HOME/~}"
  bad=$((bad+1))
fi

echo "─────────────────────────────────────"
printf '结果：%d 正常 / %d 警告 / %d 错误\n' "$ok" "$warn" "$bad"

if [ "$bad" -eq 0 ] && [ "$warn" -eq 0 ]; then
  echo "一切正常，各平台共用同一份规则与记忆。"
  exit 0
fi

if [ "$FIX" -eq 0 ]; then
  echo
  echo "加 --fix 自动修复（实体文件会先备份到 ~/ai/.backup/rescue/）"
  exit 1
fi

echo
echo "开始修复…"
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$AI/.backup/rescue"
for item in "${issues[@]}"; do
  IFS='|' read -r label link target reason <<< "$item"
  [ -d "$(dirname "$link")" ] || mkdir -p "$(dirname "$link")"
  if [ -f "$link" ] && [ ! -L "$link" ]; then
    cp "$link" "$AI/.backup/rescue/$(basename "$link").$STAMP"
    rm "$link"
  elif [ -L "$link" ]; then
    rm "$link"
  fi
  ln -s "$target" "$link" && printf '  修复 %s\n' "$label"
done
echo "修复完成。备份在 ~/ai/.backup/rescue/"
