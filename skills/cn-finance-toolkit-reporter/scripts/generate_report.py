#!/usr/bin/env python3
"""
金融日报生成器
==============
从 fetch_data.py 获取数据，生成 Obsidian 格式日报。
自动保存到 Obsidian 洞察报告目录。

Usage:
    python generate_report.py                    # 生成今日日报
    python generate_report.py --date 2026-03-20  # 生成指定日期日报
    python generate_report.py --data-file xxx.json  # 从已有JSON数据生成
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OBSIDIAN_BASE = Path.home() / "Documents/study/github/Obsidian"
OBSIDIAN_REPORT_DIR = OBSIDIAN_BASE / "洞察报告/投资日报"


def get_obsidian_path(date_str: str) -> Path:
    """获取指定日期的 Obsidian 日报路径。"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    year = dt.strftime("%Y")
    month = dt.strftime("%Y-%m")
    day_file = dt.strftime("%Y-%m-%d") + ".md"
    return OBSIDIAN_REPORT_DIR / year / month / day_file


def _trend_arrow(pct: float | None) -> str:
    if pct is None:
        return "—"
    if pct > 0:
        return f"+{pct:.2f}%"
    return f"{pct:.2f}%"


def _trend_emoji(pct: float | None) -> str:
    if pct is None:
        return "—"
    if pct > 2:
        return "🔥"
    if pct > 0:
        return "📈"
    if pct < -2:
        return "⚠️"
    return "📉"


def generate_market_summary(data: dict) -> str:
    """生成市场板块摘要。"""
    lines = []

    # A股
    a_share = data.get("a_share", {})
    if a_share and not any("error" in str(v) for v in a_share.values() if isinstance(v, dict)):
        lines.append("## 一、A 股市场\n")
        lines.append("| 指数 | 收盘价 | 涨跌幅 | 趋势 |")
        lines.append("|------|--------|--------|------|")
        index_map = [
            ("上证指数", "sh000001"),
            ("沪深300", "sh000300"),
            ("上证50", "sh000016"),
            ("中证500", "sh000905"),
            ("深证成指", "sz399001"),
            ("创业板指", "sz399006"),
            ("科创50", "sh000688"),
            ("中证1000", "sz399852"),
        ]
        for name, code in index_map:
            if name in a_share:
                d = a_share[name]
                if isinstance(d, dict) and "price" in d:
                    chg = d.get("change_pct")
                    lines.append(
                        f"| {name} | {d['price']:.2f} | "
                        f"**{_trend_arrow(chg)}** | {_trend_emoji(chg)} |"
                    )
        lines.append("")

    # 美股
    us = data.get("us_stocks", {})
    if us and us.get("us_stocks"):
        lines.append("## 二、美股\n")
        lines.append("| 指数 | 最新价 | 涨跌% |")
        lines.append("|------|--------|-------|")
        for name, d in us.get("us_stocks", {}).items():
            if isinstance(d, dict) and "price" in d:
                chg = d.get("change_pct", d.get("chg"))
                lines.append(f"| {name} | {d['price']:,.2f} | {_trend_arrow(chg)} |")
        lines.append("")

    # 金属
    if us and us.get("metals"):
        lines.append("## 三、大宗商品\n")
        lines.append("| 商品 | 单位 | 价格 | 涨跌% |")
        lines.append("|------|------|------|-------|")
        for name, d in us.get("metals", {}).items():
            if isinstance(d, dict) and "price" in d:
                chg = d.get("change_pct", d.get("chg"))
                unit = "USD/oz" if name in ("Gold", "Silver", "Platinum", "Palladium") else "USD/lb"
                lines.append(f"| {name} | {unit} | {d['price']:,.2f} | {_trend_arrow(chg)} |")
        lines.append("")

    # 北向资金
    nb = data.get("northbound", {})
    if nb and not nb.get("error"):
        lines.append("## 四、北向资金\n")
        records = nb.get("records", nb.get("shanghai", []))
        if records:
            latest = records[-1] if isinstance(records, list) else records
            lines.append(f"- 交易日：{latest.get('date', 'N/A')}")
            if "north_net" in latest:
                lines.append(f"- 成交净买额：{latest['north_net']:.2f} 亿元")
            lines.append("")

    return "\n".join(lines)


