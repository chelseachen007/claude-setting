#!/bin/bash
# 数据湖看门狗：每日收盘后检查「今天的数据抓到了没」，没抓到就告警。
# 由 LaunchAgent com.user.lake-watchdog 每天 15:10 调起（15:05 之后任意一次巡检成立即可）。
set -uo pipefail
PROJECT="/Users/chenjie/ai/invest"
cd "$PROJECT" || exit 2

mkdir -p "$PROJECT/logs"
LOG="$PROJECT/logs/lake-watchdog.log"
PY="$PROJECT/.venv/bin/python3"

{
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') ====="
  "$PY" "$PROJECT/工具/数据湖/lake_watchdog.py" "$@"
  code=$?
  echo "[exit $code]"
} >>"$LOG" 2>&1

# 日志保留最近 500 行
if [ "$(wc -l <"$LOG")" -gt 500 ]; then
  tail -n 500 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

exit 0
