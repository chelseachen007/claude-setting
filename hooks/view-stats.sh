#!/usr/bin/env bash
# View usage statistics

set -euo pipefail

DATA_DIR="${HOME}/.claude/data"
SKILL_LOG="${DATA_DIR}/skill-usage.jsonl"
TOOL_LOG="${DATA_DIR}/usage-stats.jsonl"

echo "📊 Claude Code 使用统计"
echo "========================"
echo

# Skill usage stats
if [[ -f "$SKILL_LOG" ]]; then
  echo "🎯 Skill 使用排行 (Top 10):"
  echo "---------------------------"
  jq -r '.skill' "$SKILL_LOG" 2>/dev/null | sort | uniq -c | sort -rn | head -10 | while read count skill; do
    printf "  %-30s %4d 次\n" "$skill" "$count"
  done
  echo
  echo "📈 总计: $(wc -l < "$SKILL_LOG" | tr -d ' ') 次 skill 调用"
else
  echo "⚠️ 暂无 skill 使用记录"
fi

echo
echo "------------------------"

# Tool usage stats
if [[ -f "$TOOL_LOG" ]]; then
  echo
  echo "🔧 工具使用统计:"
  echo "----------------"
  jq -r '.tool' "$TOOL_LOG" 2>/dev/null | sort | uniq -c | sort -rn | head -10 | while read count tool; do
    printf "  %-20s %4d 次\n" "$tool" "$count"
  done
  echo
  echo "📈 总计: $(wc -l < "$TOOL_LOG" | tr -d ' ') 次工具调用"
else
  echo "⚠️ 暂无工具使用记录"
fi

echo
echo "========================"
echo "数据目录: $DATA_DIR"
