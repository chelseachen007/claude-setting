#!/usr/bin/env python3
"""
send_wechat.py — 通过 WorkBuddy 已绑定的「微信 ClawBot」(iLink bot) 把文本推送到用户个人微信。

跨平台：
  - WorkBuddy 宿主：自动读取 ~/.workbuddy/settings.json 中 claw.users.*.channels.weixinClawBot
  - Codex / Claude Code 等无 WB 托管的宿主：用环境变量或独立配置文件提供凭据
      CLAWBOT_BOT_TOKEN / CLAWBOT_BASE_URL / CLAWBOT_USER_ID
      或 ~/.clawbot/config.json {"botToken":..., "baseUrl":..., "userId":...}

关键发现（v2，实测）：对「用户自己绑定的 ClawBot」，sendmessage 用**空 context_token** 即可直接推送本人，
无需先让用户在微信发一条 inbound 消息来"种"令牌。getupdates 取令牌的逻辑保留为可选兜底。

只发文本（不发文件加密上传），纯标准库，不依赖任何第三方包。

用法：
  python3 send_wechat.py send "要发的文本"          # 发送文本（超长自动分条）
  python3 send_wechat.py send --file 报告.md        # 读取文件内容发送（自动分条）
  python3 send_wechat.py status                     # 显示绑定/凭据状态
  python3 send_wechat.py refresh                    # 可选：轮询取 context_token（多数情况不需要）
  python3 send_wechat.py send --json "文本"          # JSON 输出模式（便于程序调用）
"""
import json
import os
import sys
import uuid
import base64
import time
import urllib.request
import urllib.error

WB_SETTINGS_CANDIDATES = [
    os.path.expanduser("~/.workbuddy/settings.json"),
    os.path.expanduser("~/.workbuddy-ai/settings.json"),
]
STANDALONE_CFG = os.path.expanduser("~/.clawbot/config.json")
CACHE = os.path.expanduser("~/.clawbot/.token_cache.json")
CHANNEL_VERSION = "workbuddy-desktop-1.0.0"
HTTP_TIMEOUT = 45
MAX_CHUNK = 1800  # 单条微信文本安全长度


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def mask(s, keep=4):
    """脱敏显示：仅保留首尾若干字符，避免用户把 status 输出贴到公开渠道时泄露标识。"""
    s = str(s)
    if len(s) <= keep * 2:
        return "***"
    return f"{s[:keep]}***{s[-keep:]}"


def gen_uin():
    return base64.b64encode(os.urandom(16)).decode("ascii")


