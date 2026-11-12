#!/bin/bash
# 数据湖体检速查：一条命令看清「服务在不在 / 调度器活不活 / 数据到哪天 / 欠什么账」。
#
#   bash 工具/数据湖/lake_health.sh
#
# 只读，不改任何数据。退出码 0=健康，1=有需要处理的问题。
set -uo pipefail
PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT" || exit 2

PY="$PROJECT/.venv/bin/python3"
CONFIG="$PROJECT/配置/cnequity.toml"
UID_NUM=$(id -u)
PROBLEMS=0

hr() { printf '%s\n' "------------------------------------------------------------"; }

hr
echo "① 数据湖服务（cne-wb serve）"
launchctl print "gui/$UID_NUM/com.cnequity.lake-serve" 2>/dev/null \
  | grep -E '^\s+(state|pid) =' | sed 's/^ */   /'
code=$(curl -s -o /dev/null -m 8 --noproxy '*' -w '%{http_code}' "http://127.0.0.1:8787/")
echo "   端口 8787 HTTP $code"
[ "$code" = "200" ] || { echo "   ✗ 服务没响应，先看 data/cnequity/logs/serve.err.log"; PROBLEMS=1; }

hr
echo "② 每日调度器（com.cnequity.web.<hash>）"
LABEL=$(ls "$HOME/Library/LaunchAgents" 2>/dev/null | grep -E '^com\.cnequity\.web\..*\.plist$' | sed 's/\.plist$//' | head -1)
if [ -z "$LABEL" ]; then
  echo "   ✗ 没装调度器：看板 http://localhost:8787 → 运维 → 定时任务 里打开「每日更新」"
  PROBLEMS=1
else
  echo "   $LABEL"
  launchctl print "gui/$UID_NUM/$LABEL" 2>/dev/null \
    | grep -E '^\s+(state|runs|last exit code) =' | sed 's/^ */   /'
  LAST_TICK="/Users/chenjie/Data/cnequity/cnequity/meta/state/web_scheduler/last_tick.json"
  if [ -f "$LAST_TICK" ]; then
    "$PY" - "$LAST_TICK" <<'EOF'
import json, sys
from datetime import datetime, timezone
d = json.load(open(sys.argv[1]))
at = datetime.fromisoformat(d["at"])
mins = (datetime.now(timezone.utc) - at).total_seconds() / 60
print(f"   上次心跳 {at.astimezone():%Y-%m-%d %H:%M:%S}（{mins:.0f} 分钟前） status={d.get('status')} jobs={d.get('jobs')}")
if mins > 10:
    print("   ✗ 心跳超过 10 分钟没动，调度器可能卡住了")
EOF
  else
    echo "   ✗ 从没跑过心跳，检查 ~/Library/LaunchAgents/$LABEL.plist 是否已 bootstrap"
    PROBLEMS=1
  fi
fi

hr
echo "③ 数据到哪天"
"$PY" - "$PROJECT" <<'EOF'
import json, sys
from datetime import date
from pathlib import Path
root = Path(sys.argv[1])
part = sorted(p.name.split("=", 1)[1] for p in (Path("/Users/chenjie/Data/cnequity/cnequity/curated/daily_bars")).glob("trade_date=*"))
latest = part[-1] if part else None
state = Path("/Users/chenjie/Data/cnequity/cnequity/meta/state/daily_bars.json")
s = json.loads(state.read_text()) if state.exists() else {}
print(f"   daily_bars 最新 {latest}（共 {len(part)} 天）")
print(f"   coverage_status={s.get('coverage_status')} complete_through={s.get('complete_through')} observed_max={s.get('observed_max')}")
out = s.get("outstanding_keys") or []
print(f"   欠账 {len(out)} 条")
for k in out[:5]:
    print(f"     - {k.get('symbol')} {k.get('trade_date')} {k.get('reason')} retryable={k.get('retryable')}")
today = date.today()
if latest and latest < today.isoformat() and today.weekday() < 5:
    print(f"   ! 今天是工作日但行情只到 {latest}，15:05 后跑 工具/数据湖/lake_watchdog.py 会算一次真实差距")
EOF

hr
echo "④ 看门狗（com.user.lake-watchdog，工作日 15:10）"
launchctl print "gui/$UID_NUM/com.user.lake-watchdog" 2>/dev/null \
  | grep -E '^\s+(state|runs|last exit code) =' | sed 's/^ */   /' \
  || { echo "   ✗ 没装，bash scripts/lake-watchdog.sh 手动跑一次可以；要自动告警得 bootstrap plist"; PROBLEMS=1; }
echo "   最近一次判定："
tail -n 20 "$PROJECT/logs/lake-watchdog.log" 2>/dev/null | grep -E '"result"|"latest_bar_date"|"lag_sessions"' | tail -3 | sed 's/^/     /'

hr
[ "$PROBLEMS" = "0" ] && echo "结论：没发现需要处理的问题。" || echo "结论：上面标 ✗ 的地方需要处理。"
exit "$PROBLEMS"
