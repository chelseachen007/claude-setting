#!/usr/bin/env python3
"""
HK Stock Data Fetcher (港股数据获取)
=====================================
Fetch HK stock fundamentals, price history, financial metrics
using Sina Finance + Tencent Finance APIs (no API key required).

Usage:
    python hk_stock_data.py 00700                        # Basic info (Tencent)
    python hk_stock_data.py 00700 --history              # Price history (Sina)
    python hk_stock_data.py 00700 --financials           # Financial statements
    python hk_stock_data.py 00700 --valuation            # Valuation metrics
    python hk_stock_data.py 00700 --full                 # All data combined
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.utils import output_json, safe_float, error_exit

STOCK_NAMES = {
    "00700": "腾讯控股", "09988": "阿里巴巴-W", "03690": "美团-W",
    "01810": "小米集团-W", "01024": "快手-W", "00981": "中芯国际",
    "09999": "网易-S", "09888": "百度集团-SW", "09618": "京东集团-SW",
    "02015": "理想汽车-W", "09866": "蔚来-SW", "09868": "小鹏汽车-W",
    "00268": "金蝶国际", "00388": "香港交易所", "02382": "舜宇光学科技",
    "02899": "紫金矿业", "02018": "国泰君安国际",
}


def _curl_get(url: str, timeout: int = 15, referer: str = "") -> str:
    """Use curl to fetch URL, bypassing Python proxy issues."""
    cmd = ["curl", "-sS", "--connect-timeout", str(timeout), "-m", str(timeout + 5)]
    cmd += ["-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"]
    if referer:
        cmd += ["-H", f"Referer: {referer}"]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, timeout=timeout + 10)
    if result.returncode != 0:
        return ""
    for enc in ("utf-8", "gbk", "gb2312", "latin-1"):
        try:
            return result.stdout.decode(enc)
        except (UnicodeDecodeError, AttributeError):
            continue
    return result.stdout.decode("utf-8", errors="replace")


def fetch_basic_info(symbol: str) -> dict:
    """Fetch real-time quote from Tencent Finance API."""
    sym = _normalize(symbol)
    url = f"https://qt.gtimg.cn/q=r_hk{sym}"
    raw = _curl_get(url)
    if not raw:
        return {"error": f"No data for {sym}"}

    # Parse Tencent quote format: v_r_hk00700="field1~field2~..."
    match = re.search(r'"(.+)"', raw)
    if not match:
        return {"error": f"Parse error for {sym}"}

    fields = match.group(1).split("~")
    if len(fields) < 50:
        return {"error": f"Insufficient data fields for {sym}"}

    return {
        "symbol": sym,
        "name": STOCK_NAMES.get(sym, fields[1] if len(fields) > 1 else ""),
        "current_price": safe_float(fields[3]),
        "prev_close": safe_float(fields[4]),
        "open": safe_float(fields[5]),
        "volume": safe_float(fields[6]),
        "high": safe_float(fields[33]) if len(fields) > 33 else None,
        "low": safe_float(fields[34]) if len(fields) > 34 else None,
        "change_pct": safe_float(fields[32]) if len(fields) > 32 else None,
        "change": safe_float(fields[31]) if len(fields) > 31 else None,
        "turnover": safe_float(fields[37]) if len(fields) > 37 else None,
        "turnover_rate": safe_float(fields[43]) if len(fields) > 43 else None,
        "pe_dynamic": safe_float(fields[39]) if len(fields) > 39 else None,
        "pe_ttm": safe_float(fields[64]) if len(fields) > 64 else None,
        "pb": safe_float(fields[72]) if len(fields) > 72 else None,
        "dividend_yield": safe_float(fields[58]) if len(fields) > 58 else None,
        "market_cap_wan_hkd": safe_float(fields[69]) if len(fields) > 69 else None,
        "week_52_high": safe_float(fields[48]) if len(fields) > 48 else None,
        "week_52_low": safe_float(fields[49]) if len(fields) > 49 else None,
        "currency": "HKD",
        "date": fields[30] if len(fields) > 30 else "",
    }


def fetch_history(symbol: str, days: int = 365) -> dict:
    """Fetch historical OHLCV from Sina Finance HK API."""
    sym = _normalize(symbol)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Sina HK stock history API
    url = (
        f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
        f"CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no"
        f"&datalen={days}"
    )
    raw = _curl_get(url, referer="https://finance.sina.com.cn")
    if not raw:
        return {"error": f"No history data for {sym}"}

    try:
        records = json.loads(raw)
    except json.JSONDecodeError:
        return {"error": f"Parse error for history of {sym}"}

    prices = []
    for r in records:
        prices.append({
            "date": r.get("day", ""),
            "open": safe_float(r.get("open")),
            "high": safe_float(r.get("high")),
            "low": safe_float(r.get("low")),
            "close": safe_float(r.get("close")),
            "volume": safe_float(r.get("volume")),
        })

    return {
        "symbol": sym,
        "period_days": days,
        "data_points": len(prices),
        "prices": prices,
    }


def fetch_sina_realtime(symbol: str) -> dict:
    """Fetch real-time quote from Sina Finance HK API."""
    sym = _normalize(symbol)
    url = f"https://hq.sinajs.cn/list=hk{sym}"
    raw = _curl_get(url, referer="https://finance.sina.com.cn")
    if not raw:
        return {"error": f"No Sina data for {sym}"}

    match = re.search(r'"(.+)"', raw)
    if not match:
        return {"error": f"Sina parse error for {sym}"}

    fields = match.group(1).split(",")
    # Sina HK format: name,name_cn,current,prev_close,open,high,low,...
    return {
        "symbol": sym,
        "name_en": fields[0] if len(fields) > 0 else "",
        "name_cn": STOCK_NAMES.get(sym, ""),
        "current_price": safe_float(fields[2]) if len(fields) > 2 else None,
        "prev_close": safe_float(fields[3]) if len(fields) > 3 else None,
        "open": safe_float(fields[5]) if len(fields) > 5 else None,
        "high": safe_float(fields[6]) if len(fields) > 6 else None,
        "low": safe_float(fields[7]) if len(fields) > 7 else None,
        "volume": safe_float(fields[12]) if len(fields) > 12 else None,
        "turnover": safe_float(fields[11]) if len(fields) > 11 else None,
        "date": fields[17] if len(fields) > 17 else "",
        "time": fields[18] if len(fields) > 18 else "",
    }


def fetch_financials(symbol: str) -> dict:
    """Fetch financial statements from Sina Finance CN stock API (for H-share dual listings)."""
    sym = _normalize(symbol)

    # Try to get financial data via Sina stock finance interface
    url = (
        f"https://money.finance.sina.com.cn/corp/go.php/vFD_BalanceSheet/"
        f"stockid/{sym}/ctrl/part/displaytype/4.phtml"
    )
    raw = _curl_get(url, referer="https://finance.sina.com.cn")

    # Simplified: return basic financial metrics from Tencent API
    basic = fetch_basic_info(sym)
    return {
        "symbol": sym,
        "source": "tencent_finance",
        "valuation": {
            "pe_ratio": basic.get("pe_ratio"),
            "market_cap_hkd": basic.get("market_cap_hkd"),
        },
        "note": "Detailed financials require WebSearch for HK-listed companies. "
                "Use --full to get basic valuation + price data.",
    }


def _normalize(symbol: str) -> str:
    """Normalize HK stock symbol to 5-digit format."""
    sym = symbol.strip()
    for prefix in [".HK", ".hk", "HK"]:
        sym = sym.replace(prefix, "")
    return sym.zfill(5)


def main():
    parser = argparse.ArgumentParser(description="HK Stock Data Fetcher (港股数据)")
    parser.add_argument("symbol", help="HK stock code (e.g., 00700, 09988)")
    parser.add_argument("--history", action="store_true", help="Historical OHLCV prices")
    parser.add_argument("--financials", action="store_true", help="Financial statements")
    parser.add_argument("--valuation", action="store_true", help="Valuation metrics")
    parser.add_argument("--full", action="store_true", help="All data combined")
    parser.add_argument("--days", type=int, default=365, help="History period in days (default: 365)")

    args = parser.parse_args()
    symbol = _normalize(args.symbol)

    if args.full:
        basic = fetch_basic_info(symbol)
        time.sleep(0.3)
        history = fetch_history(symbol, args.days)
        time.sleep(0.3)
        financials = fetch_financials(symbol)
        output_json({
            "basic": basic,
            "history": history,
            "financials": financials,
        })
    elif args.history:
        output_json(fetch_history(symbol, args.days))
    elif args.financials:
        output_json(fetch_financials(symbol))
    elif args.valuation:
        output_json(fetch_basic_info(symbol))
    else:
        output_json(fetch_basic_info(symbol))


if __name__ == "__main__":
    main()