def load_cfg():
    """按优先级发现 ClawBot 凭据：环境变量 > WB settings.json > 独立 config.json。"""
    tok = os.environ.get("CLAWBOT_BOT_TOKEN")
    base = os.environ.get("CLAWBOT_BASE_URL")
    uid = os.environ.get("CLAWBOT_USER_ID")
    if tok and base and uid:
        return {"botToken": tok, "baseUrl": base, "userId": uid,
                "channelId": os.environ.get("CLAWBOT_CHANNEL_ID", ""),
                "enabled": True, "source": "env"}

    # WorkBuddy 宿主：settings.json -> claw.users[legacyOwnerUid].channels.weixinClawBot
    # 兼容两种目录名：~/.workbuddy（旧）与 ~/.workbuddy-ai（当前）
    for wb_settings in WB_SETTINGS_CANDIDATES:
        if not os.path.exists(wb_settings):
            continue
        try:
            d = json.load(open(wb_settings, encoding="utf-8"))
            claw = d.get("claw", {})
            uid_key = claw.get("legacyOwnerUid")
            users = claw.get("users", {})
            u = users.get(uid_key) if uid_key else (next(iter(users.values())) if users else {})
            ch = u.get("channels", {}).get("weixinClawBot", {})
            if ch.get("botToken") and ch.get("enabled", False):
                bt = ch["botToken"]
                # WorkBuddy 新版把敏感凭据存为加密信封：{'$wbEncrypted':1,'envelope':'<密文>'}
                # 明文取不到，把 dict 当 token 发出去必然被服务端拒（errcode=-14 session timeout）。
                # 与其让它带着假凭据跑到服务端再失败，不如本地立刻说清楚。
                if isinstance(bt, dict):
                    raise SystemExit(
                        "微信 ClawBot 的 botToken 是 WorkBuddy 加密信封（$wbEncrypted），"
                        "脚本读不到明文，直发一定被服务端拒绝（errcode=-14 session timeout）。\n"
                        "这不是「会话失效」，在微信侧发消息激活无效。解决办法：\n"
                        "  1) 在 WorkBuddy App「设置 → 通道」重新绑定微信 ClawBot；或\n"
                        "  2) 提供明文凭据：环境变量 CLAWBOT_BOT_TOKEN / CLAWBOT_BASE_URL / "
                        "CLAWBOT_USER_ID，或 ~/.clawbot/config.json"
                    )
                ch = dict(ch)
                ch["source"] = "workbuddy-settings:" + os.path.basename(os.path.dirname(wb_settings))
                return ch
        except Exception as e:
            log(f"[load_cfg] 读取 {wb_settings} 失败: {e}")

    # 独立 config.json
    if os.path.exists(STANDALONE_CFG):
        try:
            c = json.load(open(STANDALONE_CFG, encoding="utf-8"))
            if c.get("botToken") and c.get("baseUrl") and c.get("userId"):
                c["source"] = "standalone-config"
                return c
        except Exception as e:
            log(f"[load_cfg] 读取 {STANDALONE_CFG} 失败: {e}")

    raise SystemExit(
        "未找到微信 ClawBot 凭据。请提供之一：\n"
        "  1) WorkBuddy 已绑定并启用 ClawBot（~/.workbuddy-ai/settings.json）；或\n"
        "  2) 环境变量 CLAWBOT_BOT_TOKEN / CLAWBOT_BASE_URL / CLAWBOT_USER_ID；或\n"
        "  3) 配置文件 ~/.clawbot/config.json"
    )


def load_cache():
    if os.path.exists(CACHE):
        try:
            return json.load(open(CACHE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(token=None, buf=None):
    c = load_cache()
    if token is not None:
        c["context_token"] = token
    if buf is not None:
        c["get_updates_buf"] = buf
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(c, open(CACHE, "w", encoding="utf-8"))
    return c


def api_req(base_url, path, bot_token, payload, timeout=HTTP_TIMEOUT):
    url = f"{base_url.rstrip('/')}{path}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "Authorization": f"Bearer {bot_token}",
            "X-WECHAT-UIN": gen_uin(),
        },
        method="POST",
    )
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        body = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {e.code}: {body[:300]}")
    except Exception as e:
        raise RuntimeError(f"{type(e).__name__}: {str(e)[:200]}")
    try:
        parsed = json.loads(body)
    except Exception:
        parsed = None
    # 业务层错误码：iLink 即便 HTTP 200 也会在 body 里返回 errcode（如 -14 session timeout）。
    # 不检查就会把失败误报成成功。
    if isinstance(parsed, dict):
        ec = parsed.get("errcode")
        if ec not in (None, 0):
            raise RuntimeError(
                f"API errcode={ec} errmsg={parsed.get('errmsg')}"
            )
    return parsed


