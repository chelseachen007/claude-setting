#!/usr/bin/env bash
# Notification hook - plays sound when task completes
# Triggers when Claude sends a notification

set -euo pipefail

# Config file
CONFIG_FILE="${HOME}/.claude/data/sound-config.json"

# Default sound
DEFAULT_SOUND="Glass"

# Get sound from config or use default
if [[ -f "$CONFIG_FILE" ]]; then
  SOUND_NAME=$(jq -r '.completion // "'"$DEFAULT_SOUND"'"' "$CONFIG_FILE" 2>/dev/null || echo "$DEFAULT_SOUND")
else
  SOUND_NAME="$DEFAULT_SOUND"
fi

# If sound is empty (muted), exit silently
if [[ -z "$SOUND_NAME" ]]; then
  cat
  exit 0
fi

SOUND_FILE="/System/Library/Sounds/${SOUND_NAME}.aiff"

# Play completion sound (async to not block)
if [[ -f "$SOUND_FILE" ]]; then
  afplay "$SOUND_FILE" &
fi

# Pass through any notification data
cat
exit 0
