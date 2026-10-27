#!/usr/bin/env bash
# ~/ai/scripts/sync-skill-sources.sh
#
# 技能单一源收口：确保所有平台的技能入口都指向 ~/ai/skills。
#
# 唯一源：  ~/ai/skills/            （每个 skill 一个真实目录，内含 SKILL.md）
# 入口软链：~/.agents/skills        → dsh / Codex 共用的 Agent Skills 根
#           ~/.dsh/skills           → dsh 的第二个全局技能根
#           ~/.codex/skills         → Codex
#           ~/.workbuddy-ai/skills  → WorkBuddy（App 托管，这里只做核对不做接管）
#
# 用法：
#   sync-skill-sources.sh          体检，列出差异
#   sync-skill-sources.sh --apply  对被 App 覆盖成实体目录的入口做备份+接管
#
# 注意：搬移一律用 mv（rename），不复制——技能目录里带 scripts/、assets/、
# references/，复制会产生两份不一致的副本，并且白白多占空间。
set -uo pipefail

AI="$HOME/ai"
SRC="$AI/skills"
APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

# 入口 | 标签
ENTRIES=(
  "$HOME/.agents/skills|dsh+Codex 共用"
  "$HOME/.dsh/skills|dsh 全局根"
  "$HOME/.codex/skills|Codex"
)

ok=0; bad=0; warn=0

echo "技能单一源体检 · $(date '+%Y-%m-%d %H:%M')"
echo "─────────────────────────────────────"

if [ ! -d "$SRC" ]; then
  echo "  ✗ 唯一源不存在：$SRC"
  exit 1
fi
src_n=$(find "$SRC" -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' ')
printf '  ✓ 唯一源 %-20s %s 个技能\n' "${SRC/#$HOME/~}" "$src_n"
ok=$((ok+1))

for item in "${ENTRIES[@]}"; do
  IFS='|' read -r entry label <<< "$item"
  if [ -L "$entry" ]; then
    actual=$(readlink "$entry")
    if [ "$actual" = "$SRC" ]; then
      printf '  ✓ %-18s → %s\n' "$label" "${actual/#$HOME/~}"
      ok=$((ok+1))
    else
      printf '  ⚠ %-18s 指向别处：%s\n' "$label" "${actual/#$HOME/~}"
      warn=$((warn+1))
    fi
  elif [ -d "$entry" ]; then
    n=$(find "$entry" -maxdepth 1 -mindepth 1 | wc -l | tr -d ' ')
    printf '  ✗ %-18s 是实体目录（%s 项），未指向唯一源\n' "$label" "$n"
    bad=$((bad+1))
    if [ "$APPLY" -eq 1 ]; then
      stamp=$(date +%Y%m%d-%H%M%S)
      mkdir -p "$AI/.backup/skills-rescue"
      mv "$entry" "$AI/.backup/skills-rescue/$(basename "$(dirname "$entry")")-skills.$stamp"
      mkdir -p "$(dirname "$entry")"
      ln -s "$SRC" "$entry" && printf '    已接管 → %s\n' "${SRC/#$HOME/~}"
    fi
  else
    printf '  ✗ %-18s 不存在\n' "$label"
    bad=$((bad+1))
    if [ "$APPLY" -eq 1 ]; then
      mkdir -p "$(dirname "$entry")"
      ln -s "$SRC" "$entry" && printf '    已创建 → %s\n' "${SRC/#$HOME/~}"
    fi
  fi
done

# WorkBuddy 的目录是 App 托管的，不能是软链；只核对技能是否都在唯一源里有镜像
WB="$HOME/.workbuddy-ai/skills"
if [ -d "$WB" ] && [ ! -L "$WB" ]; then
  missing=()
  while IFS= read -r d; do
    n=$(basename "$d")
    case "$n" in _*|.*) continue ;; esac
    [ -n "$(ls -A "$d" 2>/dev/null)" ] || continue   # 空目录不算技能
    [ -e "$SRC/$n" ] || missing+=("$n")
  done < <(find "$WB" -maxdepth 1 -mindepth 1 -type d)
  if [ "${#missing[@]}" -gt 0 ]; then
    printf '  ⚠ WorkBuddy 有 %d 个技能未进唯一源：%s\n' "${#missing[@]}" "${missing[*]:0:8}"
    warn=$((warn+1))
  else
    printf '  ✓ %-18s 技能已全部镜像到唯一源\n' "WorkBuddy"
    ok=$((ok+1))
  fi
fi

# 唯一源里每个技能必须有 SKILL.md
noskill=$(find "$SRC" -maxdepth 1 -mindepth 1 -type d ! -name '.system' ! -exec test -f '{}/SKILL.md' \; -print | wc -l | tr -d ' ')
if [ "$noskill" -gt 0 ]; then
  printf '  ⚠ 唯一源中 %s 个目录缺 SKILL.md\n' "$noskill"
  warn=$((warn+1))
fi

echo "─────────────────────────────────────"
printf '结果：%d 正常 / %d 警告 / %d 错误\n' "$ok" "$warn" "$bad"
[ "$bad" -eq 0 ] && [ "$warn" -eq 0 ] && exit 0
[ "$APPLY" -eq 0 ] && echo "加 --apply 接管被 App 覆盖成实体目录的入口"
exit 1
