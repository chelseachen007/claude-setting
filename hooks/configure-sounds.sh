#!/usr/bin/env bash
# Configure notification sounds

CONFIG_FILE="${HOME}/.claude/data/sound-config.json"

# Available sounds
SOUNDS=(
  "Basso"
  "Blow"
  "Bottle"
  "Frog"
  "Funk"
  "Glass"
  "Hero"
  "Morse"
  "Ping"
  "Pop"
  "Purr"
  "Sosumi"
  "Submarine"
  "Tink"
)

play_sound() {
  local sound="$1"
  local file="/System/Library/Sounds/${sound}.aiff"
  if [[ -f "$file" ]]; then
    afplay "$file"
  fi
}

show_menu() {
  echo "🎵 Claude Code 提示音配置"
  echo "=========================="
  echo
  echo "当前配置:"
  if [[ -f "$CONFIG_FILE" ]]; then
    cat "$CONFIG_FILE" | jq .
  else
    echo "  任务完成: Glass"
    echo "  需要确认: Ping"
  fi
  echo
  echo "选项:"
  echo "  1) 设置任务完成音"
  echo "  2) 设置需要确认音"
  echo "  3) 试听所有声音"
  echo "  4) 测试当前配置"
  echo "  5) 恢复默认"
  echo "  q) 退出"
  echo
}

select_sound() {
  local purpose="$1"
  echo
  echo "选择 ${purpose} 的声音:"
  echo "-------------------"
  for i in "${!SOUNDS[@]}"; do
    printf "  %2d) %s\n" $((i+1)) "${SOUNDS[$i]}"
  done
  echo "  0) 静音"
  echo
  read -p "请选择 [1-${#SOUNDS[@]}]: " choice

  if [[ "$choice" == "0" ]]; then
    SELECTED_SOUND=""
  elif [[ "$choice" -ge 1 && "$choice" -le ${#SOUNDS[@]} ]]; then
    SELECTED_SOUND="${SOUNDS[$((choice-1))]}"
    echo
    echo "试听 ${SELECTED_SOUND}..."
    play_sound "$SELECTED_SOUND"
  else
    echo "无效选择"
    return 1
  fi
  return 0
}

save_config() {
  local type="$1"
  local sound="$2"

  mkdir -p "$(dirname "$CONFIG_FILE")"

  if [[ ! -f "$CONFIG_FILE" ]]; then
    echo '{"completion": "Glass", "confirmation": "Ping"}' > "$CONFIG_FILE"
  fi

  local tmp=$(mktemp)
  if [[ "$type" == "completion" ]]; then
    jq --arg sound "$sound" '.completion = $sound' "$CONFIG_FILE" > "$tmp"
  else
    jq --arg sound "$sound" '.confirmation = $sound' "$CONFIG_FILE" > "$tmp"
  fi
  mv "$tmp" "$CONFIG_FILE"

  echo "✅ 已保存"
  update_hooks
}

update_hooks() {
  local completion=$(jq -r '.completion // "Glass"' "$CONFIG_FILE" 2>/dev/null || echo "Glass")
  local confirmation=$(jq -r '.confirmation // "Ping"' "$CONFIG_FILE" 2>/dev/null || echo "Ping")

  # Update notification hook
  sed -i '' "s/SOUND_NAME=\".*\"/SOUND_NAME=\"${completion}\"/" \
    "${HOME}/.claude/hooks/notification-sound.sh" 2>/dev/null || true

  # Update stop hook
  sed -i '' "s/SOUND_NAME=\".*\"/SOUND_NAME=\"${confirmation}\"/" \
    "${HOME}/.claude/hooks/stop-sound.sh" 2>/dev/null || true
}

preview_all() {
  echo
  echo "🔊 试听所有声音..."
  echo "-------------------"
  for sound in "${SOUNDS[@]}"; do
    echo "  ${sound}..."
    play_sound "$sound"
    sleep 0.3
  done
}

test_current() {
  local completion=$(jq -r '.completion // "Glass"' "$CONFIG_FILE" 2>/dev/null || echo "Glass")
  local confirmation=$(jq -r '.confirmation // "Ping"' "$CONFIG_FILE" 2>/dev/null || echo "Ping")

  echo
  echo "🔊 测试任务完成音 (${completion})..."
  play_sound "$completion"
  sleep 1
  echo "🔊 测试确认提示音 (${confirmation})..."
  play_sound "$confirmation"
}

restore_defaults() {
  rm -f "$CONFIG_FILE"
  update_hooks
  echo "✅ 已恢复默认设置 (Glass / Ping)"
}

# Main loop
while true; do
  show_menu
  read -p "请选择: " action
  echo

  case "$action" in
    1)
      select_sound "任务完成"
      [[ $? -eq 0 ]] && save_config "completion" "$SELECTED_SOUND"
      ;;
    2)
      select_sound "需要确认"
      [[ $? -eq 0 ]] && save_config "confirmation" "$SELECTED_SOUND"
      ;;
    3)
      preview_all
      ;;
    4)
      test_current
      ;;
    5)
      restore_defaults
      ;;
    q|Q)
      echo "👋 再见!"
      exit 0
      ;;
    *)
      echo "无效选择"
      ;;
  esac
  echo
  read -p "按回车继续..."
done
