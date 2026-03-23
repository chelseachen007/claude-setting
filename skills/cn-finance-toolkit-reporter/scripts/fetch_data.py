#!/usr/bin/env python3
"""
金融日报数据获取器 — 智能缓存版
===================================
核心设计：
  - 高频数据（A股指数/美股/金属/北向）：每次必取
  - 低频数据（LPR/CPI/PPI/PMI/外汇储备）：缓存30天

Usage:
    python fetch_data.py --all          # 获取所有数据（智能缓存）
    python fetch_data.py --market       # 只取高频市场数据
    python fetch_data.py --macro       # 只取宏观数据（忽略缓存）
    python fetch_data.py --cache-show  # 显示缓存状态
    python fetch_data.py --cache-clear # 清除缓存
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_FILE = SCRIPT_DIR / "cache.json"
OBSIDIAN_BASE = Path.home() / "Documents/study/github/Obsidian"

# ---------------------------------------------------------------------------
# 缓存管理
# ---------------------------------------------------------------------------

def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return {"macro": {}, "market": {}}
    return {"macro": {}, "market": {}}


def save_cache(cache: dict):
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))


def cache_age(cache: dict, category: str, key: str) -> int:
    """返回缓存年龄（天）。-1 表示不存在。"""
    cat = cache.get(category, {})
    if key not in cat:
        return -1
    ts = cat[key].get("fetched_at", "")
    try:
        fetched = datetime.strptime(ts, "%Y-%m-%d")
        return (datetime.now() - fetched).days
    except Exception:
        return -1


def is_stale(cache: dict, category: str, key: str, max_age: int = 30) -> bool:
    """检查缓存是否过期。"""
    age = cache_age(cache, category, key)
    if age < 0:
        return True
    return age > max_age


def set_cache(cache: dict, category: str, key: str, data: dict):
    if category not in cache:
        cache[category] = {}
    cache[category][key] = {
        "fetched_at": datetime.now().strftime("%Y-%m-%d"),
        "data": data,
    }


# ---------------------------------------------------------------------------
# 高频数据获取（每次必取）
# ---------------------------------------------------------------------------

def fetch_a_share_indices() -> dict:
    """获取A股主要指数。"""
    import akshare as ak

    results = {}
    indices = {
        "sh000001": "上证指数",
        "sh000300": "沪深300",
        "sh000016": "上证50",
        "sh000905": "中证500",
        "sz399001": "深证成指",
        "sz399006": "创业板指",
        "sh000688": "科创50",
        "sz399852": "中证1000",
    }
    for code, name in indices.items():
        try:
            df = ak.stock_zh_index_daily(symbol=code)
            if df is not None and len(df) >= 2:
                d1 = df.tail(1).iloc[0]
                d2 = df.tail(2).iloc[0]
                close = float(d1["close"])
                prev = float(d2["close"])
                chg = (close - prev) / prev * 100
                results[name] = {
                    "price": round(close, 2),
                    "change_pct": round(chg, 2),
                    "prev_close": round(prev, 2),
                    "date": str(d1.name) if hasattr(d1, "name") else str(d1.get("date", "")),
                    "volume": float(d1.get("volume", 0)),
                }
        except Exception as e:
            results[name] = {"error": str(e)[:80]}
    return results


def fetch_us_stocks() -> dict:
    """获取美股和金属数据。优先 Stooq，备用 yfinance。"""
    results = {"us_stocks": {}, "metals": {}}

    # 1) 尝试 Stooq（更可靠，无限流）
    try:
        import urllib.request

        def fetch_stooq(ticker: str) -> dict | None:
            url = f"https://stooq.com/q/l/?s={ticker}&i=d"
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read().decode("utf-8")
                lines = data.strip().split("\n")
                if len(lines) < 2 or "N/D" in lines[1]:
                    return None
                parts = lines[1].split(",")
                if len(parts) >= 7:
                    try:
                        return {
                            "date": parts[1],
                            "close": float(parts[5]),
                            "prev_close": float(parts[5]),
                            "raw": parts,
                        }
                    except Exception:
                        return None
            except Exception:
                return None
            return None

        # Stooq 美股指数
        us_map = {
            "%5Espx": "S&P 500",
            "%5Edji": "Dow Jones",
            "%5Endx": "Nasdaq 100",
            "%5Erut": "Russell 2000",
            "%5Evix": "VIX",
        }
        for ticker, name in us_map.items():
            rec = fetch_stooq(ticker)
            if rec and rec["date"] == "20260320":
                # 需要获取前一天数据
                results["us_stocks"][name] = {
                    "price": round(rec["close"], 2),
                    "date": rec["date"],
                    "source": "stooq",
                }

        # Stooq 金属期货
        metals_map = {
            "gc.f": "Gold",
            "si.f": "Silver",
            "hg.f": "Copper",
            "pl.f": "Platinum",
            "pa.f": "Palladium",
        }
        for ticker, name in metals_map.items():
            rec = fetch_stooq(ticker)
            if rec:
                results["metals"][name] = {
                    "price": round(rec["close"], 2),
                    "date": rec["date"],
                    "source": "stooq",
                }
    except Exception as e:
        results["_stooq_error"] = str(e)[:80]

    # 2) 备用：yfinance（容易被限流）
    if not results["us_stocks"] or not results["metals"]:
        try:
            import yfinance as yf

            def fetch_yf(ticker: str) -> dict | None:
                try:
                    t = yf.Ticker(ticker)
                    hist = t.history(period="10d")
                    if hist is not None and len(hist) >= 2:
                        curr = hist.iloc[-1]
                        prev = hist.iloc[-2]
                        close = float(curr["Close"])
                        prev_close = float(prev["Close"])
                        return {
                            "price": close,
                            "prev_close": prev_close,
                            "change_pct": round((close - prev_close) / prev_close * 100, 2),
                        }
                except Exception:
                    pass
                return None

            yf_map = {
                "^GSPC": ("S&P 500", "us_stocks"),
                "^DJI": ("Dow Jones", "us_stocks"),
                "^IXIC": ("Nasdaq Composite", "us_stocks"),
                "^RUT": ("Russell 2000", "us_stocks"),
                "^VIX": ("VIX", "us_stocks"),
                "GC=F": ("Gold", "metals"),
                "SI=F": ("Silver", "metals"),
                "HG=F": ("Copper", "metals"),
                "PL=F": ("Platinum", "metals"),
                "PA=F": ("Palladium", "metals"),
            }
            for ticker, (name, cat) in yf_map.items():
                if cat == "us_stocks" and results["us_stocks"].get(name):
                    continue
                if cat == "metals" and results["metals"].get(name):
                    continue
                rec = fetch_yf(ticker)
                if rec:
                    results[cat][name] = {
                        "price": round(rec["price"], 2),
                        "change_pct": rec["change_pct"],
                        "prev_close": round(rec["prev_close"], 2),
                        "source": "yfinance",
                    }
        except ImportError:
            results["_yfinance_note"] = "yfinance not installed"

    return results


def fetch_northbound() -> dict:
    """获取北向资金流向。"""
    import akshare as ak

    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
        if df is not None and not df.empty:
            records = []
            for _, row in df.tail(5).iterrows():
                records.append({
                    "date": str(row.get("交易日", "")),
                    "north_net": float(row.get("成交净买额", 0)),
                    "type": str(row.get("板块", "")),
                })
            return {"records": records, "note": "沪港通/深港通成交净买额"}
    except Exception as e:
        return {"error": str(e)[:100]}

    # 备用：历史数据
    try:
        results = {"shanghai": [], "shenzhen": []}
        for symbol in ["沪股通", "深股通"]:
            df = ak.stock_hsgt_hist_em(symbol=symbol)
            if df is not None and not df.empty:
                key = "shanghai" if symbol == "沪股通" else "shenzhen"
                for _, row in df.tail(5).iterrows():
                    results[key].append({
                        "date": str(row.get("日期", "")),
                        "index_close": float(row.get("上证指数" if key == "shanghai" else "深证指数", 0)),
                        "index_chg": float(row.get("上证指数-涨跌幅" if key == "shanghai" else "深证指数-涨跌幅", 0)),
                        "top_stock": str(row.get("领涨股", "")),
                    })
        return results
    except Exception as e:
        return {"error": str(e)[:100]}


# ---------------------------------------------------------------------------
# 低频数据获取（缓存30天）
# ---------------------------------------------------------------------------

def fetch_macro_lpr() -> dict:
    """获取LPR数据。"""
    import akshare as ak

    try:
        df = ak.macro_china_lpr()
        if df is not None and not df.empty:
            records = []
            for _, row in df.tail(3).iterrows():
                records.append({
                    "date": str(row.get("TRADE_DATE", "")),
                    "lpr_1y": float(row.get("LPR1Y", 0)),
                    "lpr_5y": float(row.get("LPR5Y", 0)),
                })
            return {"records": records, "latest": records[-1] if records else None}
    except Exception as e:
        return {"error": str(e)[:80]}
    return {}


def fetch_macro_pmi() -> dict:
    """获取PMI数据。"""
    import akshare as ak

    results = {}
    try:
        df = ak.macro_china_pmi_yearly()
        if df is not None and not df.empty:
            latest = df.tail(1).iloc[0]
            results["official_mfg"] = {
                "date": str(latest.get("日期", "")),
                "value": float(latest.get("今值", 0)) if latest.get("今值") else None,
                "forecast": float(latest.get("预测值", 0)) if latest.get("预测值") else None,
                "prev": float(latest.get("前值", 0)) if latest.get("前值") else None,
            }
    except Exception as e:
        results["official_mfg"] = {"error": str(e)[:80]}

    try:
        df = ak.macro_china_non_man_pmi()
        if df is not None and not df.empty:
            latest = df.tail(1).iloc[0]
            results["non_mfg"] = {
                "date": str(latest.get("日期", "")),
                "value": float(latest.get("今值", 0)) if latest.get("今值") else None,
            }
    except Exception as e:
        results["non_mfg"] = {"error": str(e)[:80]}

    try:
        df = ak.macro_china_cx_pmi_yearly()
        if df is not None and not df.empty:
            latest = df.tail(1).iloc[0]
            results["caixin_mfg"] = {
                "date": str(latest.get("日期", "")),
                "value": float(latest.get("今值", 0)) if latest.get("今值") else None,
            }
    except Exception as e:
        results["caixin_mfg"] = {"error": str(e)[:80]}

    return results


def fetch_macro_inflation() -> dict:
    """获取CPI/PPI数据。"""
    import akshare as ak

    results = {}
    try:
        df = ak.macro_china_cpi_yearly()
        if df is not None and not df.empty:
            latest = df.tail(1).iloc[0]
            results["cpi"] = {
                "date": str(latest.get("日期", "")),
                "yoy": float(latest.get("今值", 0)) if latest.get("今值") else None,
                "forecast": float(latest.get("预测值", 0)) if latest.get("预测值") else None,
                "prev": float(latest.get("前值", 0)) if latest.get("前值") else None,
            }
    except Exception as e:
        results["cpi"] = {"error": str(e)[:80]}

    try:
        df = ak.macro_china_ppi_yearly()
        if df is not None and not df.empty:
            latest = df.tail(1).iloc[0]
            results["ppi"] = {
                "date": str(latest.get("日期", "")),
                "yoy": float(latest.get("今值", 0)) if latest.get("今值") else None,
                "forecast": float(latest.get("预测值", 0)) if latest.get("预测值") else None,
                "prev": float(latest.get("前值", 0)) if latest.get("前值") else None,
            }
    except Exception as e:
        results["ppi"] = {"error": str(e)[:80]}

    return results


def fetch_macro_fx_reserve() -> dict:
    """获取外汇储备和黄金储备数据。"""
    import akshare as ak

    try:
        df = ak.macro_china_fx_gold()
        if df is not None and not df.empty:
            latest = df.tail(1).iloc[0]
            return {
                "date": str(latest.get("月份", "")),
                "gold_reserve_billion_usd": float(latest.get("黄金储备-数值", 0)),
                "fx_reserve_billion_usd": float(latest.get("国家外汇储备-数值", 0)),
                "gold_reserve_chg": float(latest.get("黄金储备-环比", 0)),
                "fx_reserve_chg": float(latest.get("国家外汇储备-环比", 0)),
            }
    except Exception as e:
        return {"error": str(e)[:80]}
    return {}


def fetch_gold_etf_holdings() -> dict:
    """获取COMEX黄金ETF持仓数据。"""
    import akshare as ak

    try:
        df = ak.macro_cons_gold()
        if df is not None and not df.empty:
            records = []
            for _, row in df.tail(5).iterrows():
                records.append({
                    "date": str(row.get("日期", "")),
                    "total_tons": float(row.get("总库存", 0)),
                    "chg": float(row.get("增持/减持", 0)),
                })
            return {"records": records}
    except Exception as e:
        return {"error": str(e)[:80]}
    return {}


def fetch_sge_gold() -> dict:
    """获取上海黄金交易所黄金现货价格。"""
    import akshare as ak

    try:
        df = ak.spot_golden_benchmark_sge()
        if df is not None and not df.empty:
            records = []
            for _, row in df.tail(5).iterrows():
                records.append({
                    "date": str(row.get("交易时间", "")),
                    "evening": float(row.get("晚盘价", 0)),
                    "morning": float(row.get("早盘价", 0)),
                })
            return {"records": records}
    except Exception as e:
        return {"error": str(e)[:80]}
    return {}


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def fetch_all_data(force_macro: bool = False) -> dict:
    """获取所有数据，智能处理缓存。"""
    cache = load_cache()
    today = datetime.now().strftime("%Y-%m-%d")

    results = {
        "report_date": today,
        "cache_info": {},
        "data": {
            "a_share": None,
            "us_stocks": None,
            "northbound": None,
            "macro": {},
        },
    }

    # --- 高频数据：每次必取 ---
    print("📈 获取A股指数...", file=sys.stderr)
    results["data"]["a_share"] = fetch_a_share_indices()

    print("📊 获取美股+金属...", file=sys.stderr)
    results["data"]["us_stocks"] = fetch_us_stocks()

    print("💰 获取北向资金...", file=sys.stderr)
    results["data"]["northbound"] = fetch_northbound()

    # --- 低频数据：智能缓存 ---
    macro_funcs = {
        "lpr": fetch_macro_lpr,
        "pmi": fetch_macro_pmi,
        "inflation": fetch_macro_inflation,
        "fx_reserve": fetch_macro_fx_reserve,
        "gold_etf": fetch_gold_etf_holdings,
        "sge_gold": fetch_sge_gold,
    }

    for key, func in macro_funcs.items():
        stale = is_stale(cache, "macro", key, max_age=30) or force_macro
        age = cache_age(cache, "macro", key)
        results["cache_info"][key] = {
            "stale": stale,
            "age_days": age,
            "from_cache": not stale,
        }

        if stale:
            print(f"📋 获取宏观数据 [{key}]（缓存过期/强制刷新，{age}天前）...", file=sys.stderr)
            data = func()
            set_cache(cache, "macro", key, data)
            results["data"]["macro"][key] = data
        else:
            print(f"📋 宏观数据 [{key}]（缓存命中，{age}天前）...", file=sys.stderr)
            results["data"]["macro"][key] = cache["macro"][key]["data"]

    save_cache(cache)
    return results


def output_json(data: dict):
    import json

    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="金融日报数据获取器（智能缓存版）")
    parser.add_argument("--all", action="store_true", help="获取所有数据（默认）")
    parser.add_argument("--market", action="store_true", help="只获取高频市场数据")
    parser.add_argument("--macro", action="store_true", help="强制刷新宏观数据")
    parser.add_argument("--cache-show", action="store_true", help="显示缓存状态")
    parser.add_argument("--cache-clear", action="store_true", help="清除所有缓存")
    args = parser.parse_args()

    if args.cache_clear:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
        print("✅ 缓存已清除")
        return

    if args.cache_show:
        cache = load_cache()
        output_json(cache)
        return

    if args.market:
        # 只取高频数据
        data = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "data": {
                "a_share": fetch_a_share_indices(),
                "us_stocks": fetch_us_stocks(),
                "northbound": fetch_northbound(),
            },
        }
        output_json(data)
        return

    if args.macro:
        cache = load_cache()
        macro_funcs = {
            "lpr": fetch_macro_lpr,
            "pmi": fetch_macro_pmi,
            "inflation": fetch_macro_inflation,
            "fx_reserve": fetch_macro_fx_reserve,
            "gold_etf": fetch_gold_etf_holdings,
            "sge_gold": fetch_sge_gold,
        }
        results = {}
        for key, func in macro_funcs.items():
            data = func()
            set_cache(cache, "macro", key, data)
            results[key] = data
        save_cache(cache)
        output_json(results)
        return

    # 默认：全部数据（智能缓存）
    try:
        data = fetch_all_data(force_macro=args.macro)
        output_json(data)
    except ImportError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
