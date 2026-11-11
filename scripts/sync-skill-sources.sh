#!/usr/bin/env bash
# ~/ai/scripts/sync-skill-sources.sh
#
# 技能单一源收口：确保所有平台的技能入口都指向 ~/ai/skills。
#
# 唯一源：  ~/ai/skills/            （每个 skill 一个真实目录，内含 SKILL.md）
# 入口软链：~/.agents/skills        → dsh / Codex 共用的 Agent Skills 根
#           ~/.dsh/skills           → dsh 的第二个全局技能根
#           ~/.codex/skills         → Codex
#           ~/.workbuddy*/skills    → WorkBuddy（App 托管的实体根，内部逐技能软链）
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
src_n=$(find "$SRC" -maxdepth 1 -mindepth 1 -type d ! -name '.*' | wc -l | tr -d ' ')
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

# WorkBuddy 的技能根是 App 托管的实体目录，不能整体软链——App 会往里写迁移文件，
# 整体软链会把写的动作穿透进 ~/ai。所以改为逐技能软链：目录里每个技能
# 都应该是一条指向 $SRC/<同名> 的软链。
for WB in "$HOME"/.workbuddy*/skills; do
  [ -d "$WB" ] || continue
  tag=$(basename "$(dirname "$WB")" | sed 's/^\.//')
  label="WB($tag)"
  link_n=0
  real=(); broken=(); missing=()

  while IFS= read -r entry; do
    n=$(basename "$entry")
    case "$n" in _*|.*) continue ;; esac
    if [ -L "$entry" ]; then
      if [ ! -e "$entry" ]; then
        broken+=("$n")
      elif [ "$(readlink "$entry")" = "$SRC/$n" ]; then
        link_n=$((link_n+1))
      fi
    elif [ -d "$entry" ]; then
      [ -n "$(ls -A "$entry" 2>/dev/null)" ] && real+=("$n")   # 空目录不算技能
    fi
  done < <(find "$WB" -maxdepth 1 -mindepth 1 \( -type d -o -type l \))

  # 唯一源里有、WorkBuddy 入口里没有的（.system 等内部目录不参与）
  while IFS= read -r d; do
    n=$(basename "$d")
    { [ -e "$WB/$n" ] || [ -L "$WB/$n" ]; } || missing+=("$n")
  done < <(find "$SRC" -maxdepth 1 -mindepth 1 -type d ! -name '.*')

  if [ "${#real[@]}" -gt 0 ]; then
    printf '  ✗ %-18s %d 个实体副本未指向唯一源：%s\n' "$label" "${#real[@]}" "${real[*]:0:5}"
    bad=$((bad+1))
    if [ "$APPLY" -eq 1 ]; then
      stamp=$(date +%Y%m%d-%H%M%S)
      mkdir -p "$AI/.backup/skills-rescue"
      for n in "${real[@]}"; do
        mv "$WB/$n" "$AI/.backup/skills-rescue/$n.$stamp" 2>/dev/null &&
          ln -s "$SRC/$n" "$WB/$n" && printf '    转软链 %s\n' "$n"
      done
    fi
  fi

  if [ "${#broken[@]}" -gt 0 ]; then
    printf '  ✗ %-18s %d 条断链：%s\n' "$label" "${#broken[@]}" "${broken[*]:0:5}"
    bad=$((bad+1))
    if [ "$APPLY" -eq 1 ]; then
      for n in "${broken[@]}"; do
        rm "$WB/$n"
        [ -e "$SRC/$n" ] && ln -s "$SRC/$n" "$WB/$n" && printf '    重建 %s\n' "$n"
      done
    fi
  fi

  if [ "${#missing[@]}" -gt 0 ]; then
    printf '  ⚠ %-18s %d 个技能未接入：%s\n' "$label" "${#missing[@]}" "${missing[*]:0:5}"
    warn=$((warn+1))
    if [ "$APPLY" -eq 1 ]; then
      for n in "${missing[@]}"; do
        ln -s "$SRC/$n" "$WB/$n" && printf '    接入 %s\n' "$n"
      done
    fi
  fi

  if [ "${#real[@]}" -eq 0 ] && [ "${#broken[@]}" -eq 0 ] && [ "${#missing[@]}" -eq 0 ]; then
    printf '  ✓ %-18s %d 个技能全部软链到唯一源\n' "$label" "$link_n"
    ok=$((ok+1))
  fi
done

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
