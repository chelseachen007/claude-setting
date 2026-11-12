#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""会话考古（第二版）：只看「人开口时说的话」，找出反复出现的诉求。

## 为什么换口径

第一版统计命令频次，挖出来的全是 agent 自己跑的东西（curl 99 次、grep 98 次）——
那是机器的重复劳动，不是人的认知负担。真正该挖的是：**用户每次都要亲口再说一遍什么**。

一句话反复出现，说明「这件事本该由系统记住或自动做」。

## 输出

- 高频意图：把用户消息按开头句聚类（去掉具体名词后比骨架）
- 高频原话：完整句子出现 ≥2 次
- 每类的代表会话，方便回看上下文

用法：
    python3 工具/session_archaeology.py --days 60
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import time
from pathlib import Path

SESSIONS = Path.home() / ".dsh" / "sessions"

# 用户消息里的噪音：系统注入、时间戳、图像标注、goal 续跑提示
NOISE_PAT = re.compile(
    r"^\s*(\[Compressed conversation section\]|Time sampled|Browser time zone|"
    r"Elapsed since|The available skill catalog|Current runtime context|"
    r"<goal_round>|Continue working toward|^\[acp|^\s*$)"
)
CJK = re.compile(r"[\u4e00-\u9fff]")


def iter_sessions(days: int):
    cutoff = time.time() - days * 86400
    for f in SESSIONS.rglob("session.v4.jsonl.zstd"):
        try:
            if f.stat().st_mtime < cutoff:
                continue
            yield f
        except OSError:
            continue


def read_session(path: Path) -> list[dict]:
    import zstandard
    try:
        raw = zstandard.ZstdDecompressor().stream_reader(open(path, "rb")).read()
        return [json.loads(l) for l in raw.decode("utf-8", "ignore").splitlines() if l.strip()]
    except Exception:
        return []


def user_texts(records: list[dict]) -> list[str]:
    out = []
    for r in records:
        if r.get("type") != "user/message":
            continue
        d = r.get("data") or {}
        txt = d.get("text") or d.get("content") or ""
        if isinstance(txt, list):
            txt = " ".join(str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in txt)
        txt = str(txt).strip()
        if not txt or NOISE_PAT.match(txt):
            continue
        # 去掉 <system-reminder> / <...> 块
        txt = re.sub(r"<[^>]+>.*?</[^>]+>", "", txt, flags=re.S)
        txt = re.sub(r"<[^>]+>", "", txt).strip()
        # 导入的旧会话会把别的 agent 的长 prompt 一起带进来，那不是「人说的话」
        if len(txt) > 300 or txt.count("\n") > 2:
            continue
        if len(txt) < 2 or not CJK.search(txt):
            continue
        out.append(txt)
    return out


def skeleton(s: str) -> str:
    """把一句话压成骨架：去掉具体名词/代码/路径，只留诉求结构。"""
    s = re.sub(r"`[^`]*`", "", s)
    s = re.sub(r"[A-Za-z0-9_./\-]{3,}", "", s)
    s = re.sub(r"[^\u4e00-\u9fff]", "", s)   # 只留汉字，符号全是噪音
    return s[:14]


def main() -> int:
    ap = argparse.ArgumentParser(description="按人的诉求考古")
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    exact: collections.Counter = collections.Counter()
    skel: dict[str, list[str]] = collections.defaultdict(list)
    n_sess = 0
    total = 0

    for path in iter_sessions(a.days):
        recs = read_session(path)
        texts = user_texts(recs)
        if not texts:
            continue
        n_sess += 1
        sid = path.parent.name.replace("session-", "")
        for t in texts:
            total += 1
            if len(t) <= 60:
                exact[t] += 1
            k = skeleton(t)
            if len(k) >= 4:
                skel[k].append(f"{sid}:{t[:50]}")

    if a.json:
        print(json.dumps({
            "sessions": n_sess, "messages": total,
            "exact": exact.most_common(a.top),
            "skel": [(k, len(v), v[:3]) for k, v in sorted(skel.items(), key=lambda x: -len(x[1]))[:a.top]],
        }, ensure_ascii=False, indent=1))
        return 0

    print(f"近 {a.days} 天：{n_sess} 个会话、{total} 条人说的话\n")

    print("## 一字不差重复过的原话")
    rep = [(k, v) for k, v in exact.most_common() if v >= 2]
    if not rep:
        print("  没有完全相同的重复句。")
    for k, v in rep[: a.top]:
        print(f"  {v}×  {k}")

    print("\n## 骨架相同的诉求（去掉名词后同一句话）")
    for k, v in sorted(skel.items(), key=lambda x: -len(x[1]))[: a.top]:
        if len(v) < 3:
            break
        print(f"  {len(v):3d}×  「{k}」")
        print(f"         例：{v[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
