#!/usr/bin/env bash
# ~/ai/scripts/chat-archive.sh — 会话归档：把 Codex / WorkBuddy 的历史会话增量汇进 dsh
#
# 定位：dsh 是「会话归档层」，Codex / WorkBuddy 是「工作现场」。
# 只做单向汇聚（→ dsh），不试图反向同步——那两家没有导入 API。
#
# 用法：
#   chat-archive.sh              预览：只列出会导入哪些会话，不写任何东西（默认）
#   chat-archive.sh --apply      真导入（幂等：已导入跳过、源增长续写）
#   chat-archive.sh --json       JSON 输出，供定时任务 / 外部脚本消费
#   chat-archive.sh --source codex|workbuddy   只处理单一来源
#
# 退出码：0 = 正常（无论有没有待导入）；1 = 依赖缺失或扫描/导入失败
#
# 定时任务：见 ~/Library/LaunchAgents/com.user.dsh-chat-archive.plist（默认不启动）
set -uo pipefail

DSH_BIN="$HOME/.npm-global/bin/dsh"
IMPORT_PKG="$HOME/.dsh/profiles/web/node_modules/dsh-chat-import/bin/dsh-chat-import.mjs"
STATE_DIR="$HOME/.dsh"
LOG_DIR="$HOME/ai/logs"
TODAY=$(date +%F)
LOG="$LOG_DIR/chat-archive-$TODAY.log"

APPLY=0
JSON=0
SOURCE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --json)  JSON=1 ;;
    --source) SOURCE="${2:-}"; shift ;;
    -h|--help) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "未知参数：$1" >&2; exit 2 ;;
  esac
  shift
done

mkdir -p "$LOG_DIR"
log() { printf '%s %s\n' "$(date '+%H:%M:%S')" "$*" >> "$LOG"; }

# ── 依赖检查：缺什么就说缺什么，并给出修复动作 ─────────────────
fail() {
  echo "✗ $1" >&2
  [ -n "${2:-}" ] && echo "  → $2" >&2
  log "FAIL: $1"
  exit 1
}
[ -x "$DSH_BIN" ]      || fail "dsh CLI 不存在：$DSH_BIN" "确认 DeepSeek Harness 已安装，或改 DSH_BIN"
[ -f "$IMPORT_PKG" ]   || fail "导入插件 CLI 不存在：$IMPORT_PKG" "在 web profile 装 dsh-chat-import 后重试"
[ -f "$HOME/.dsh/dsh-chat-import/imports.json" ] || fail "导入注册表不存在，说明还没导入过任何会话" "先在 dsh 里跑一次 /import-all"

# ── 选来源 ────────────────────────────────────────────────
SOURCES=()
if [ -n "$SOURCE" ]; then
  SOURCES=("$SOURCE")
else
  SOURCES=(codex workbuddy)
fi

for s in "${SOURCES[@]}"; do
  case "$s" in
    codex|workbuddy) ;;
    *) fail "不支持的来源：$s" "可选：codex / workbuddy" ;;
  esac
done

# ── 只读预览 ──────────────────────────────────────────────
before=$(md5 -q "$HOME/.dsh/dsh-chat-import/imports.json" 2>/dev/null || echo none)

all_json='{'
total_pending=0
total_dangling=0
for s in "${SOURCES[@]}"; do
  out=$(node "$IMPORT_PKG" scan "$s" --json 2>/dev/null)
  rc=$?
  if [ $rc -ne 0 ] || [ -z "$out" ]; then
    fail "扫描 $s 失败（退出码 $rc）" "单独跑：node $IMPORT_PKG scan $s"
  fi
  read -r n d <<< "$(printf '%s' "$out" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(len(d.get('pending',[])), len(d.get('dangling',[])))
" 2>/dev/null || echo '0 0')"
  total_pending=$((total_pending + n))
  total_dangling=$((total_dangling + d))
  all_json="$all_json\"$s\":$out,"

  if [ "$JSON" -eq 0 ]; then
    printf '%s' "$out" | python3 -c "
import json,sys
d=json.load(sys.stdin)
fmt=d.get('format','?')
pend=d.get('pending',[])
dang=d.get('dangling',[])
skip=d.get('skipped',0)
arch=d.get('archived',0)
if not pend and not dang:
    print('  %-10s %d 个会话，全部已归档' % (fmt, d.get('scanned',0)))
else:
    print('  %-10s 扫描 %d ｜ 待导入 %d ｜ 已跳过 %d ｜ 悬空 %d'
          % (fmt, d.get('scanned',0), len(pend), skip+arch, len(dang)))
    for p in pend[:10]:
        print('    ├─ %s' % (p.get('title') or p.get('sourcePath','')))
    if len(pend)>10: print('    │  …另有 %d 个' % (len(pend)-10))
    for p in dang[:6]:
        print('    ⚠ 悬空: %s' % (p.get('title') or p.get('sourcePath','')))
    if len(dang)>6: print('    ⚠  …另有 %d 个悬空' % (len(dang)-6))
" 2>/dev/null || echo "  $s: 解析失败"
  fi
done
all_json="${all_json%,}}"

# ── 只读保证 ──────────────────────────────────────────────
after=$(md5 -q "$HOME/.dsh/dsh-chat-import/imports.json" 2>/dev/null || echo none)
if [ "$APPLY" -eq 0 ] && [ "$before" != "$after" ]; then
  fail "预览阶段改动了注册表，这不该发生" "检查 dsh-chat-import 的 scan 子命令是否真的只读"
fi

log "scan sources=${SOURCES[*]} pending=$total_pending apply=$APPLY"

# ── 真导入 ────────────────────────────────────────────────
if [ "$APPLY" -eq 1 ]; then
  if [ "$total_pending" -eq 0 ]; then
    echo "没有待导入的会话，跳过。"
    [ "$JSON" -eq 1 ] && echo "$all_json"
    exit 0
  fi
  echo "开始导入…"
  for s in "${SOURCES[@]}"; do
    echo "── $s ──"
    "$DSH_BIN" --profile headless "/import-all $s" 2>&1 | grep -vE '^\[' | tail -15
    rc=${PIPESTATUS[0]}
    [ $rc -ne 0 ] && fail "导入 $s 失败（退出码 $rc）" "看 $LOG 与 dsh 输出"
  done
  echo "完成。"
fi

if [ "$JSON" -eq 1 ]; then
  echo "$all_json"
elif [ "$APPLY" -eq 0 ]; then
  echo
  if [ "$total_pending" -eq 0 ] && [ "$total_dangling" -eq 0 ]; then
    echo "全部已归档，无事可做。"
  else
    [ "$total_pending" -gt 0 ]  && echo "预览模式，未写入任何东西。加 --apply 导入 $total_pending 个新会话。"
    [ "$total_dangling" -gt 0 ] && echo "悬空 $total_dangling 个：注册表有记录但磁盘无会话目录，需 /import-all <source> <path> --force 重导补回。"
  fi
fi
exit 0
