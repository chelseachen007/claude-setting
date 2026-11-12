#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 Obsidian 投资笔记生成「数据湖事实卡」。

用法：
    python3 fact_card.py --preview 10          # 只打印前 10 篇，不写文件
    python3 fact_card.py --apply --limit 10    # 写入前 10 篇
    python3 fact_card.py --apply               # 写入全部

事实卡用 <!-- lake-facts:start/end --> 包裹，重复运行会原地替换，不会堆积。
只追加/替换这个区块，不动笔记正文。
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import duckdb

# 工作区根目录 = 本文件上溯两级（工具/数据湖/fact_card.py -> 投资/）
WORKSPACE = Path(__file__).resolve().parents[2]
LAKE = WORKSPACE / "data" / "cnequity"
VAULT = Path("/Users/chenjie/Documents/study/github/Obsidian/投资研究")
SKIP_DIRS = {"雪球日报", "youdata", "雪球大佬图鉴", "模板"}

START = "<!-- lake-facts:start -->"
END = "<!-- lake-facts:end -->"


def q(rel: str) -> str:
    # hive_partitioning 必须关掉：分区目录名（如 trade_date=2023）会顶掉同名的真实
    # DATE 字段，把日期静默截成「年」。这是本湖最坑的一个陷阱。
    return f"read_parquet('{LAKE}/{rel}/**/*.parquet', hive_partitioning=false)"


def load_instruments(con: duckdb.DuckDBPyConnection) -> dict[str, tuple[str, str, date | None]]:
    """归一化后的名字 -> (symbol, exchange, list_date)

    数据湖里的名字带行情前缀且被截断到 4 字（如「XD西部超」「N远大」「*ST海越」），
    直接按原文匹配会漏，所以索引时去掉前缀。
    """
    rows = con.execute(
        f"SELECT symbol, name, exchange, list_date FROM {q('curated/instruments')} "
        "WHERE asset_type = 'stock' AND delist_date IS NULL"
    ).fetchall()
    idx: dict[str, tuple[str, str, date | None]] = {}
    for symbol, name, exchange, list_date in rows:
        if not name:
            continue
        idx[name] = (symbol, exchange, list_date)
        clean = NAME_PREFIX_RE.sub("", name)
        if clean and clean != name:
            idx.setdefault(clean, (symbol, exchange, list_date))
    return idx


# 行情软件的名字前缀：XD 除息 / XR 除权 / DR 除权除息 / N 新股 / C 次新 / ST 系列
NAME_PREFIX_RE = re.compile(r"^(\*?ST|XD|XR|DR|N|C)+")


CODE_RE = re.compile(r"(\d{6})")
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
NOISE_RE = re.compile(
    r"(多空辩论分析|多空辩论|深度研究报告|多空对比|六线选股分析|多空对比分析|研究报告|分析|校对)$"
)


def resolve(note: Path, name_index: dict[str, tuple[str, str, date | None]]) -> str | None:
    stem = DATE_PREFIX_RE.sub("", note.stem)

    m = CODE_RE.search(stem)
    if m:
        code = m.group(1)
        for symbol in name_index.values():
            if symbol[0].startswith(code):
                return symbol[0]

    # 去掉后缀噪声后按名字做最长匹配
    cleaned = NOISE_RE.sub("", stem)
    candidates = [cleaned, stem]
    for text in candidates:
        if text in name_index:
            return name_index[text][0]
    best = None
    for name, (symbol, _, _) in name_index.items():
        if len(name) >= 3 and name in stem:
            if best is None or len(name) > len(best[0]):
                best = (name, symbol)
    return best[1] if best else None


