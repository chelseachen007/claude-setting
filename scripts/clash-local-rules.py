#!/usr/bin/env python3
"""把本地自定义规则挂回 ClashX / mihomo 配置。

背景：ClashX 更新订阅时会整份重写 ~/.config/clash/<name>.yaml，
手加的规则全被冲掉。但 rule-provider 指向的本地文件不会被删，
所以把规则放 Rules/local/*.yaml，主配置里只留两行引用 —— 丢掉后补回来即可。

本脚本做的事（幂等，可反复跑）：
  1. 在 rule-providers 段确保有 `MyExtra: {type: file, path: ./Rules/local/my-extra.yaml}`
  2. 在 rules 段确保有 `- RULE-SET,MyExtra,🚧Proxy`，插在 RULE-SET,Global 之前
  3. 校验：每个 RULE-SET 引用的 provider 都存在，规则目标组都存在
  4. --reload：通过 ClashX API 重载配置

用法:
  python3 clash-local-rules.py                 # dry-run，只报告缺什么
  python3 clash-local-rules.py --apply         # 写入（自动备份 .bak-<时间戳>）
  python3 clash-local-rules.py --apply --reload
  python3 clash-local-rules.py --apply --reload --all   # 所有订阅配置都处理

环境变量:
  CLASHX_CFG_NAME    只处理这一个配置名（默认 zhs.futbol）
"""
import argparse
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HOME = Path.home()
CLASH_DIR = HOME / ".config/clash"
LOCAL_DIR = CLASH_DIR / "Rules/local"
RULESET_NAME = "MyExtra"
RULESET_FILE = "my-extra.yaml"
TARGET_GROUP = "🚧Proxy"
DEFAULT_CFG = "zhs.futbol"

BLOCK_PROVIDER = (
    f"  {RULESET_NAME}:\n"
    f"    type: file\n"
    f"    behavior: classical\n"
    f"    path: ./Rules/local/{RULESET_FILE}\n"
)
MARK_RULE = "  # 本地自定义规则（订阅更新不会覆盖，见 Rules/local/）\n"
BLOCK_RULE = f"{MARK_RULE}  - RULE-SET,{RULESET_NAME},{TARGET_GROUP}\n"


def log(msg):
    print(msg, flush=True)


# ---------- 配置发现 ----------

def config_names(explicit, all_cfgs):
    if explicit:
        return [explicit]
    if all_cfgs:
        return sorted(p.stem for p in CLASH_DIR.glob("*.yaml")
                      if not p.stem.startswith("."))
    return [DEFAULT_CFG]


# ---------- 补引用 ----------

def ensure_provider(text):
    """确保 rule-providers 段有 MyExtra 条目。返回 (新文本, 是否改动)。"""
    if re.search(rf"^\s+{RULESET_NAME}\s*:\s*$", text, re.M):
        return text, False

    i = text.find("\nrule-providers:")
    if i < 0:
        i = text.find("\nproxies:")  # 老格式兜底
        if i < 0:
            raise SystemExit("❌ 找不到 rule-providers 段，配置格式不认识，手动处理")
        # 没有 rule-providers 段，直接建一个
        j = text.find("\nrules:", i)
        text = text[:j] + "\nrule-providers:\n" + BLOCK_PROVIDER + text[j:]
        return text, True

    j = text.find("\nrules:", i)
    if j < 0:
        raise SystemExit("❌ 找不到 rules 段")

    # 插到 rule-providers 段最后一条非空内容之后
    seg = text[i:j].rstrip("\n")
    return text[:i] + seg + "\n" + BLOCK_PROVIDER + text[j:], True


def ensure_rule(text):
    """确保 rules 段有 RULE-SET,MyExtra。优先插在 RULE-SET,Global 之前。"""
    if re.search(rf"^\s*-\s*RULE-SET,{RULESET_NAME},", text, re.M):
        return text, False

    m = re.search(r"^(\s*)-\s*RULE-SET,Global,", text, re.M)
    if m:
        return text[:m.start()] + BLOCK_RULE + text[m.start():], True

    # 没有 Global 兜底，就插在 rules: 段第一行
    i = text.find("\nrules:")
    if i < 0:
        raise SystemExit("❌ 找不到 rules 段")
    j = text.index("\n", i + 1) + 1
    return text[:j] + BLOCK_RULE + text[j:], True


# ---------- 校验 ----------

