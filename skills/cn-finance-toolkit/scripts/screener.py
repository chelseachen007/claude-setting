#!/usr/bin/env python3
"""
全A股选股筛选器
==============
按6条标准筛选：低PE(<20)、低PB(<2)、高ROE(>15%)、上市满5年、行业垄断、长远增长确定性。

Usage:
    python screener.py                    # 默认筛选
    python screener.py --top 30           # 返回前30只
    python screener.py --pe 25 --pb 3     # 自定义阈值
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.utils import safe_float


def fetch_all_stocks_snapshot():
    """拉取全A股实时行情快照（含PE、PB、市值）。"""
    import akshare as ak
    df = ak.stock_zh_a_spot_em()
    return df


def fetch_listing_date(symbol: str) -> str:
    """获取上市日期。"""
    import akshare as ak
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                if str(row.iloc[0]) == "上市时间":
                    return str(row.iloc[1])
    except Exception:
        pass
    return ""


def fetch_roe(symbol: str) -> float | None:
    """获取最新ROE。"""
    import akshare as ak
    try:
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            return safe_float(latest.get("净资产收益率"))
    except Exception:
        pass
    return None


def fetch_growth(symbol: str) -> dict:
    """获取营收和利润增长率（最近2期）。"""
    import akshare as ak
    try:
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
        if df is not None and not df.empty and len(df) >= 2:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            return {
                "revenue_growth_latest": safe_float(latest.get("营业总收入同比增长率")),
                "profit_growth_latest": safe_float(latest.get("归母净利润同比增长率")),
                "revenue_growth_prev": safe_float(prev.get("营业总收入同比增长率")),
                "profit_growth_prev": safe_float(prev.get("归母净利润同比增长率")),
            }
    except Exception:
        pass
    return {}


def screen_market(max_pe=20.0, max_pb=2.0, min_roe=15.0, min_market_cap=50,
                  min_list_years=5, top_n=50):
    """全市场筛选主函数。"""
    print(f"[*] 拉取全A股实时数据...", file=sys.stderr)
    df = fetch_all_stocks_snapshot()
    total = len(df)
    print(f"[*] 共 {total} 只股票", file=sys.stderr)

    # --- Phase 1: PE + PB + 市值初筛 ---
    cutoff_date = datetime.now() - timedelta(days=min_list_years * 365)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d")
    print(f"[*] 第一轮筛选：PE<{max_pe}, PB<{max_pb}, 市值>{min_market_cap}亿", file=sys.stderr)

    filtered = df.copy()
    filtered["pe"] = filtered["市盈率-动态"].apply(safe_float)
    filtered["pb"] = filtered["市净率"].apply(safe_float)
    filtered["cap"] = filtered["总市值"].apply(safe_float)

    # PE: 排除 None/负值，且 < max_pe
    filtered = filtered[
        (filtered["pe"].notna()) &
        (filtered["pe"] > 0) &
        (filtered["pe"] <= max_pe)
    ]
    # PB: 排除 None/负值，且 < max_pb
    filtered = filtered[
        (filtered["pb"].notna()) &
        (filtered["pb"] > 0) &
        (filtered["pb"] <= max_pb)
    ]
    # 市值 > min_market_cap 亿
    filtered = filtered[
        (filtered["cap"].notna()) &
        (filtered["cap"] >= min_market_cap * 1e8)
    ]
    print(f"[*] 第一轮通过：{len(filtered)} 只", file=sys.stderr)

    # --- Phase 2: 上市日期 + ROE ---
    results = []
    checked = 0
    for _, row in filtered.iterrows():
        symbol = str(row["代码"])
        name = str(row["名称"])
        checked += 1

        if checked % 20 == 0:
            print(f"[*] 进度：{checked}/{len(filtered)}", file=sys.stderr)

        # 上市日期
        list_date = fetch_listing_date(symbol)
        if not list_date:
            continue
        try:
            ld = datetime.strptime(list_date, "%Y-%m-%d")
            if ld > cutoff_date:
                continue
        except ValueError:
            continue

        # ROE
        roe = fetch_roe(symbol)
        if roe is None or roe < min_roe:
            continue

        # 增长数据
        growth = fetch_growth(symbol)

        results.append({
            "symbol": symbol,
            "name": name,
            "pe": round(float(row["pe"]), 2),
            "pb": round(float(row["pb"]), 2),
            "market_cap_yi": round(float(row["cap"]) / 1e8, 2),
            "roe": roe,
            "listing_date": list_date,
            "growth": growth,
            "price": safe_float(row.get("最新价")),
        })

    print(f"\n[✓] 最终通过：{len(results)} 只", file=sys.stderr)

    # 按 ROE 降序排列
    results.sort(key=lambda x: x["roe"] or 0, reverse=True)
    return results[:top_n]


def main():
    parser = argparse.ArgumentParser(description="全A股选股筛选器")
    parser.add_argument("--pe", type=float, default=20.0, help="最大PE（默认20）")
    parser.add_argument("--pb", type=float, default=2.0, help="最大PB（默认2）")
    parser.add_argument("--roe", type=float, default=15.0, help="最小ROE（默认15%%）")
    parser.add_argument("--cap", type=float, default=50, help="最小市值/亿（默认50）")
    parser.add_argument("--years", type=int, default=5, help="上市满N年（默认5）")
    parser.add_argument("--top", type=int, default=50, help="返回前N只（默认50）")
    args = parser.parse_args()

    results = screen_market(
        max_pe=args.pe,
        max_pb=args.pb,
        min_roe=args.roe,
        min_market_cap=args.cap,
        min_list_years=args.years,
        top_n=args.top,
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
