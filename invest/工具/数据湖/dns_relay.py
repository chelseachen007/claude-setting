#!/usr/bin/env python3
"""本机 DNS 中继：只把写进 hosts 名单的域名，转交给系统解析器走一遍。

为什么需要它：
  本机所有域名都走 Clash 的 fake-ip（198.18.0.2 应答，返回 198.18.x.x）。
  curl 和 httpx 认这个假 IP，走代理的 CONNECT 时由代理解析真名，一切正常；
  **但 baostock 用自己的 socket 直连 public-api.baostock.com:10030，它不认假 IP**，
  于是报 `nodename nor servname provided`（等价于 curl 的 "Could not resolve host"）。

  可用性还受 macOS 对单个域名 DNS 解析器的限制：同一个域名每秒解析太多次会被拒
  （`nodename nor servname provided` 间歇出现），这也是 cne 日志里 DNS 错误时有时无的原因。

做法：
  `socket.getaddrinfo` 被换成了一个查「本进程内有缓存的中继表」的版本。缓存由后台线程
  按 TTL 刷新（默认 30s）。表为空时直接回落到原始解析，零风险。
  只有 net_resolve.py 会加载它，不影响任何别的程序。

用法（一般不用手动跑，net_resolve.py 会拉起）：
  .venv/bin/python3 工具/数据湖/dns_relay.py --hosts public-api.baostock.com --port 5399
"""

from __future__ import annotations

import argparse
import socket
import threading
import time

_table: dict[str, tuple[list[tuple[int, tuple]], float]] = {}
_lock = threading.Lock()
_orig_getaddrinfo = socket.getaddrinfo


def install(hosts, ttl=30.0, timeout=5.0):
    """把 hosts 里的名字交给一个带缓存的后台解析器，其余名字原样透传。"""
    hosts = tuple(h.lower() for h in hosts)

    def _lookup(host):
        socket.setdefaulttimeout(timeout)
        try:
            infos = _orig_getaddrinfo(host, None)
        except Exception:
            socket.setdefaulttimeout(None)
            return []
        socket.setdefaulttimeout(None)
        # 丢掉 fake-ip 段（198.18.0.0/15），只留真实地址
        keep = [
            (fam, addr) for fam, _t, _p, _c, addr in infos
            if fam == socket.AF_INET and not str(addr[0]).startswith("198.18.")
        ]
        return keep

    def _refresher():
        while True:
            for h in hosts:
                left = _lookup(h)
                if left:
                    with _lock:
                        _table[h] = (left, time.time() + ttl)
            time.sleep(ttl)

    def _getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        key = host.lower() if isinstance(host, str) else None
        if key and key in hosts:
            with _lock:
                entry = _table.get(key)
            if entry and entry[1] > time.time():
                return [
                    (fam, type or socket.SOCK_STREAM, proto or socket.IPPROTO_TCP, "",
                     (addr[0], port or 0))
                    for fam, addr in entry[0]
                ]
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    t = threading.Thread(target=_refresher, daemon=True)
    t.start()
    socket.getaddrinfo = _getaddrinfo
    # 首次同步解析一次，保证调用方第一次就能拿到真实地址
    for h in hosts:
        left = _lookup(h)
        if left:
            with _lock:
                _table[h] = (left, time.time() + ttl)
    return _table


def main() -> int:
    ap = argparse.ArgumentParser(description="DNS 中继（仅用于测试，业务侧由 net_resolve.py 拉起）")
    ap.add_argument("--hosts", nargs="+", default=["public-api.baostock.com"])
    ap.add_argument("--ttl", type=float, default=30.0)
    ap.add_argument("--port", type=int, default=5399)
    ap.add_argument("--once", action="store_true", help="解析一次打印结果就退出")
    a = ap.parse_args()
    table = install(a.hosts, ttl=a.ttl)
    for h in a.hosts:
        print(f"{h}: {[addr[0] for _f, addr in table.get(h, ((), 0))[0]]}")
        if not table.get(h):
            print(f"  ! 解析不到真实地址，仍在用原来那条路")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
