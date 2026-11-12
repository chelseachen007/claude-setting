#!/usr/bin/env python3
"""数据湖看门狗：每日抓取没跑 / 数据过期时主动告警。

为什么要有它：10-30 之后数据湖静默停了 13 天没人知道。`cne serve` 的进程一直活着，
看板健康检查看的是「进程在不在」，看不出「数据三天没更新」。

判据（全部满足才算失败）：
  1. 今天是沪深交易日
  2. 现在已过收盘 + 缓冲（默认 15:05）
  3. daily_bars 最新交易日 != 今天（允许配置的滞后）
  4. 今天 06:05 以来没有进行中的数据抓取（cne 进程 / serve job）

告警方式（任一成功即算已告警）：
  - macOS 通知中心（osascript）
  - 微信推送（仅当 WECHAT_PUSH=1 且 wechat-clawbot-push 技能可用）

用法：
  .venv/bin/python3 工具/数据湖/lake_watchdog.py            # 正常巡检
  .venv/bin/python3 工具/数据湖/lake_watchdog.py --dry-run  # 只打印判断过程，不告警
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
STATE = PROJECT / "data" / "cnequity" / "meta" / "state" / "daily_bars.json"
CURRICULUM = PROJECT / "data" / "cnequity" / "curated" / "daily_bars"
CONFIG = PROJECT / "配置" / "cnequity.toml"

# 进程识别用的标记：常驻服务（看板/调度器）不算抓取，其余 cne 进程才算
SERVE_MARKER = "cne-wb serve"                # 看板常驻进程（实测 argv 就是 .venv/bin/cne-wb serve）
SCHEDULER_MARKER = "cnequity.serve.ops.scheduled"
JOB_MARKER = "cnequity.serve.ops.job"
INGEST_MARKER = re.compile(r"(^|\s)cne\s+(run|init|backfill)\b")


def is_session(day) -> bool:
    sys.path.insert(0, str(PROJECT / ".venv" / "lib" / "python3.13" / "site-packages"))
    try:
        from cnequity.adapters.calendar.holidays_cn import CLOSED_DATES

        if day.isoformat() in CLOSED_DATES:
            return False
    except Exception:  # 没装 cnequity 时退化为工作日判断
        pass
    return day.weekday() < 5


def latest_bar_date():
    """curated/daily_bars 下最新的 trade_date 分区。"""
    if not CURRICULUM.exists():
        return None
    dates = sorted(p.name.split("=", 1)[1] for p in CURRICULUM.glob("trade_date=*"))
    return dates[-1] if dates else None


def an_ingest_is_running(now) -> bool:
    """今天 06:05 之后启动的 cne 抓取进程还算「在跑」，不告警。

    只看真正干活的两类进程：serve 拉起的 job（`-m cnequity.serve.ops.job`）和
    命令行 cne（`cne run|init|backfill`）。**常驻的看板服务本身要排除** ——
    它 `pgrep -f cnequity` 永远命中，且 06:05 之后才重启的话会被误当成抓取中，
    从而把「今天没抓到」整个吞掉（2026-11-12 实测就踩到了）。
    """
    morning = now.replace(hour=6, minute=5, second=0, microsecond=0)
    try:
        out = subprocess.run(
            ["ps", "-axo", "pid=,command="], capture_output=True, text=True, timeout=10
        ).stdout
    except Exception:
        return False
    for line in out.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        pid_text, command = parts
        if "cnequity" not in command and "cne " not in command:
            continue
        if SERVE_MARKER in command or SCHEDULER_MARKER in command or "cnequity.serve.ops.server" in command:
            continue  # 常驻服务 / 调度器，不是抓取
        if not (JOB_MARKER in command or INGEST_MARKER.search(command)):
            continue
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        started = process_start(pid)
        if started and started >= morning:
            return True
    return False


def bars_landed_after_cutoff(now) -> bool:
    """今天 15:05 之后 daily_bars 有过写入，就算当天的数据已经落地。

    比「有没有进程在跑」更直接：15:30 的日更可能到 16 点才写盘，这条判据不会误报；
    反过来，某个跟抓数无关的 cnequity 进程也不会让它漏报。
    """
    cutoff = now.replace(hour=15, minute=5, second=0, microsecond=0)
    if not CURRICULUM.exists():
        return False
    for part in CURRICULUM.glob("trade_date=*"):
        for f in part.glob("*.parquet"):
            try:
                if datetime.fromtimestamp(f.stat().st_mtime) >= cutoff:
                    return True
            except OSError:
                continue
    return False


def process_start(pid: int):
    """用 lstart 判断进程启动时间；拿不到返回 None。"""
    try:
        out = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        if not out:
            return None
        return datetime.strptime(out, "%a %b %d %H:%M:%S %Y")
    except Exception:
        return None


def notify(title: str, message: str) -> list[str]:
    """通知中心 + 可选微信；返回已用通道。

    通知中心走 osascript 的 `display notification`。它成功退出的含义是
    「App 有权限发」，不保证横幅真弹出来（免打扰、专注模式都会吞掉），
    这是 osascript 能力边界内能做到的最强信号。
    """
    used = []
    escape = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')
    script = f'display notification "{escape(message)}" with title "{escape(title)}" sound name "Basso"'
    if shutil.which("osascript") and subprocess.run(
        ["osascript", "-e", script], capture_output=True
    ).returncode == 0:
        used.append("notifycenter")

    if os.environ.get("WECHAT_PUSH") == "1":
        pusher = Path.home() / "ai" / "skills" / "wechat-clawbot-push"
        push_py = next(iter(sorted(pusher.glob("scripts/*.py"))), None) if pusher.exists() else None
        if push_py:
            proc = subprocess.run(
                [sys.executable, str(push_py), "--title", title, message],
                capture_output=True, text=True, timeout=60,
            )
            if proc.returncode == 0:
                used.append("wechat")
    return used


def main() -> int:
    ap = argparse.ArgumentParser(description="数据湖抓取看门狗")
    ap.add_argument("--dry-run", action="store_true", help="只打印判断，不告警")
    ap.add_argument("--after-hours", type=float, default=15.08,
                    help="几点算收盘后（小时，默认 15.08 即 15:05）")
    ap.add_argument("--max-lag", type=int, default=0,
                    help="允许 daily_bars 落后几个交易日（默认 0，即必须更新到今天）")
    args = ap.parse_args()

    now = datetime.now()
    today = now.date()
    verdict = {
        "checked_at": now.isoformat(timespec="seconds"),
        "is_session_today": is_session(today),
        "after_hours": now.hour + now.minute / 60 >= args.after_hours,
        "latest_bar_date": latest_bar_date(),
        "ingest_running": False,
        "state_file": str(STATE),
    }

    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    verdict["last_success_trade_date"] = state.get("last_success_trade_date")
    verdict["coverage_status"] = state.get("coverage_status")
    verdict["outstanding_keys"] = len(state.get("outstanding_keys") or [])

    # 不告警的三种情况
    if not verdict["is_session_today"]:
        verdict["result"] = "skip:非交易日"
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
        return 0
    if not verdict["after_hours"]:
        verdict["result"] = "skip:未收盘"
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
        return 0
    verdict["ingest_running"] = an_ingest_is_running(now)
    verdict["bars_landed_after_cutoff"] = bars_landed_after_cutoff(now)
    if verdict["ingest_running"] or verdict["bars_landed_after_cutoff"]:
        # 15:30 的日更写完盘可能已经 16 点了，盘面文件有新写入就算今天抓过，
        # 此时报「没抓到」就是误报。
        verdict["result"] = "skip:抓取进行中"
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
        return 0

    # 到期判定
    latest = verdict["latest_bar_date"]
    lag_sessions = 0
    if latest:
        d = today
        while d.isoformat() > latest:
            if is_session(d):
                lag_sessions += 1
            d -= timedelta(days=1)
    verdict["lag_sessions"] = lag_sessions

    if lag_sessions <= args.max_lag:
        verdict["result"] = "ok"
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
        return 0

    verdict["result"] = "ALERT"
    title = "投资数据湖：今天没抓到数据"
    body = (
        f"最新行情只到 {latest}，落后 {lag_sessions} 个交易日。"
        f"看板 http://localhost:8787 可直接补跑。"
    )
    verdict["alert"] = {"title": title, "body": body}
    if args.dry_run:
        verdict["alert"]["channels"] = ["dry-run"]
    else:
        verdict["alert"]["channels"] = notify(title, body) or ["failed"]
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    return 1 if not args.dry_run else 0


if __name__ == "__main__":
    raise SystemExit(main())
