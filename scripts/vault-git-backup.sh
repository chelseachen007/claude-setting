#!/usr/bin/env bash
# vault-git-backup.sh — 把本地仓库自动提交并推送到 GitHub
#
# 用法:
#   bash ~/ai/scripts/vault-git-backup.sh            # 提交 + 推送有变化的仓库
#   bash ~/ai/scripts/vault-git-backup.sh --dry-run  # 只看会发生什么
#   bash ~/ai/scripts/vault-git-backup.sh --only Obsidian
#
# 由 LaunchAgent com.user.vault-git-backup 每天定时调用。
# 设计要点:
#   - 绝不 force push，绝不 rebase，绝不丢历史
#   - 推送前先 pull --rebase，冲突就跳过该仓库并报警，不瞎合并
#   - 有锁，避免上一轮没跑完下一轮又起
#   - 每个仓库独立成败，一个仓库失败不影响其他

set -uo pipefail

LOG_DIR="$HOME/ai/logs"
LOG_FILE="$LOG_DIR/vault-git-backup.log"
LOCK_DIR="$HOME/.cache/vault-git-backup"
LOCK_FILE="$LOCK_DIR/backup.lock"
MAX_LOG_BYTES=$((2 * 1024 * 1024))   # 日志超过 2MB 就滚动一份

DRY_RUN=0
ONLY=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --only) ONLY="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

mkdir -p "$LOG_DIR" "$LOCK_DIR"

# 日志滚动
if [ -f "$LOG_FILE" ] && [ "$(stat -f%z "$LOG_FILE" 2>/dev/null || echo 0)" -gt "$MAX_LOG_BYTES" ]; then
  mv "$LOG_FILE" "$LOG_FILE.1"
fi

log() {
  local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
  echo "$msg" >> "$LOG_FILE"
  [ "$DRY_RUN" -eq 1 ] && echo "$msg"
}

# 单实例锁（macOS 没有 flock，用 mkdir 原子性）
if ! mkdir "$LOCK_FILE" 2>/dev/null; then
  # 锁超过 2 小时视为僵尸锁
  if [ -d "$LOCK_FILE" ] && [ $(( $(date +%s) - $(stat -f%m "$LOCK_FILE") )) -gt 7200 ]; then
    log "发现僵尸锁，强制清理"
    rmdir "$LOCK_FILE" 2>/dev/null && mkdir "$LOCK_FILE" 2>/dev/null || { log "锁仍不可用，退出"; exit 0; }
  else
    log "上一轮还在跑，跳过"
    exit 0
  fi
fi
trap 'rmdir "$LOCK_FILE" 2>/dev/null' EXIT

# 仓库清单: 名称|路径|是否走 archive-ai
REPOS=(
  "Obsidian|$HOME/Documents/study/github/Obsidian|plain"
  "ai-assets|$HOME/ai|archive"
  "ObPublish|$HOME/Documents/study/github/ObPublish|plain"
  "youtube|$HOME/Documents/study/github/youtube|plain"
  "ai-image-automation|$HOME/Documents/study/github/ai-image-automation|plain"
  "micro-web|$HOME/Documents/study/github/micro-web|plain"
)

ok=0; changed=0; skipped=0; failed=0; failed_names=""

log "──────── 开始 vault-git-backup ────────"

