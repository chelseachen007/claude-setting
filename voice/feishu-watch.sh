#!/bin/bash
# 飞书语音闪念常驻监听
#
# 两条腿：
#   1) 事件模式：lark-cli event consume 常驻，来一条处理一条（低延迟）
#   2) 历史兜底：每 15 分钟跑一次 --from-history，补事件模式漏掉/断线期间的消息
#
# 坑（实测）：
#   - lark-cli 把 stdin EOF 当退出信号，后台跑必须喂一个永不结束的 stdin
#   - macOS 没有 timeout 命令
#   - event consume 只在 websocket 在线时收事件，不补推历史 → 所以必须有兜底

set -uo pipefail

VOICE_DIR="$HOME/ai/voice"
LARK="$HOME/.npm-global/bin/lark-cli"
PY_ASR="/opt/homebrew/bin/python3"
SCRIPT="$VOICE_DIR/voiceflash.py"
LOG="$VOICE_DIR/logs/watch.log"
TMP="$VOICE_DIR/tmp"
BACKFILL_SEC=900   # 历史兜底间隔

mkdir -p "$VOICE_DIR/logs" "$TMP"

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"; }

# 日志超过 2MB 滚一次
if [ -f "$LOG" ] && [ "$(stat -f%z "$LOG" 2>/dev/null || echo 0)" -gt 2097152 ]; then
  mv "$LOG" "$LOG.1"
fi

log "=== watch 启动 (pid $$) ==="

# ---------- 历史兜底：后台循环 ----------
(
  while true; do
    sleep "$BACKFILL_SEC"
    "$PY_ASR" "$SCRIPT" --from-history >> "$LOG" 2>&1 || log "backfill 失败"
  done
) &
BACKFILL_PID=$!
log "backfill 循环启动 (pid $BACKFILL_PID, 每 ${BACKFILL_SEC}s)"

cleanup() {
  log "=== watch 退出，停 backfill ==="
  kill "$BACKFILL_PID" 2>/dev/null
  exit 0
}
trap cleanup INT TERM

# ---------- 事件模式：主循环，断线自动重连 ----------
while true; do
  EVT="$TMP/evt-$$.json"
  rm -f "$EVT"

  # tail -f /dev/null 保证 stdin 永不 EOF
  "$LARK" event consume im.message.receive_v1 \
      --max-events 1 --timeout 600s > "$EVT" 2>"$TMP/evt-err-$$.log" < <(tail -f /dev/null)

  if [ -s "$EVT" ]; then
    if grep -q '"audio"' "$EVT"; then
      log "事件到达，处理中"
      "$PY_ASR" "$SCRIPT" --event-file "$EVT" >> "$LOG" 2>&1 || log "处理事件失败"
    fi
    rm -f "$EVT"
  else
    # 超时是正常现象（600s 内没人说话），不是错误
    if [ -s "$TMP/evt-err-$$.log" ] && grep -qi "error\|fail" "$TMP/evt-err-$$.log"; then
      log "consume 报错: $(head -c 300 "$TMP/evt-err-$$.log")"
      sleep 10
    fi
  fi
  sleep 2
done