def generate_macro_summary(macro: dict, cache_info: dict) -> str:
    """生成宏观数据摘要。"""
    lines = []
    lines.append("## 五、宏观数据\n")

    lines.append("> ⚠️ 以下数据更新频率低，已缓存，不重复获取。详见 [[投资-宏观数据]] 卡片。\n")
    lines.append("| 指标 | 最新值 | 日期 | 趋势 |")
    lines.append("|------|--------|------|------|")

    # LPR
    lpr = macro.get("lpr", {})
    if lpr and "latest" in lpr:
        latest = lpr["latest"]
        date = latest.get("date", "N/A")
        l1 = latest.get("lpr_1y", "—")
        l5 = latest.get("lpr_5y", "—")
        cached = cache_info.get("lpr", {}).get("from_cache", False)
        tag = "(缓存)" if cached else "(最新)"
        lines.append(f"| [[LPR]] 1年期 | {l1}% | {date} {tag} | 持平 |")
        lines.append(f"| [[LPR]] 5年期 | {l5}% | {date} | 持平 |")

    # PMI
    pmi = macro.get("pmi", {})
    if pmi:
        for key, label in [("official_mfg", "官方制造业[[PMI]]"), ("non_mfg", "非制造业PMI"), ("caixin_mfg", "财新制造业PMI")]:
            if key in pmi and pmi[key].get("value"):
                v = pmi[key]["value"]
                d = pmi[key].get("date", "N/A")
                signal = "⚠️ 低于50" if v < 50 else "✅ 高于50"
                lines.append(f"| {label} | {v} | {d} | {signal} |")

    # CPI/PPI
    inf = macro.get("inflation", {})
    for key, label in [("cpi", "[[CPI]] 同比"), ("ppi", "[[PPI]] 同比")]:
        if key in inf and inf[key].get("yoy") is not None:
            v = inf[key]["yoy"]
            d = inf[key].get("date", "N/A")
            signal = "通缩" if v < 0 else "通胀"
            lines.append(f"| {label} | {v:.1f}% | {d} | {signal} |")

    # FX Reserve
    fx = macro.get("fx_reserve", {})
    if fx and fx.get("gold_reserve_billion_usd"):
        lines.append(f"| 外汇储备 | {fx['gold_reserve_billion_usd']:.0f}亿美元 | {fx.get('date', 'N/A')} | +{fx.get('fx_reserve_chg', 0):.1f}% MoM |")
        lines.append(f"| 央行黄金储备 | {fx['gold_reserve_billion_usd']:.0f}亿美元 | {fx.get('date', 'N/A')} | +{fx.get('gold_reserve_chg', 0):.1f}% MoM |")

    lines.append("")
    return "\n".join(lines)