def compute(con: duckdb.DuckDBPyConnection, symbols: list[str]) -> dict[str, dict]:
    if not symbols:
        return {}
    lst = ", ".join(f"'{s}'" for s in symbols)
    sql = f"""
    WITH adj AS (
      SELECT symbol, trade_date, factor
      FROM {q('derived/adj_factors')} WHERE adjust_type = 'hfq'
    ),
    base AS (
      SELECT b.symbol, b.trade_date, b.close, b.amount,
             b.close * COALESCE(a.factor, 1) AS h
      FROM {q('curated/daily_bars')} b
      LEFT JOIN adj a ON a.symbol = b.symbol AND a.trade_date = b.trade_date
      WHERE b.symbol IN ({lst}) AND b.close IS NOT NULL
    ),
    win AS (
      SELECT symbol, trade_date, h,
             max(h) OVER (PARTITION BY symbol ORDER BY trade_date
                          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS peak,
             lag(h) OVER (PARTITION BY symbol ORDER BY trade_date) AS prev_h
      FROM base
    ),
    agg AS (
      SELECT symbol,
             count(*) AS n_days,
             min(trade_date) AS d0,
             max(trade_date) AS d1,
             max(1 - h / peak) AS mdd,
             stddev_samp(ln(h / prev_h)) * sqrt(252) AS vol
      FROM win GROUP BY symbol
    ),
    last AS (
      SELECT symbol, trade_date AS last_date, close AS last_close, h AS last_h,
             avg(amount) OVER (PARTITION BY symbol ORDER BY trade_date
                               ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS amt20
      FROM base QUALIFY trade_date = max(trade_date) OVER (PARTITION BY symbol)
    ),
    r1y AS (
      SELECT b.symbol, b.h AS h_1y FROM base b
      JOIN last l ON l.symbol = b.symbol
      WHERE b.trade_date = (SELECT max(trade_date) FROM base x
                            WHERE x.symbol = b.symbol
                              AND x.trade_date <= l.last_date - INTERVAL 365 DAY)
    ),
    r3y AS (
      SELECT symbol, arg_min(h, trade_date) AS h_3y FROM base GROUP BY symbol
    )
    SELECT a.symbol, a.n_days, a.d0, a.d1, a.mdd, a.vol,
           l.last_date, l.last_close, l.last_h, l.amt20,
           r1y.h_1y, r3y.h_3y
    FROM agg a
    JOIN last l USING (symbol)
    LEFT JOIN r1y USING (symbol)
    LEFT JOIN r3y USING (symbol)
    """
    out = {}
    for row in con.execute(sql).fetchall():
        (symbol, n_days, d0, d1, mdd, vol, last_date, last_close, last_h,
         amt20, h_1y, h_3y) = row
        out[symbol] = {
            "n_days": n_days, "d0": d0, "d1": d1,
            "mdd": mdd, "vol": vol,
            "last_date": last_date, "last_close": last_close, "last_h": last_h,
            "amt20": amt20,
            "ret_1y": (last_h / h_1y - 1) if h_1y else None,
            "ret_3y": (last_h / h_3y - 1) if h_3y else None,
        }
    return out


def corporate(con: duckdb.DuckDBPyConnection, symbols: list[str]) -> dict[str, tuple[int, date | None]]:
    if not symbols:
        return {}
    lst = ", ".join(f"'{s}'" for s in symbols)
    rows = con.execute(
        f"SELECT symbol, count(*), max(ex_date) FROM {q('curated/corporate_actions')} "
        f"WHERE symbol IN ({lst}) GROUP BY symbol"
    ).fetchall()
    return {r[0]: (r[1], r[2]) for r in rows}


STATUS_MAP = {"normal": "正常交易", "suspended": "停牌", "delisted": "已退市"}


def status(con: duckdb.DuckDBPyConnection, symbols: list[str]) -> dict[str, str]:
    if not symbols:
        return {}
    lst = ", ".join(f"'{s}'" for s in symbols)
    rows = con.execute(
        f"""
        SELECT symbol, status, risk_warning FROM {q('curated/trading_status')}
        WHERE symbol IN ({lst})
        QUALIFY trade_date = max(trade_date) OVER (PARTITION BY symbol)
        """
    ).fetchall()
    out = {}
    for symbol, st, rw in rows:
        label = STATUS_MAP.get(st, st or "未知")
        if rw:
            label += " · ST/风险警示"
        out[symbol] = label
    return out


def fmt_pct(v, digits=2):
    return "—" if v is None else f"{v * 100:+.{digits}f}%"


