#!/usr/bin/env bash
# ~/ai/scripts/build-memory-agents.sh
#
# 把 ~/ai/memory/ 下的 USER / SOUL / MEMORY 拼成一份 AGENTS.md，
# 供只认单个 AGENTS.md 的 harness 使用（DeepSeek Harness 的第二个全局根
# ~/.agents/AGENTS.md 就软链到这里）。
#
# 处理规则：去掉源文件开头的 YAML frontmatter、去掉第一个一级标题，
# 统一挂到二级标题下面，避免同一份文件里出现多个 H1。
#
# 改完记忆文件后跑一次；~/ai/sync.sh 每次启动也会自动调用。
set -euo pipefail

AI="$HOME/ai"
OUT="$AI/memory/AGENTS.md"

emit() {
  local file="$1" title="$2"
  [ -f "$file" ] || return 0
  printf '\n## %s\n\n' "$title"
  awk '
    NR==1 && $0=="---" { fm=1; next }
    fm==1 && $0=="---" { fm=0; next }
    fm==1 { next }
    { print }
  ' "$file" \
  | awk '!h1 && /^# / { h1=1; next } { print }' \
  | awk '/^#/ { print "#" $0; next } { print }' \
  | awk 'seen || NF { seen=1; print }'
  printf '\n'
}

{
  printf '<!-- 自动生成，勿手改：~/ai/scripts/build-memory-agents.sh -->\n'
  printf '<!-- 源文件：~/ai/memory/{USER,SOUL,MEMORY}.md -->\n\n'
  printf '# 用户与长期记忆\n'
  emit "$AI/memory/USER.md"   "关于我（USER.md）"
  emit "$AI/memory/SOUL.md"   "人格与风格（SOUL.md）"
  emit "$AI/memory/MEMORY.md" "长期记忆（MEMORY.md）"
} > "$OUT.tmp"

mv "$OUT.tmp" "$OUT"
echo "已生成 ${OUT}（$(wc -c < "$OUT" | tr -d ' ') 字节）"