def generate_analysis(data: dict, macro: dict) -> str:
    """生成综合点评。"""
    lines = []
    lines.append("## 六、综合点评\n")

    # 市场情绪判断
    a_share = data.get("a_share", {})
    us = data.get("us_stocks", {})

    # 计算平均A股涨跌
    chgs = []
    for name, d in a_share.items():
        if isinstance(d, dict) and "change_pct" in d:
            chgs.append(d["change_pct"])

    avg_chg = sum(chgs) / len(chgs) if chgs else 0

    if avg_chg < -1.5:
        sentiment = "🔴 极度悲观"
    elif avg_chg < -0.5:
        sentiment = "⚠️ 偏悲观"
    elif avg_chg < 0.5:
        sentiment = "🟡 中性"
    else:
        sentiment = "🟢 偏乐观"

    lines.append(f"### 市场情绪：{sentiment}\n")

    # 关键观察点
    lines.append("### 关键观察点\n")
    if chgs:
        worst = min(chgs)
        best = max(chgs)
        lines.append(f"- A股平均涨跌幅：{avg_chg:+.2f}%，最大跌幅：{worst:+.2f}%，最大涨幅：{best:+.2f}%")

    # 北向资金
    nb = data.get("northbound", {})
    if nb and not nb.get("error"):
        records = nb.get("records", [])
        if records:
            lines.append(f"- 北向资金最近交易日：{records[-1].get('date', 'N/A')}")

    # 黄金闪崩检测
    metals = us.get("metals", {})
    gold = metals.get("Gold", {})
    if isinstance(gold, dict) and gold.get("price"):
        gold_chg = gold.get("change_pct", 0)
        if abs(gold_chg) > 3:
            lines.append(f"- ⚡ **黄金日内异动**：{gold_chg:+.2f}%（{gold.get('source', '')}）")

    lines.append("")
    return "\n".join(lines)


def build_obsidian_report(data: dict) -> str:
    """构建完整的 Obsidian 格式日报。"""
    report_date = data.get("report_date", datetime.now().strftime("%Y-%m-%d"))
    dt = datetime.strptime(report_date, "%Y-%m-%d")

    # 计算上一个交易日（A股）
    prev_trading = (dt - timedelta(days=3 if dt.weekday() == 0 else 1)).strftime("%Y-%m-%d")

    content = f"""---
title: 投资日报 {report_date}
date: {report_date}
tags: [投资日报, A股, 美股, 大宗商品]
aliases: [投资日报-{report_date.replace('-', '')}]
---

# 📊 投资日报 — {report_date}

**报告日期：{report_date}**
"""

    content += "\n" + generate_market_summary(data.get("data", {}))
    content += "\n" + generate_macro_summary(data.get("data", {}).get("macro", {}), data.get("cache_info", {}))
    content += "\n" + generate_analysis(data.get("data", {}), data.get("data", {}).get("macro", {}))

    content += """
---

> 数据获取时间：{fetch_time}
> ⚠️ 数据说明：部分数据源可能存在延迟或限流，建议交叉验证。
""".format(fetch_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return content


def main():
    parser = argparse.ArgumentParser(description="金融日报生成器")
    parser.add_argument("--date", default=None, help="指定日期（YYYY-MM-DD）")
    parser.add_argument("--data-file", default=None, help="从JSON文件读取数据")
    parser.add_argument("--output", default=None, help="输出文件路径（默认输出到标准输出）")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不保存到Obsidian")
    args = parser.parse_args()

    # 获取数据
    if args.data_file:
        with open(args.data_file) as f:
            data = json.load(f)
    else:
        # 调用 fetch_data.py
        import subprocess

        script = SCRIPT_DIR / "fetch_data.py"
        result = subprocess.run(
            [sys.executable, str(script), "--all"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"获取数据失败: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        try:
            data = json.loads(result.stdout)
        except Exception as e:
            print(f"解析数据失败: {e}", file=sys.stderr)
            print(f"原始输出: {result.stdout[:500]}", file=sys.stderr)
            sys.exit(1)

    # 生成日报
    date_str = args.date or data.get("report_date", datetime.now().strftime("%Y-%m-%d"))
    report = build_obsidian_report(data)

    # 输出
    if args.output:
        Path(args.output).write_text(report)
        print(f"✅ 日报已保存: {args.output}")
    elif args.dry_run:
        print(report)
    else:
        # 自动保存到 Obsidian
        obs_path = get_obsidian_path(date_str)
        obs_path.parent.mkdir(parents=True, exist_ok=True)
        obs_path.write_text(report)
        print(f"✅ 日报已保存: {obs_path}")
        print(f"   📄 相对路径: 洞察报告/投资日报/{obs_path.parent.name}/{obs_path.name}")


if __name__ == "__main__":
    main()