def fmt_vol(v):
    return "—" if v is None else f"{v * 100:.2f}%"


def render(symbol, name, exchange, list_date, f, ca, st) -> str:
    years = "—"
    if list_date:
        years = f"{(date.today() - list_date).days / 365.25:.1f} 年"
    n_ca, last_ex = ca if ca else (0, None)
    last_ex_txt = f"{last_ex}" if last_ex else "—"
    amt = f"{f['amt20'] / 1e8:.2f} 亿" if f.get("amt20") else "—"
    lines = [
        START,
        f"> [!data] 数据湖事实 · 截至 {f['last_date']}",
        f"> 数据来源：本地 CNEquity 数据湖（{f['d0']} ~ {f['d1']}，{f['n_days']} 个交易日）",
        ">",
        "> | 项目 | 值 |",
        "> | --- | --- |",
        f"> | 代码 | `{symbol}`（{exchange}） |",
        f"> | 上市日期 | {list_date or '—'}（{years}） |",
        f"> | 最新收盘 | {f['last_close']:.2f}（{f['last_date']}） |",
        f"> | 近 1 年收益（复权） | {fmt_pct(f['ret_1y'])} |",
        f"> | 近 3 年收益（复权） | {fmt_pct(f['ret_3y'])} |",
        f"> | 3 年最大回撤 | {fmt_pct(-f['mdd'] if f['mdd'] else None)} |",
        f"> | 年化波动 | {fmt_vol(f['vol'])} |",
        f"> | 近 20 日均成交额 | {amt} |",
        f"> | 分红/除权次数 | {n_ca} 次（最近 {last_ex_txt}） |",
        f"> | 交易状态 | {st or '—'} |",
        END,
    ]
    return "\n".join(lines)


def upsert(note: Path, block: str) -> None:
    text = note.read_text(encoding="utf-8")
    if START in text and END in text:
        new = re.sub(
            re.escape(START) + r".*?" + re.escape(END),
            block,
            text,
            flags=re.S,
        )
    else:
        new = text.rstrip() + "\n\n" + block + "\n"
    note.write_text(new, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="写入笔记（默认只预览）")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 篇")
    ap.add_argument("--preview", type=int, default=0, help="预览前 N 篇")
    args = ap.parse_args()

    con = duckdb.connect()
    name_index = load_instruments(con)

    notes = sorted(
        p for p in VAULT.rglob("*.md")
        if p.is_file() and p.name != "README.md"
        and not (set(p.relative_to(VAULT).parts[:-1]) & SKIP_DIRS)
    )

    resolved: list[tuple[Path, str]] = []
    unresolved: list[Path] = []
    for note in notes:
        symbol = resolve(note, name_index)
        if symbol:
            resolved.append((note, symbol))
        else:
            unresolved.append(note)

    symbols = sorted({s for _, s in resolved})
    facts = compute(con, symbols)
    cas = corporate(con, symbols)
    sts = status(con, symbols)

    name_of = {v[0]: (k, v[1], v[2]) for k, v in name_index.items()}

    limit = args.preview or args.limit or len(resolved)
    written = 0
    for note, symbol in resolved[:limit]:
        f = facts.get(symbol)
        if not f:
            continue
        name, exchange, list_date = name_of.get(symbol, (symbol, "", None))
        block = render(symbol, name, exchange, list_date, f, cas.get(symbol), sts.get(symbol))
        if args.apply:
            upsert(note, block)
            written += 1
        else:
            print(f"\n===== {note.relative_to(VAULT)}  →  {symbol} {name} =====")
            print(block)

    print(f"\n--- 汇总 ---", file=sys.stderr)
    print(f"笔记总数 {len(notes)}｜识别出标的 {len(resolved)}｜未识别 {len(unresolved)}", file=sys.stderr)
    if args.apply:
        print(f"已写入 {written} 篇", file=sys.stderr)
    else:
        print("预览模式，未改动任何文件", file=sys.stderr)
    if unresolved:
        print("未识别样例：" + "、".join(p.stem for p in unresolved[:6]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