for entry in "${REPOS[@]}"; do
  IFS='|' read -r name path mode <<< "$entry"

  [ -n "$ONLY" ] && [ "$ONLY" != "$name" ] && continue

  if [ ! -d "$path" ]; then
    log "SKIP  $name — 目录不存在 ($path)"
    skipped=$((skipped + 1)); continue
  fi

  # ai 资产走专门的档案脚本（rsync 到 claude-setting 再推）
  if [ "$mode" = "archive" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then
      log "DRY   $name — 会调用 archive-ai.sh --commit"
      continue
    fi
    if out=$(bash "$HOME/ai/scripts/archive-ai.sh" --commit 2>&1); then
      if echo "$out" | grep -q "无变化"; then
        log "OK    $name — 无变化"
        ok=$((ok + 1))
      else
        log "OK    $name — 已同步并推送 $(echo "$out" | grep '已推送' | tail -1)"
        ok=$((ok + 1)); changed=$((changed + 1))
      fi
    else
      log "FAIL  $name — $(echo "$out" | tail -3 | tr '\n' ' ')"
      failed=$((failed + 1)); failed_names="$failed_names $name"
    fi
    continue
  fi

  if [ ! -d "$path/.git" ]; then
    log "SKIP  $name — 不是 git 仓库"
    skipped=$((skipped + 1)); continue
  fi

  # submodule 指针变动不算内容变化：Obsidian 库每天都在提交，会让所有引用它的
  # superproject 每天都显示改动。除非显式开 UPDATE_SUBMODULES=1，否则忽略。
  if [ "${UPDATE_SUBMODULES:-0}" = "1" ]; then
    dirty=$(git -C "$path" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  else
    dirty=$(git -C "$path" status --porcelain --ignore-submodules=all 2>/dev/null | wc -l | tr -d ' ')
  fi
  unpushed=$(git -C "$path" log --oneline '@{u}..HEAD' 2>/dev/null | wc -l | tr -d ' ')

  if [ "$dirty" -eq 0 ] && [ "$unpushed" -eq 0 ]; then
    log "OK    $name — 无变化"
    ok=$((ok + 1)); continue
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    log "DRY   $name — 未提交 $dirty 项，未推送 $unpushed 个提交"
    changed=$((changed + 1)); continue
  fi

  # 1) 提交
  if [ "$dirty" -gt 0 ]; then
    msg="vault backup: $(date '+%Y-%m-%d %H:%M:%S')"
    # .gitignore 里可能被临时改过，用 -A 统一处理；--no-verify 跳过钩子避免卡住无人值守流程
    if ! git -C "$path" add -A --ignore-errors 2>>"$LOG_FILE"; then
      log "FAIL  $name — git add 失败"
      failed=$((failed + 1)); failed_names="$failed_names $name"; continue
    fi
    if ! git -C "$path" commit -q -m "$msg" --no-verify 2>>"$LOG_FILE"; then
      log "FAIL  $name — git commit 失败"
      failed=$((failed + 1)); failed_names="$failed_names $name"; continue
    fi
    log "COMMIT $name — $dirty 个文件"
    changed=$((changed + 1))
  fi

  # 2) 同步远端（先 rebase，冲突就放弃）
  branch=$(git -C "$path" rev-parse --abbrev-ref HEAD 2>/dev/null)
  if git -C "$path" rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
    if ! git -C "$path" pull --rebase --autostash -q 2>>"$LOG_FILE"; then
      log "FAIL  $name — pull --rebase 失败（可能有冲突），已中止 rebase 并跳过推送"
      git -C "$path" rebase --abort 2>/dev/null
      failed=$((failed + 1)); failed_names="$failed_names $name"; continue
    fi
  fi

  # 3) 推送
  if git -C "$path" push -q origin "$branch" 2>>"$LOG_FILE"; then
    log "PUSH  $name — 已推送到 origin/$branch"
    ok=$((ok + 1))
  else
    log "FAIL  $name — git push 失败（查上面的错误行）"
    failed=$((failed + 1)); failed_names="$failed_names $name"
  fi
done

log "──────── 结束：成功 $ok / 有变更 $changed / 跳过 $skipped / 失败 $failed ────────"

if [ "$failed" -gt 0 ]; then
  log "失败仓库:$failed_names"
  # 失败时弹一条系统通知（无人值守也需要知道）
  osascript -e "display notification \"$failed 个仓库备份失败:$failed_names\" with title \"Vault 备份\"" 2>/dev/null || true
  exit 1
fi

exit 0
