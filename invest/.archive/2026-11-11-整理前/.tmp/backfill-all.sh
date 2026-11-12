#!/bin/bash
# 按依赖与成本顺序回填空数据集。每步独立计时、独立记日志，失败不阻断后续。
set -u
cd "/Users/chenjie/WorkBuddy AI/投资" || exit 1
export CODEBUDDY_SAFE_DELETE_ENABLED=0
CNE="./.venv/bin/python3 ./.venv/bin/cne-wb"
LOG=".tmp/backfill-all.log"
: > "$LOG"

# 依赖在前：行业分类→行业指数；公告→监管事件；新闻/公告→情绪得分
LIST=(
  index_constituents
  industry_members
  sector_bars
  share_unlock_schedule
  valuation_metrics
  margin_trading
  northbound_flows
  northbound_holdings
  macro_indicators
  market_breadth
  announcement_index
  earnings_disclosure_schedule
  block_trades
  dragon_tiger
  institutional_holdings
  share_structure
  shareholder_counts
  financial_statement_items
  top_holders
)

for ds in "${LIST[@]}"; do
  start=$(date +%s)
  echo "[$(date +%H:%M:%S)] >>> START $ds" >> "$LOG"
  $CNE backfill "$ds" --config configs/cnequity.toml >> "$LOG" 2>&1
  rc=$?
  dur=$(( $(date +%s) - start ))
  echo "[$(date +%H:%M:%S)] <<< END   $ds  rc=$rc  ${dur}s" >> "$LOG"
done

# 派生集：需要上游已落地
for step in "derive industry_index" "derive regulatory_events" "derive sentiment_scores"; do
  set -- $step
  echo "[$(date +%H:%M:%S)] >>> START $1 $2" >> "$LOG"
  $CNE "$1" "$2" --config configs/cnequity.toml >> "$LOG" 2>&1
  echo "[$(date +%H:%M:%S)] <<< END   $1 $2  rc=$?" >> "$LOG"
done

# 快照型：只能取当下，取一次就有一天的数据
for ds in fund_flow sector_fund_flow hot_rank news_headlines analyst_consensus sector_members; do
  echo "[$(date +%H:%M:%S)] >>> START $ds (snapshot)" >> "$LOG"
  $CNE backfill "$ds" --config configs/cnequity.toml >> "$LOG" 2>&1
  echo "[$(date +%H:%M:%S)] <<< END   $ds  rc=$?" >> "$LOG"
done

echo "[$(date +%H:%M:%S)] ==== ALL DONE ====" >> "$LOG"
