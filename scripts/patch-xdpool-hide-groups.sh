#!/usr/bin/env bash
# ~/ai/scripts/patch-xdpool-hide-groups.sh
#
# 把 dsh-xdpool 模型选择器里两组从下拉里摘掉，幂等可重打。
#
# 摘掉的两组：
#   [xdpool-hide-free]   XD Pool · 免费模型   (provider id: xdpool-free)
#   [xdpool-hide-buddy]  CodeBuddy (腾讯)     (provider id: buddy)
#
# 为什么必须用脚本：改的是 node_modules 里的插件源码，
# `dsh plugin add/update` 升级 xdpool 会整包覆盖，补丁随即丢失，
# 升级后跑一次本脚本即可恢复。
#
# 用法：
#   patch-xdpool-hide-groups.sh             打补丁（已打过则跳过）
#   patch-xdpool-hide-groups.sh --check     只体检，不改任何文件
#   patch-xdpool-hide-groups.sh --revert    从最近备份还原
#
# 退出码：0 正常 / 1 前置检查失败 / 2 补丁失败并已回滚
set -uo pipefail

PROFILE="${XDPOOL_PROFILE:-$HOME/.dsh/profiles/web}"
PLUGIN="$PROFILE/node_modules/dsh-xdpool"
IDX="$PLUGIN/lib/index.js"
PACK="$PLUGIN/vendor/channel-pack/pack.js"

MODE="apply"
case "${1:-}" in
  --check)  MODE="check" ;;
  --revert) MODE="revert" ;;
  "")       ;;
  -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) echo "未知参数：$1（可用 --check / --revert / --help）" >&2; exit 1 ;;
esac

say()   { printf '%s\n' "$*"; }
head1() { printf '\n%s\n%s\n' "$*" "─────────────────────────────────────"; }

# 0. 前置检查：插件在位、python3 / node 可用
if [ ! -f "$IDX" ] || [ ! -f "$PACK" ]; then
  say "✗ 找不到 dsh-xdpool 插件文件："
  [ -f "$IDX" ]  || say "   缺失 $IDX"
  [ -f "$PACK" ] || say "   缺失 $PACK"
  say "  确认 profile 路径，或用 XDPOOL_PROFILE=<path> 指定。"
  exit 1
fi

command -v python3 >/dev/null 2>&1 || { say "✗ PATH 里没有 python3。"; exit 1; }
command -v node    >/dev/null 2>&1 || { say "✗ PATH 里没有 node，无法做语法校验。"; exit 1; }

has_mark()   { grep -qF "$1" "$2"; }
latest_bak() { ls -1t "$1".bak-* 2>/dev/null | head -1; }

apply_one() {
  local mark="$1" file="$2" label="$3" script="$4"

  if has_mark "$mark" "$file"; then
    printf '  ✓ %-20s 已打过，跳过\n' "$label"
    return 0
  fi

  if [ "$MODE" = "check" ]; then
    printf '  ✗ %-20s 未打（跑本脚本不带参数即可修复）\n' "$label"
    return 3
  fi

  local bak
  bak="$(printf '%s.bak-%s' "$file" "$(date +%Y%m%d-%H%M%S)")"
  cp -p "$file" "$bak" || { printf '  ✗ %-20s 备份失败\n' "$label"; return 2; }

  if ! PATCH_TARGET="$file" python3 -c "$script"; then
    printf '  ✗ %-20s 打补丁失败，已回滚\n' "$label"
    cp -p "$bak" "$file"
    return 2
  fi

  if ! node --check "$file" 2>/dev/null; then
    printf '  ✗ %-20s 语法校验失败，已回滚\n' "$label"
    printf '     这个插件版本可能变了，补丁锚点需要更新\n'
    cp -p "$bak" "$file"
    return 2
  fi

  printf '  ✓ %-20s 已打（备份 %s）\n' "$label" "$(basename "$bak")"
  return 0
}

# ── 补丁 1：免费分组（lib/index.js 三处）─────────────────────────────
read -r -d '' FREE_PY <<'PY'
import os, sys
path = os.environ["PATCH_TARGET"]
s = open(path, encoding="utf-8").read()

# 1) 不再注册 free adapter
old = ('\t\t\t\treleaseAdapterAggregate = ctx.llm.registerAdapter([XDPOOL_AGGREGATE_PROVIDER], adaptersByRegion.aggregate.adapter);\n'
       '\t\t\t\treleaseAdapterFree = ctx.llm.registerAdapter([XDPOOL_FREE_PROVIDER], adaptersByRegion.free.adapter);\n')
new = ('\t\t\t\treleaseAdapterAggregate = ctx.llm.registerAdapter([XDPOOL_AGGREGATE_PROVIDER], adaptersByRegion.aggregate.adapter);\n'
       '\t\t\t\t// [xdpool-hide-free] free lane disabled on user request\n')
