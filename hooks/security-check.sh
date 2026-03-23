#!/usr/bin/env bash
# PreToolUse hook for security checks
# Blocks dangerous commands and warns user

set -euo pipefail

# Read tool input from stdin
INPUT=$(cat)

# Parse tool name and command
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input // empty')

# Only check Bash commands
if [[ "$TOOL_NAME" != "Bash" ]]; then
  echo '{"proceed": true}'
  exit 0
fi

# Extract the command
COMMAND=$(echo "$TOOL_INPUT" | jq -r '.command // empty')

# Dangerous patterns list
DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf /*"
  "rm -rf \*"
  "rm -rf ."
  "rm -rf \.\."
  ":(){ :|:& };:"
  "mkfs"
  "dd if="
  "> /dev/sd"
  "chmod -R 777 /"
  "chown -R .* /"
  "curl.*|.*bash"
  "wget.*|.*bash"
  "curl.*|.*sh"
  "wget.*|.*sh"
)

# Check each pattern
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    # Block and warn
    cat <<EOF
{
  "proceed": false,
  "reason": "Blocked dangerous command pattern: $pattern",
  "message": {
    "role": "user",
    "content": "🚫 安全检查：此命令被阻止执行。如果确实需要执行，请手动运行或使用 --dangerously-disable-sandbox。"
  }
}
EOF
    exit 0
  fi
done

# Check for force push to main/master
if echo "$COMMAND" | grep -qE "git push.*--force.*(main|master)" && ! echo "$COMMAND" | grep -q "force-with-lease"; then
  cat <<EOF
{
  "proceed": false,
  "reason": "Blocked force push to main/master",
  "message": {
    "role": "user",
    "content": "⚠️ 安全检查：禁止 force push 到 main/master 分支。如需强制推送，请使用 --force-with-lease。"
  }
}
EOF
  exit 0
fi

# Allow the command
echo '{"proceed": true}'
exit 0
