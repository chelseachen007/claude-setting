#!/usr/bin/env python3
"""在干净网络环境下跑 cne（去掉代理变量 + 给 baostock 换真实 IP）。

为什么需要这一层：
  1) httpx 0.28.1 解析 NO_PROXY 里的 `[::1]` 会抛 `InvalidURL: Invalid port: ':1]'`，
     只要代理变量在环境里，东财请求就可能全挂；本机所有源直连都通，代理变量纯属包袱。
  2) Clash fake-ip 让 `public-api.baostock.com` 解析成 198.18.x.x，baostock 用裸 socket
     连不上，需要 net_resolve 换成真实 A 记录。

用法（参数原样透传给 cne）：
  .venv/bin/python3 工具/数据湖/cne_clean.py run daily --group signals --config 配置/cnequity.toml
  .venv/bin/python3 工具/数据湖/cne_clean.py backfill daily_bars --outstanding --config 配置/cnequity.toml

调度器（launchd 那条）本身环境是干净的，不需要它；这个脚本是给「手动在终端里跑」用的。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(HERE))
    import net_resolve

    removed = net_resolve.scrub_proxy_env()
    net_resolve.install()
    if "-v" in argv:
        argv = [a for a in argv if a != "-v"]
        print(f"[cne_clean] 删掉代理变量 {list(removed)}；baostock 用真实 IP "
              f"{net_resolve.resolve('public-api.baostock.com')}", file=sys.stderr)

    os.chdir(PROJECT)
    sys.argv = ["cne", *argv]
    from cnequity.cli.main import cli  # type: ignore

    cli()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
