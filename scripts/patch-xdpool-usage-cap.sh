#!/usr/bin/env bash
# 取消 dsh-xdpool 数据看板「最近 2000 次调用」的截断。
#
# 背景：插件把 USAGE_MAX_SAMPLES 硬编码成 2e3，record() 里超了就 shift() 丢最旧的样本，
# 所以总调用数一到 2000，KPI 和「最近调用」就停止增长。插件升级会覆盖 node_modules，
# 这个补丁必须重跑（跟 patch-xdpool-11128.sh 一样）。
#
# 改动（幂等）：
#   1. USAGE_MAX_SAMPLES 2e3 -> 2e4   —— 内存仍封顶，只是封顶高到日常到不了
#   2. entries 只回传最近 500 条       —— 面板只渲染 12 行，回传全量会让 /usage 响应膨胀
#
# 用法：bash ~/ai/scripts/patch-xdpool-usage-cap.sh [index.js 路径]
#      跑完要重启 DSH 才生效（node 模块进程内已缓存）。
set -euo pipefail

TARGET="${1:-$HOME/.dsh/profiles/web/node_modules/dsh-xdpool/lib/index.js}"
CAP_NEW="2e4"
ENTRIES_NEW="500"

[ -f "$TARGET" ] || { echo "找不到 $TARGET"; exit 1; }

python3 - "$TARGET" "$CAP_NEW" "$ENTRIES_NEW" <<'PY'
import shutil, sys, time, pathlib

path = pathlib.Path(sys.argv[1])
cap_new, entries_new = sys.argv[2], sys.argv[3]
src = path.read_text(encoding="utf-8")

cap_old = "const USAGE_MAX_SAMPLES = 2e3;"
cap_patched = f"const USAGE_MAX_SAMPLES = {cap_new};"
entries_old = "entries: this.samples.slice().reverse()"
entries_patched = f"entries: this.samples.slice(-{entries_new}).reverse()"

touched = []

if cap_old in src:
    if src.count(cap_old) != 1:
        sys.exit(f"USAGE_MAX_SAMPLES 出现 {src.count(cap_old)} 次，不敢动")
    src = src.replace(cap_old, cap_patched)
    touched.append(f"USAGE_MAX_SAMPLES 2e3 -> {cap_new}")
elif cap_patched in src:
    print(f"· USAGE_MAX_SAMPLES 已是 {cap_new}，跳过")
else:
    sys.exit("没找到 USAGE_MAX_SAMPLES = 2e3，插件版本可能又变了，先看代码")

if entries_old in src:
    if src.count(entries_old) != 1:
        sys.exit(f"entries 表达式出现 {src.count(entries_old)} 次，不敢动")
    src = src.replace(entries_old, entries_patched)
    touched.append(f"entries 回传最近 {entries_new} 条")
elif entries_patched in src:
    print(f"· entries 已是 slice(-{entries_new})，跳过")
else:
    sys.exit("没找到 entries: this.samples.slice().reverse()，插件版本可能又变了")

if not touched:
    print("已是打过补丁的状态，无需改动")
    raise SystemExit(0)

backup = path.with_name(f"{path.name}.bak-usagcap-{time.strftime('%Y%m%d-%H%M%S')}")
shutil.copy2(path, backup)
path.write_text(src, encoding="utf-8")

print("已打补丁：")
for line in touched:
    print(f"  - {line}")
print(f"备份：{backup}")
PY

node --check "$TARGET" && echo "语法检查通过"

if [ "$(uname)" = "Darwin" ]; then
  echo
  echo "⚠️  重启 DSH 后生效：quit 掉 DeepSeek Harness 再打开，或 launchctl kickstart -k gui/$(id -u)/com.user.dsh-web"
fi
