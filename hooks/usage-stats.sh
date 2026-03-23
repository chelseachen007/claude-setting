#!/usr/bin/env bash
# PreToolUse hook for usage statistics
# Logs tool usage to track skill effectiveness

set -euo pipefail

# Data directory for logs
DATA_DIR="${HOME}/.claude/data"
LOG_FILE="${DATA_DIR}/usage-stats.jsonl"
SKILL_LOG="${DATA_DIR}/skill-usage.jsonl"

# Ensure data directory exists
mkdir -p "$DATA_DIR"

# Read tool input from stdin
INPUT=$(cat)

# Parse input
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log general tool usage
log_tool_usage() {
  local tool="$1"
  local details="$2"

  jq -n \
    --arg timestamp "$TIMESTAMP" \
    --arg session "$SESSION_ID" \
    --arg tool "$tool" \
    --arg details "$details" \
    '{timestamp: $timestamp, session: $session, tool: $tool, details: $details}' \
    >> "$LOG_FILE"
}

# Log skill usage specifically
log_skill_usage() {
  local skill_name="$1"

  jq -n \
    --arg timestamp "$TIMESTAMP" \
    --arg session "$SESSION_ID" \
    --arg skill "$skill_name" \
    '{timestamp: $timestamp, session: $session, skill: $skill}' \
    >> "$SKILL_LOG"
}

# Track different tool types
case "$TOOL_NAME" in
  "Skill")
    SKILL_NAME=$(echo "$INPUT" | jq -r '.tool_input.skill // empty')
    if [[ -n "$SKILL_NAME" ]]; then
      log_skill_usage "$SKILL_NAME"
    fi
    ;;
  "Bash")
    COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' | cut -c1-100)
    log_tool_usage "Bash" "$COMMAND"
    ;;
  "Agent")
    AGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty')
    log_tool_usage "Agent" "$AGENT_TYPE"
    ;;
  *)
    log_tool_usage "$TOOL_NAME" ""
    ;;
esac

# Always proceed - this hook only logs
echo '{"proceed": true}'
exit 0
