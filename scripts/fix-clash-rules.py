#!/usr/bin/env python3
"""修复 ClashX / mihomo 的 rule-provider 报错:
    initial rule provider LAN error: file must have a `payload` field

背景：部分机场订阅的 rule-providers 指向的规则集（如 GlobalMedia / ChinaMedia）
本身不是 Clash 规则集格式，或者更新时下载/写出失败，落盘的缓存文件里没有
顶层 `payload:` 字段，内核加载时直接报错。

做法：把出问题的 http provider 改成 `type: inline`，把规则内容直接写进配置，
不再依赖缓存文件；保留 `path:` 以兼容 ClashX Pro 的 provider 注册。
网络不通时退回「就地补 payload 字段」。

用法:
  python3 fix-clash-rules.py               # dry-run，只报告
  python3 fix-clash-rules.py --apply       # 修复（自动备份到 .rulefix-backup/）
  python3 fix-clash-rules.py --apply --no-inline   # 只补 payload 字段
环境变量:
  CLASH_DIRS="/a:/b"     指定目录（默认自动探测）
  NO_PROXY_FETCH=1       下载规则时不走 127.0.0.1:7890
"""
import argparse
import os
import re
import shutil
import sys
import time
import urllib.request
from pathlib import Path

HOME = Path.home()
DEFAULT_DIRS = [
    HOME / ".config/clash",
    HOME / ".config/clash.meta",
    HOME / "Library/Application Support/io.github.clash-verge-rev.clash-verge-rev",
]
DIRS = ([Path(p) for p in os.environ["CLASH_DIRS"].split(":") if p]
        if os.environ.get("CLASH_DIRS") else DEFAULT_DIRS)
PROXY = "http://127.0.0.1:7890"


def opener():
    if os.environ.get("NO_PROXY_FETCH"):
        return urllib.request.build_opener()
    h = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    return urllib.request.build_opener(h)


def ensure_payload(path: Path) -> str:
    """文件缺顶层 payload 时就地补一行。返回动作描述。"""
    if not path.exists():
        return "文件不存在（下次更新订阅会重新下载）"
    text = path.read_bytes().decode("utf-8", "replace")
    if re.search(r"^\s*payload\s*:", text, re.M):
        return "ok"
    path.write_text("payload:\n" + text, encoding="utf-8")
    return "prepended"


def provider_section(s: str):
    i = s.find("\nrule-providers:")
    if i < 0:
        return None
    j = s.find("\nrules:", i)
    return i, s[i:j if j > 0 else len(s)]


def iter_entries(seg: str):
    """遍历 rule-providers 下的条目。允许重叠匹配：上一条目末行尾随空格会吞掉下一条目的缩进。"""
    pat = re.compile(r"\n  ([^\s#][^\n]*):\n((?:    [^\n]*\n)+)")
    pos = 0
    while True:
        m = pat.search(seg, pos)
        if not m:
            return
        yield m
        pos = m.start() + 1


def inline_provider(cfg: Path, name: str, url: str, fpath: Path) -> bool:
    """把 http provider 改成 inline（内容直接写进配置，不再依赖缓存文件）。"""
    s = cfg.read_text(encoding="utf-8")
    sec = provider_section(s)
    if not sec:
        return False
    i, seg = sec
    m = re.search(rf"\n  {re.escape(name)}:\n    type: \w+\n    behavior: \w+\n", seg)
    if not m:
        return False
    head_i = i + m.start()
    # 块尾 = 下一条目的起点（也可能紧贴上一条带缩进的末行）
    nxt = re.search(r"\n  \S[^\n]*:\n    type:", seg[m.end():])
    body_i = i + m.end() + (nxt.start() + 1 if nxt else len(seg) - m.end())
    if "payload:" in s[head_i:body_i]:
        return True
    body = opener().open(urllib.request.Request(url, headers={"User-Agent": "clash-verge/2.4.2"}),
                         timeout=30).read().decode("utf-8", "replace")
    if not re.search(r"^\s*payload\s*:", body, re.M):
        body = "payload:\n" + body
    items = []
    for line in body.splitlines():
        mm = re.match(r"^\s*-\s+(.+)$", line.rstrip())
        if mm and not mm.group(1).startswith("#"):
            items.append(mm.group(1).strip().strip("'\""))
    if not items:
        return False
    # 保留 path：ClashX Pro 的兼容 provider 按 path 注册，缺了会让 RULE-SET 找不到规则
    keep = ""
    if fpath.exists():
        keep = "    path: ./" + str(fpath.relative_to(cfg.parent)) + "\n"
    block = (f"\n  {name}:\n    type: inline\n    behavior: classical\n" + keep +
             "    payload:\n" + "".join(f"      - {x}\n" for x in items))
    cfg.write_text(s[:head_i] + block + s[body_i:], encoding="utf-8")
    return True


def scan(cfg: Path):
    """返回 [(provider名, 文件路径, 问题, url)]"""
    s = cfg.read_text(encoding="utf-8", errors="replace")
    sec = provider_section(s)
    if not sec:
        return []
    bad = []
    for m in iter_entries(sec[1]):
        name, body = m.group(1).rstrip(":"), m.group(2)
        pm = re.search(r"path:\s*\./([^\s]+)", body)
        um = re.search(r"url:\s*(\S+)", body)
        if not pm:
            continue
        f = cfg.parent / pm.group(1)
        url = um.group(1) if um else None
        if not f.exists():
            bad.append((name, f, "文件不存在", url))
            continue
        txt = f.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"^\s*payload\s*:", txt, re.M):
            bad.append((name, f, "缺 payload 字段", url))
        elif re.search(r"^\s*-[^\s].*://", txt, re.M):
            bad.append((name, f, "混入 Clash 不认的 URL 形式规则", url))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真正修改（默认只报告）")
    ap.add_argument("--no-inline", action="store_true", help="只补 payload 字段，不改 inline")
    a = ap.parse_args()
    dirs = [d for d in DIRS if d.is_dir()]
    if not dirs:
        print("没找到 Clash 配置目录")
        return 1
    stamp = time.strftime("%Y%m%d-%H%M%S")
    found = False
    for d in dirs:
        printed = False
        for cfg in sorted(d.glob("*.yaml")):
            bad = scan(cfg)
            if not bad:
                continue
            if not printed:
                print(f"\n=== {d}")
                printed = True
            found = True
            print(f"  [{cfg.name}]")
            for name, f, why, url in bad:
                print(f"    - {name}: {why}  ({f.relative_to(d)})")
                if not a.apply:
                    continue
                if url and not a.no_inline:
                    try:
                        if inline_provider(cfg, name, url, f):
                            print("      → 已改为 inline，不再依赖缓存文件")
                            continue
                    except Exception as e:
                        print(f"      ! 下载失败（{e}），退回修缓存文件")
                bk = d / ".rulefix-backup" / stamp
                bk.mkdir(parents=True, exist_ok=True)
                if f.exists():
                    shutil.copy2(f, bk / f.name)
                print(f"      → {ensure_payload(f)}（备份 .rulefix-backup/{stamp}/{f.name}）")
    if not found:
        print("没有发现问题规则（所有 provider 文件都有 payload 字段）")
    elif not a.apply:
        print("\n（dry-run，加 --apply 才会修改）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