def find_context_token(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "context_token" and v:
                return v
            r = find_context_token(v)
            if r:
                return r
    elif isinstance(obj, list):
        for it in obj:
            r = find_context_token(it)
            if r:
                return r
    return None


def find_buf(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "get_updates_buf" and v:
                return v
            r = find_buf(v)
            if r:
                return r
    elif isinstance(obj, list):
        for it in obj:
            r = find_buf(it)
            if r:
                return r
    return None


def refresh_token(cfg, wait=40):
    """可选：轮询 getupdates 取 context_token（多数情况不需要，空 token 即可发）。"""
    cache = load_cache()
    buf = cache.get("get_updates_buf", "")
    try:
        result = api_req(
            cfg["baseUrl"],
            "/ilink/bot/getupdates",
            cfg["botToken"],
            {"get_updates_buf": buf, "base_info": {"channel_version": CHANNEL_VERSION}},
            timeout=wait + 5,
        )
    except RuntimeError as e:
        log(f"[refresh] 请求失败: {e}")
        return None
    nb = find_buf(result)
    if nb:
        save_cache(buf=nb)
    token = find_context_token(result)
    if token:
        save_cache(token=token)
        log(f"[refresh] 取得 context_token: {token[:16]}...")
        return token
    log("[refresh] 未取到 context_token（msgs 为空）。")
    return None


def send_text(cfg, text, token, client_tag="wb-notify"):
    payload = {
        "msg": {
            "from_user_id": "",
            "to_user_id": cfg["userId"],
            "client_id": f"{client_tag}-{uuid.uuid4().hex[:16]}",
            "message_type": 2,
            "message_state": 2,
            "context_token": token,
            "item_list": [{"type": 1, "text_item": {"text": text}}],
        },
        "base_info": {"channel_version": CHANNEL_VERSION},
    }
    return api_req(cfg["baseUrl"], "/ilink/bot/sendmessage", cfg["botToken"], payload, timeout=20)


def chunk_text(text, size=MAX_CHUNK):
    if len(text) <= size:
        return [text]
    chunks = []
    lines = text.split("\n")
    cur = ""
    for ln in lines:
        if len(cur) + len(ln) + 1 > size:
            if cur:
                chunks.append(cur)
            while len(ln) > size:
                chunks.append(ln[:size])
                ln = ln[size:]
            cur = ln
        else:
            cur = (cur + "\n" + ln) if cur else ln
    if cur:
        chunks.append(cur)
    return chunks


def do_send(text, as_json=False):
    cfg = load_cfg()
    cache = load_cache()
    # 自有 ClawBot 用空 token 即可直发；缓存里有则带上（更稳）。
    token = cache.get("context_token") or ""
    last_err = None
    for attempt in range(2):
        try:
            chunks = chunk_text(text)
            for i, ch in enumerate(chunks):
                suffix = f"\n\n（{i+1}/{len(chunks)}）" if len(chunks) > 1 else ""
                send_text(cfg, ch + suffix, token)
                time.sleep(0.4)
            if as_json:
                print(json.dumps({"ok": True, "chunks": len(chunks)}))
            else:
                print(f"已发送 {len(chunks)} 条到微信 ClawBot（来源: {cfg.get('source')}）。")
            return 0
        except RuntimeError as e:
            last_err = e
            log(f"[send] 第{attempt+1}次失败: {e}")
            token = ""  # 回退空串重试
    if as_json:
        print(json.dumps({"ok": False, "error": str(last_err)}))
    else:
        print(f"发送失败：{last_err}")
    return 1


def do_status(as_json=False):
    try:
        cfg = load_cfg()
    except SystemExit as e:
        if as_json:
            print(json.dumps({"ok": False, "error": str(e)}))
        else:
            print(f"状态异常：{e}")
        return 1
    cache = load_cache()
    info = {
        "ok": True,
        "source": cfg.get("source"),
        "enabled": cfg.get("enabled"),
        "channelId": cfg.get("channelId"),
        "userId": cfg.get("userId"),
        "baseUrl": cfg.get("baseUrl"),
        "hasTokenCached": bool(cache.get("context_token")),
    }
    if as_json:
        print(json.dumps(info))
    else:
        print("=== 微信 ClawBot 推送状态 ===")
        print(f"  凭据来源 : {info['source']}")
        print(f"  通道启用 : {info['enabled']}")
        print(f"  channelId: {mask(info['channelId'])}")
        print(f"  userId   : {mask(info['userId'])}")
        print(f"  baseUrl  : {info['baseUrl']}")
        print(f"  已缓存令牌: {info['hasTokenCached']}")
    return 0


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    if not args or args[0] in ("status", "--status"):
        return do_status(as_json)
    if args[0] == "refresh":
        cfg = load_cfg()
        tok = refresh_token(cfg, wait=40)
        if as_json:
            print(json.dumps({"ok": bool(tok)}))
        else:
            print("刷新完成。" if tok else "刷新未取到令牌。")
        return 0 if tok else 1
    if args[0] == "send":
        if "--file" in args:
            idx = args.index("--file")
            path = args[idx + 1]
            text = open(path, "r", encoding="utf-8").read()
        else:
            rest = [a for a in args[1:] if a != "--json"]
            text = " ".join(rest)
        if not text.strip():
            print("错误：文本为空")
            return 2
        return do_send(text, as_json)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
