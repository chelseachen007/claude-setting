#!/usr/bin/env bash
# chrome-cache-gc.sh — 清理 Chrome 长期未访问的 Service Worker 缓存
#
# 背景：飞书多维表格（内部代号 bitableHtml）的 Service Worker 会把每次打开
# 的 HTML 快照写进 CacheStorage，且从不回收。长期使用会累积到几十 GB。
# 实测 2026-10-22 清出 39GB，其中 37GB 来自 70+ 个 feishu.cn 租户站点。
#
# 策略：按 origin 目录的 mtime 判断最后访问时间，只清理超过 N 天未动的缓存。
# 活跃站点不受影响，因此 Chrome 运行中也可以安全执行。
#
# 用法：
#   ./chrome-cache-gc.sh              # 预览（默认 dry-run）
#   ./chrome-cache-gc.sh --force      # 实际清理，移入废纸篓
#   ./chrome-cache-gc.sh --days=7     # 自定义阈值，默认 30 天
#   ./chrome-cache-gc.sh --purge      # 清空废纸篓里本脚本产生的备份

set -uo pipefail

DAYS=30
FORCE=0
PURGE=0

for arg in "$@"; do
  case "$arg" in
    --force)      FORCE=1 ;;
    --dry-run)    FORCE=0 ;;
    --purge)      PURGE=1 ;;
    --days=*)     DAYS="${arg#*=}" ;;
    -h|--help)
      sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "未知参数: $arg（用 --help 查看用法）" >&2
      exit 1
      ;;
  esac
done

TRASH="$HOME/.Trash"

# ---- --purge：清理历史备份 ----
if [ "$PURGE" -eq 1 ]; then
  shopt -s nullglob
  targets=("$TRASH"/chrome-swcache-*)
  if [ ${#targets[@]} -eq 0 ]; then
    echo "废纸篓里没有本脚本产生的备份。"
    exit 0
  fi
  total_kb=0
  for t in "${targets[@]}"; do
    kb=$(du -sk "$t" 2>/dev/null | cut -f1)
    total_kb=$((total_kb + kb))
    rm -rf "$t" && echo "已永久删除: $(basename "$t")"
  done
  printf '释放空间: %.2f GB\n' "$(echo "$total_kb" | awk '{print $1/1048576}')"
  exit 0
fi

CHROME_ROOT="$HOME/Library/Application Support/Google/Chrome"

if [ ! -d "$CHROME_ROOT" ]; then
  echo "未找到 Chrome 配置目录: $CHROME_ROOT" >&2
  exit 1
fi

if pgrep -x "Google Chrome" >/dev/null 2>&1; then
  echo "提示: Chrome 正在运行（按 mtime 过滤，不会影响活跃站点）"
fi

echo "阈值: ${DAYS} 天未访问   模式: $([ "$FORCE" -eq 1 ] && echo '实际清理' || echo '预览')"
echo ""

total_kb=0
count=0
feishu_kb=0

shopt -s nullglob
for profile in "$CHROME_ROOT"/*/; do
  storage="${profile}Service Worker/CacheStorage"
  [ -d "$storage" ] || continue

  while IFS= read -r -d '' d; do
    kb=$(du -sk "$d" 2>/dev/null | cut -f1)
    [ -z "$kb" ] && continue
    [ "$kb" -lt 1024 ] && continue   # 小于 1MB 的忽略，避免噪音

    origin=$(strings "$d/index.txt" 2>/dev/null \
             | grep -oE 'https?://[a-zA-Z0-9.-]+' | head -1)
    [ -z "$origin" ] && origin="(未知来源)"

    size_mb=$((kb / 1024))
    printf '  %6s MB  %s\n' "$size_mb" "$origin"

    total_kb=$((total_kb + kb))
    count=$((count + 1))
    case "$origin" in
      *feishu.cn*|*larkoffice.com*) feishu_kb=$((feishu_kb + kb)) ;;
    esac

    if [ "$FORCE" -eq 1 ]; then
      ts=$(date +%Y%m%d-%H%M%S)
      mv "$d" "$TRASH/chrome-swcache-$ts-$(basename "$d")" 2>/dev/null
    fi
  done < <(find "$storage" -mindepth 1 -maxdepth 1 -type d -mtime +"$DAYS" -print0 2>/dev/null)
done

echo ""
if [ "$count" -eq 0 ]; then
  echo "没有超过 ${DAYS} 天未访问的缓存，无需清理。"
  exit 0
fi

printf '合计: %d 个站点缓存，%.2f GB\n' "$count" "$(echo "$total_kb" | awk '{print $1/1048576}')"
printf '其中飞书相关: %.2f GB\n' "$(echo "$feishu_kb" | awk '{print $1/1048576}')"

if [ "$FORCE" -eq 0 ]; then
  echo ""
  echo "这是预览。确认后加 --force 执行（会移入废纸篓，可回滚）。"
  echo "清空废纸篓才真正释放磁盘空间: $0 --purge"
else
  echo ""
  echo "已移入废纸篓。真正释放磁盘空间请执行: $0 --purge"
fi
