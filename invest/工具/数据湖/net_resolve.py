#!/usr/bin/env python3
"""跨数据湖进程解析真实域名：在代理 + fake-ip 环境下让 socket 直连能工作。

背景（2026-11-12 排查结论）：
  本机 DNS 由 Clash fake-ip 统一应答（198.18.0.2 → 198.18.x.x）。curl / httpx 走
  系统代理时由代理去解析真名，所以 HTTP 源都正常；**但 baostock 用裸 socket 连
  public-api.baostock.com:10030，假 IP 连不上**。另外 macOS 对单域名解析有速率
  限制，同一名字每秒问太多次会返回 EAI_NONAME，于是 cne 日志里 DNS 报错时有时无
  （实测 12:17 与 12:20 各一次，随后自行恢复）。

做法：
  用 223.5.5.5（阿里公共 DNS，国内可达、不依赖代理）把那几个「必须直连」的域名
  解析成真实 A 记录，装进进程内的 getaddrinfo 补丁 + 30s 缓存。只影响被列出的域名，
  其余域名原样走系统解析。
"""

from __future__ import annotations

import socket
import struct
import threading
import time

# 必须真实 IP 才能连上的域名（它们不走系统代理）
DNS_HOSTS = (
    "public-api.baostock.com",
)
RESOLVER_IP = "223.5.5.5"
TTL_SECONDS = 30.0

_cache: dict[str, tuple[tuple[str, ...], float]] = {}
_lock = threading.Lock()
_orig_getaddrinfo = socket.getaddrinfo
_installed = False


def _dns_query(name: str, ip: str = RESOLVER_IP, timeout: float = 3.0) -> tuple[str, ...]:
    """最小 A 记录查询，不依赖 dnspython。"""
    tid = 0x5A5A
    q = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    for label in name.strip(".").split("."):
        q += struct.pack("!B", len(label)) + label.encode()
    q += b"\x00" + struct.pack("!HH", 1, 1)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(q, (ip, 53))
        data, _ = s.recvfrom(2048)
    finally:
        s.close()
    if len(data) < 12 or data[:2] != struct.pack("!H", tid):
        return ()
    ancount = struct.unpack("!H", data[6:8])[0]
    pos = 12
    while data[pos] != 0:  # 跳过问题段的 QNAME
        pos += data[pos] + 1
    pos += 5  # QTYPE + QCLASS
    found = []
    for _ in range(ancount):
        if data[pos] & 0xC0 == 0xC0:  # 压缩指针
            pos += 2
        else:
            while data[pos] != 0:
                pos += data[pos] + 1
            pos += 1
        rtype, _rclass, _ttl, rdlen = struct.unpack("!HHIH", data[pos:pos + 10])
        pos += 10
        if rtype == 1 and rdlen == 4:
            found.append(".".join(str(b) for b in data[pos:pos + 4]))
        pos += rdlen
    return tuple(found)


def resolve(name: str) -> tuple[str, ...]:
    key = name.lower()
    with _lock:
        hit = _cache.get(key)
    if hit and hit[1] > time.time():
        return hit[0]
    ips = ()
    try:
        ips = _dns_query(key)
    except Exception:
        ips = ()
    if not ips:  # 公共 DNS 不通时退回 dig，再不行退回系统解析
        try:
            import subprocess

            out = subprocess.run(
                ["dig", "+short", "+time=2", "+tries=1", "@" + RESOLVER_IP, key],
                capture_output=True, text=True, timeout=6,
            ).stdout.split()
            ips = tuple(x for x in out if x.count(".") == 3 and not x.startswith("198.18."))
        except Exception:
            ips = ()
    if ips:
        with _lock:
            _cache[key] = (ips, time.time() + TTL_SECONDS)
    return ips


def install(hosts=DNS_HOSTS):
    """给当前进程装上补丁；重复调用无副作用。"""
    global _installed
    if _installed:
        return
    names = tuple(h.lower() for h in hosts)
    for h in names:
        resolve(h)

    def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        key = host.lower() if isinstance(host, str) else None
        if key in names:
            ips = resolve(key)
            if ips:
                socktype = type or socket.SOCK_STREAM
                return [
                    (socket.AF_INET, socktype, proto or socket.IPPROTO_TCP, "",
                     (ip, port or 0))
                    for ip in ips
                ]
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = getaddrinfo
    _installed = True


def scrub_proxy_env() -> dict[str, str]:
    """删掉环境里所有代理变量，返回删掉了哪些。

    为什么：httpx 0.28.1 解析 NO_PROXY 时，遇到带方括号的 IPv6 项（本机
    NO_PROXY 里有 `[::1]`）会抛 `InvalidURL: Invalid port: ':1]'`。实测它在
    「没有代理但有 NO_PROXY」和「有代理且域名不在 NO_PROXY 里」两种情况下都会触发，
    结果东财请求全部报错、历史回补一条也补不上。本机所有源直连都正常
    （datacenter、交易所、baostock 都通），所以最干净的做法就是把代理变量一并去掉。
    """
    import os

    removed = {}
    for key in list(os.environ):
        if key.lower() in {"all_proxy", "http_proxy", "https_proxy", "no_proxy"}:
            removed[key] = os.environ.pop(key)
    return removed


if __name__ == "__main__":
    import os
    import sys

    if "--scrub" in sys.argv:
        print("删掉的代理变量:", list(scrub_proxy_env()))
    for h in DNS_HOSTS:
        print(f"{h}: {resolve(h) or '解析失败'}")