if s.count(old) != 1: sys.exit("anchor1 registerAdapter: %d hits" % s.count(old))
s = s.replace(old, new)

# 2) 从 configurable-provider 目录里摘掉 free 条目，并给 aggregate 收尾逗号
old2 = ('\t\t\t\t\t{\n'
        '\t\t\t\t\t\tprovider: XDPOOL_FREE_PROVIDER,\n'
        '\t\t\t\t\t\tdisplayName: EXTRA_LANE_NAMES.free,\n'
        '\t\t\t\t\t\tsettingsNs: XDPOOL_SETTINGS_NS,\n'
        '\t\t\t\t\t\tsettingsPath: [],\n'
        '\t\t\t\t\t\tdeclared: false\n'
        '\t\t\t\t\t}\n')
if s.count(old2) != 1: sys.exit("anchor2 free entry: %d hits" % s.count(old2))
s = s.replace(old2, '')

# 3) 模型发现接口对 free 直接返回空
old3 = '\t\t\t\tif (request.provider === "xdpool-free") return freeCatalog.current().map((row) => ({'
new3 = ('\t\t\t\t// [xdpool-hide-free] free lane unregistered; answer nothing even if asked\n'
        '\t\t\t\tif (request.provider === "xdpool-free") return [];\n'
        '\t\t\t\tif (request.provider === "__xdpool_free_unused") return freeCatalog.current().map((row) => ({')
if s.count(old3) != 1: sys.exit("anchor4 model discovery: %d hits" % s.count(old3))
s = s.replace(old3, new3)

open(path, "w", encoding="utf-8").write(s)
print("ok")
PY

# ── 补丁 2：CodeBuddy (腾讯)（pack.js 一处）──────────────────────────
read -r -d '' BUDDY_PY <<'PY'
import os, sys
path = os.environ["PATCH_TARGET"]
s = open(path, encoding="utf-8").read()

old = '''function registerBuddyLlm(ctx, options) {
  const product = options.product ?? CODEBUDDY;
  const adapter = new BuddyAdapter(options);
  registerAdapterIdempotent(ctx.llm, [product.id], adapter);
  return adapter;
}'''
new = '''function registerBuddyLlm(ctx, options) {
  const product = options.product ?? CODEBUDDY;
  const adapter = new BuddyAdapter(options);
  // [xdpool-hide-buddy] CodeBuddy lane is intentionally NOT registered with
  // ctx.llm, so the model picker no longer shows its group. The adapter object
  // is still built and returned: modelAdapters.buddy and the 'buddy' channel
  // service keep working (login, credits, gateway).
  if (product.id !== "buddy") registerAdapterIdempotent(ctx.llm, [product.id], adapter);
  return adapter;
}'''
if s.count(old) != 1: sys.exit("anchor registerBuddyLlm: %d hits" % s.count(old))
s = s.replace(old, new)

open(path, "w", encoding="utf-8").write(s)
print("ok")
PY

# ── 体检 / 还原 ─────────────────────────────────────────────────
if [ "$MODE" = "revert" ]; then
  head1 "回滚补丁 · $(date '+%Y-%m-%d %H:%M')"
  for f in "$IDX" "$PACK"; do
    b="$(latest_bak "$f")"
    if [ -z "$b" ]; then
      printf '  · %-20s 没有备份可还原\n' "$(basename "$f")"
      continue
    fi
    if cp -p "$b" "$f" && node --check "$f" 2>/dev/null; then
      printf '  ✓ %-20s 已还原自 %s\n' "$(basename "$f")" "$(basename "$b")"
    else
      printf '  ✗ %-20s 还原失败\n' "$(basename "$f")"
    fi
  done
  say ""
  say "重启 web 服务生效："
  say "  launchctl kickstart -k gui/\$(id -u)/com.user.dsh-web"
  exit 0
fi

head1 "dsh-xdpool 分组隐藏补丁 · $(date '+%Y-%m-%d %H:%M')"
say "插件：$PLUGIN"

rc=0
apply_one "[xdpool-hide-free]"  "$IDX"  "免费模型分组"    "$FREE_PY"  || rc=$?
apply_one "[xdpool-hide-buddy]" "$PACK" "CodeBuddy 分组"  "$BUDDY_PY" || rc=$?

if [ "$MODE" = "check" ]; then
  say ""
  if [ "$rc" -ne 0 ]; then say "有补丁未打。修：$0"; else say "两个补丁都在位。"; fi
  exit "$rc"
fi

if [ "$rc" -ne 0 ]; then
  say ""
  say "✗ 有补丁未能应用（对应文件已回滚）。"
  say "  插件升级后锚点通常变了，需要按新版源码更新本脚本里的匹配串。"
  exit 2
fi

say ""
say "✓ 完成。重启 web 服务生效："
say "  launchctl kickstart -k gui/\$(id -u)/com.user.dsh-web"
say "  然后刷新页面，模型选择器里这两组即消失。"