def validate(text, cfg_path):
    """返回问题列表。只做能在纯文本层面判断的检查。"""
    problems = []

    # rule-providers 里有但没定义
    providers = set(re.findall(r"^  ([^\s#][^\n:]*):\s*$", text, re.M))
    # 只保留 rule-providers 段内的，避免把 proxy-groups 当 provider
    i = text.find("\nrule-providers:")
    j = text.find("\nrules:", i) if i >= 0 else -1
    if i >= 0 and j > i:
        seg = text[i:j]
        providers = set(re.findall(r"^  ([^\s#][^\n:]*):\s*$", seg, re.M))
    else:
        providers = set()

    refs = set(re.findall(r"RULE-SET,([^,\s]+),", text))
    missing = refs - providers
    if missing:
        problems.append(f"RULE-SET 引用了未定义的 provider: {sorted(missing)}")

    # 规则目标组是否存在
    groups = set(re.findall(r"^\s+-\s*name:\s*(.+?)\s*$", text, re.M))
    targets = set()
    for m in re.finditer(r"^\s*-\s*RULE-SET,[^,]+,\s*(.+?)\s*$", text, re.M):
        targets.add(m.group(1))
    bad_groups = {t for t in targets if t not in groups and t not in
                  ("DIRECT", "REJECT", "REJECT-DROP", "PASS")}
    if bad_groups:
        problems.append(f"规则指向了不存在的策略组: {sorted(bad_groups)}")

    # 本地规则文件本身
    if RULESET_NAME in providers:
        rf = LOCAL_DIR / RULESET_FILE
        if not rf.exists():
            problems.append(f"本地规则文件不存在: {rf}")
        else:
            body = rf.read_text(encoding="utf-8")
            if not re.search(r"^\s*payload\s*:", body, re.M):
                problems.append(f"本地规则文件缺少 payload 字段: {rf}")

    if not re.search(rf"^\s*-\s*RULE-SET,{RULESET_NAME},", text, re.M):
        problems.append(f"rules 段缺少 RULE-SET,{RULESET_NAME}")

    return problems


# ---------- ClashX API 重载 ----------

def clashx_api():
    """从 ClashX Pro 偏好里读 API 端口和 secret。"""
    try:
        raw = subprocess.run(
            ["defaults", "export", "com.west2online.ClashXPro", "-"],
            capture_output=True, check=True).stdout
        d = plistlib.loads(raw)
        port = d.get("apiPort")
        secret = d.get("api-secret")
        if port and secret:
            return int(port), str(secret)
    except Exception:
        pass
    return None


def reload_cfg():
    api = clashx_api()
    if not api:
        log("⚠️  读不到 ClashX Pro 的 API 端口/secret，跳过自动重载")
        log("   手动操作：菜单栏 → Config → Reload Config")
        return False
    port, secret = api
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/configs?force=true",
        data=json.dumps({"path": "", "payload": ""}).encode(),
        headers={"Authorization": f"Bearer {secret}",
                 "Content-Type": "application/json"},
        method="PUT")
    # path 为空表示重载当前配置文件
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=10) as r:
            log(f"✅ 已请求 ClashX 重载配置 (HTTP {r.status})")
            return True
    except urllib.error.HTTPError as e:
        log(f"⚠️  重载失败 HTTP {e.code}: {e.read()[:200].decode('utf-8', 'replace')}")
    except Exception as e:
        log(f"⚠️  重载失败: {e}")
    log("   手动操作：菜单栏 → Config → Reload Config")
    return False


# ---------- 主流程 ----------

def process(cfg_path, apply):
    log(f"\n=== {cfg_path}")
    if not cfg_path.exists():
        log(f"⚠️  不存在，跳过")
        return "skip"

    text = cfg_path.read_text(encoding="utf-8")
    new, ch_prov = ensure_provider(text)
    new, ch_rule = ensure_rule(new)

    if not ch_prov and not ch_rule:
        log("✅ 引用已存在，无需改动")
    else:
        log(f"{'补' if ch_prov else '✓'} rule-providers 段 MyExtra")
        log(f"{'补' if ch_rule else '✓'} rules 段 RULE-SET,MyExtra")

    problems = validate(new, cfg_path)
    if problems:
        for p in problems:
            log(f"   ❌ {p}")
    else:
        log("   校验通过")

    if not apply:
        if ch_prov or ch_rule:
            log("   (dry-run，未写入；加 --apply 生效)")
        return "ok"

    if ch_prov or ch_rule:
        backup = cfg_path.with_suffix(
            f".yaml.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(cfg_path, backup)
        cfg_path.write_text(new, encoding="utf-8")
        log(f"   已写入，备份: {backup.name}")
        return "changed"
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="实际写入")
    ap.add_argument("--reload", action="store_true", help="写入后让 ClashX 重载")
    ap.add_argument("--all", action="store_true", help="处理所有订阅配置")
    ap.add_argument("--config", help="只处理指定配置名")
    args = ap.parse_args()

    if not CLASH_DIR.exists():
        raise SystemExit(f"❌ 目录不存在: {CLASH_DIR}")

    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    if not (LOCAL_DIR / RULESET_FILE).exists():
        log(f"⚠️  本地规则文件不存在: {LOCAL_DIR / RULESET_FILE}")
        log("   引用补上后会被内核报错，先手动创建它")

    names = config_names(args.config or os.environ.get("CLASHX_CFG_NAME"),
                         args.all)
    results = {}
    for name in names:
        cfg = CLASH_DIR / f"{name}.yaml"
        results[name] = process(cfg, args.apply)

    changed = [n for n, r in results.items() if r == "changed"]
    if args.apply and args.reload and changed:
        log("")
        reload_cfg()
    elif changed:
        log("\n提示：加 --reload 可以自动让 ClashX 重载")

    return 0


if __name__ == "__main__":
    sys.exit(main())
