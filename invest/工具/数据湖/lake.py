#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据湖查询小工具 —— 省掉每次重新探测表结构。

    python3 scripts/lake.py schema                 # 有哪些数据集、字段、行数、日期范围
    python3 scripts/lake.py schema daily_bars      # 只看一个
    python3 scripts/lake.py sql "select count(*) from daily_bars"
    python3 scripts/lake.py bars 600519.SH --adjust hfq --start 2026-09-01

SQL 模式会把 curated/ 和 derived/ 下所有数据集注册成同名视图，可以直接写
`select * from daily_bars`，另外附带一个 `daily_bars_adj` 视图（原始价 + hfq 复权价）。

注意：curated 下按 trade_date=YYYY-MM-DD/ 分区，读取要用 **/*.parquet。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

# 工作区根目录 = 本文件上溯两级（工具/数据湖/lake.py -> 投资/）
WORKSPACE = Path(__file__).resolve().parents[2]
LAKE = WORKSPACE / "data" / "cnequity"
ROOTS = {"curated": LAKE / "curated", "derived": LAKE / "derived"}


def datasets() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for _, root in ROOTS.items():
        if not root.is_dir():
            continue
        for d in sorted(root.iterdir()):
            if d.is_dir() and any(d.glob("**/*.parquet")):
                found[d.name] = d
    return found


def register(con: duckdb.DuckDBPyConnection) -> dict[str, Path]:
    found = datasets()
    for name, path in found.items():
        con.execute(
            f"CREATE OR REPLACE VIEW {name} AS "
            f"SELECT * FROM read_parquet('{path}/**/*.parquet', hive_partitioning=false)"
        )
    if "daily_bars" in found and "adj_factors" in found:
        con.execute("""
            CREATE OR REPLACE VIEW daily_bars_adj AS
            SELECT b.*, b.close * COALESCE(a.factor, 1) AS hfq_close
            FROM daily_bars b
            LEFT JOIN (SELECT symbol, trade_date, factor FROM adj_factors
                       WHERE adjust_type = 'hfq') a
              ON a.symbol = b.symbol AND a.trade_date = b.trade_date
        """)
    return found


def cmd_schema(con: duckdb.DuckDBPyConnection, only: str | None) -> None:
    found = register(con)
    if not found:
        print("数据湖是空的：", LAKE)
        return
    for name, path in found.items():
        if only and name != only:
            continue
        layer = "curated" if path.parent.name == "curated" else "derived"
        cols = con.execute(f"DESCRIBE SELECT * FROM {name}").fetchall()
        n = con.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        date_cols = [c[0] for c in cols if c[0] in
                     ("trade_date", "ex_date", "announce_date", "obs_date", "report_period")]
        span = ""
        if date_cols:
            d = date_cols[0]
            lo, hi = con.execute(f"SELECT min({d}), max({d}) FROM {name}").fetchone()
            span = f"  {lo} ~ {hi}"
        print(f"\n{name}  [{layer}]  {n:,} 行{span}")
        print("  " + ", ".join(f"{c[0]}:{c[1]}" for c in cols))
    print()


def cmd_sql(con: duckdb.DuckDBPyConnection, sql: str) -> None:
    register(con)
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    widths = [max(len(str(c)), *(len(str(r[i])) for r in rows)) if rows else len(str(c))
              for i, c in enumerate(cols)]
    print("  ".join(str(c).ljust(w) for c, w in zip(cols, widths)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(str(v).ljust(w) for v, w in zip(r, widths)))
    print(f"\n({len(rows)} 行)")


def cmd_bars(con: duckdb.DuckDBPyConnection, args) -> None:
    register(con)
    adj = args.adjust
    col = "hfq_close" if adj == "hfq" else "close"
    where = [f"symbol = '{args.symbol}'"]
    if args.start:
        where.append(f"trade_date >= '{args.start}'")
    if args.end:
        where.append(f"trade_date <= '{args.end}'")
    sql = (f"SELECT symbol, trade_date, {col} AS price, volume, amount "
           f"FROM daily_bars_adj WHERE {' AND '.join(where)} ORDER BY trade_date")
    if args.limit:
        sql += f" LIMIT {args.limit}"
    cmd_sql(con, sql)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("schema", help="列出数据集、字段与覆盖范围")
    p.add_argument("dataset", nargs="?", default=None)

    p = sub.add_parser("sql", help="跑一条 SQL")
    p.add_argument("query")

    p = sub.add_parser("bars", help="查单只股票行情")
    p.add_argument("symbol")
    p.add_argument("--adjust", choices=["raw", "hfq"], default="hfq")
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--limit", type=int, default=30)

    args = ap.parse_args()
    con = duckdb.connect()

    if args.cmd == "schema":
        cmd_schema(con, args.dataset)
    elif args.cmd == "sql":
        cmd_sql(con, args.query)
    elif args.cmd == "bars":
        cmd_bars(con, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
