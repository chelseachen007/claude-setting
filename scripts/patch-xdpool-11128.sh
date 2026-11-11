#!/usr/bin/env bash
# 给 dsh-xdpool 插件补第 3 条 11128 内容指纹改写规则。
#
# 背景（2026-10-28 实测，WorkBuddy 国内版 copilot.tencent.com）：
# 上游除已有的两条指纹外，新增了一条**句子对**指纹：
#   "Tokens prefixed with @ are paths the user explicitly referenced."
#   + 单个空格 +
#   "Relative paths resolve from the workspace root; ..."
# 两句必须都是完整句子、且只用单个空格连接才触发；换成 \n 即可通过。
# 命中后整个请求 400 / code 11128 "Illegal API invocation from an unapproved channel"。
#
# 插件升级会覆盖 lib/index.js，升级后重跑本脚本即可。
# 用法： bash ~/ai/scripts/patch-xdpool-11128.sh [--check]
set -euo pipefail

F="${XDPOOL_INDEX:-$HOME/.dsh/profiles/web/node_modules/dsh-xdpool/lib/index.js}"
ANCHOR='[/You are Claude Code, Anthropic'"'"'s official CLI for Claude\\.?/gi, "You are a coding agent."]]);'
# 上面是"改之前"的锚点（npm 原版），改成带第 3 条规则的版本
PATCHED='[/You are Claude Code, Anthropic'"'"'s official CLI for Claude\\.?/gi, "You are a coding agent."], [/referenced\\. Relative paths resolve/gi, "referenced.\\nRelative paths resolve"]]);'

[ -f "$F" ] || { echo "找不到插件文件: $F" >&2; exit 1; }

if grep -q 'referenced\\. Relative paths resolve' "$F" 2>/dev/null; then
  echo "已打过补丁：$F"
  exit 0
fi

if [ "${1:-}" = "--check" ]; then
  echo "未打补丁：$F"
  exit 1
fi

cp "$F" "$F.bak-$(date +%Y%m%d-%H%M%S)"

python3 - "$F" <<'PY'
import sys, re
p = sys.argv[1]
s = open(p, encoding="utf8").read()
needle = "/You are Claude Code, Anthropic's official CLI for Claude"
i = s.find(needle)
if i < 0:
    # 没有 Claude 那条时，挂在 Web GUI 那条后面
    needle = "[/DeepSeek Harness Web GUI/gi, \"DeepSeek Harness web interface\"]"
    i = s.find(needle)
    if i < 0:
        sys.exit("锚点未找到，插件结构可能已变，请手工处理")
    end = i + len(needle)
    s = s[:end] + ', [/referenced\\. Relative paths resolve/gi, "referenced.\\nRelative paths resolve"]' + s[end:]
else:
    j = s.find("]]);", i)
    if j < 0:
        sys.exit("锚点未找到闭合位置，插件结构可能已变")
    s = s[:j] + ', [/referenced\\. Relative paths resolve/gi, "referenced.\\nRelative paths resolve"]' + s[j:]
open(p, "w", encoding="utf8").write(s)
print("已写入", p)
PY

node --check "$F" && echo "语法检查通过"
echo "重启 dsh web 生效： launchctl kickstart -k gui/\$(id -u)/com.user.dsh-web"
